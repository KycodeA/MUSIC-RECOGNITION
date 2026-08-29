import os
import time
import shutil
import uuid
import faiss
import pandas as pd
import numpy as np
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from backend.services.cascade_service import process_music_query
from backend.services.rights_service import get_full_music_rights
from backend.services.retrieval_service import build_faiss_index

DATABASE_URL = "postgresql://postgres:postgrespassword@localhost:5432/music_rights_ai"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(
    title="Music Rights AI Platform API",
    description="Hệ thống AI nhận diện âm nhạc và truy vấn bản quyền đa tầng",
    version="1.0.0"
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --------------------------------------------------------------------------
# KHỞI TẠO NẠP CHỈ MỤC FAISS THẬT VÀ MAP RECORDING ID
# --------------------------------------------------------------------------
FAISS_INDEX_PATH = "data/processed/mert_faiss.index"
EMBEDDINGS_CSV_PATH = "data/processed/embeddings_master.csv"

GLOBAL_FAISS_INDEX = None
GLOBAL_REC_MAP = []

if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(EMBEDDINGS_CSV_PATH):
    print(f"🚀 Loading FAISS Index từ: {FAISS_INDEX_PATH}")
    GLOBAL_FAISS_INDEX = faiss.read_index(FAISS_INDEX_PATH)
    
    print(f"📖 Loading Map ID từ: {EMBEDDINGS_CSV_PATH}")
    df_emb = pd.read_csv(EMBEDDINGS_CSV_PATH)
    GLOBAL_REC_MAP = df_emb["recording_id"].astype(str).tolist()
    print(f"✅ Đã nạp thành công {len(GLOBAL_REC_MAP)} vectors vào không gian FAISS!")
else:
    print("⚠️ CẢNH BÁO: Không tìm thấy file FAISS index thật hoặc CSV metadata. Đang sử dụng Fallback Dummy mode!")
    db_session = SessionLocal()
    try:
        recordings = db_session.execute(text("SELECT recording_id FROM recordings LIMIT 10")).fetchall()
        if recordings:
            GLOBAL_REC_MAP = [str(r[0]) for r in recordings]
        else:
            GLOBAL_REC_MAP = [str(uuid.uuid4()) for _ in range(5)]
        
        num_items = len(GLOBAL_REC_MAP)
        dummy_embeddings = np.random.randn(num_items, 768).astype('float32')
        norms = np.linalg.norm(dummy_embeddings, axis=1, keepdims=True)
        dummy_embeddings = np.divide(dummy_embeddings, norms, out=np.zeros_like(dummy_embeddings), where=norms!=0)
        GLOBAL_FAISS_INDEX = build_faiss_index(dummy_embeddings)
    finally:
        db_session.close()


@app.get("/health", tags=["Health Check"])
def health_check():
    return {
        "status": "ONLINE", 
        "database": "CONNECTED", 
        "ai_models": "READY",
        "faiss_total_vectors": GLOBAL_FAISS_INDEX.ntotal if GLOBAL_FAISS_INDEX else 0
    }


@app.post("/api/v1/search", tags=["Music Identification"])
async def search_music(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    start_time = time.time()
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, file.filename)

    try:
        # 1. Lưu file âm thanh tạm thời
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 2. Chạy Phễu Cascade (Fingerprint -> MERT Retrieval)
        cascade_result = process_music_query(
            audio_path=temp_file_path,
            db=db,
            faiss_index=GLOBAL_FAISS_INDEX,
            rec_id_map=GLOBAL_REC_MAP,
            top_k=5
        )

        matched_rec_id = cascade_result.get("recording_id")
        
        # 3. Tra cứu thông tin bản quyền & Đánh giá rủi ro
        rights_detail = None
        matched_comp_id = None
        
        if matched_rec_id:
            rights_detail = get_full_music_rights(str(matched_rec_id), db)
            # Tách composition_id nếu có
            if rights_detail and rights_detail.get("status") == "SUCCESS":
                matched_comp_id = rights_detail.get("track_metadata", {}).get("composition", {}).get("composition_id")

        # 4. Tính toán độ trễ thời gian xử lý (latency_ms)
        latency_ms = (time.time() - start_time) * 1000

        # 5. Tự động ghi nhật ký vào bảng analysis_results theo chuẩn Đề cương
        job_id = str(uuid.uuid4())
        try:
            fp_score = cascade_result.get("score") if cascade_result.get("pipeline_stage") == "STAGE_1_CHROMAPRINT" else None
            emb_score = cascade_result.get("score") if cascade_result.get("pipeline_stage") == "STAGE_2_MERT_RETRIEVAL" else None
            risk_lvl = rights_detail.get("risk_level", "UNKNOWN") if rights_detail else "UNKNOWN"
            reason_msg = rights_detail.get("usage_recommendation", "") if rights_detail else "No rights found"

            db.execute(text("""
                INSERT INTO analysis_results (
                    job_id, recording_candidate, composition_candidate,
                    fingerprint_score, embedding_score, cover_score, match_type, 
                    risk_level, confidence, decision_reason, latency_ms, model_version
                ) VALUES (
                    :job_id, :rec_id, :comp_id,
                    :fp_score, :emb_score, 0.0, :match_type, 
                    :risk_level, :confidence, :reason, :latency, :model_ver
                )
            """), {
                "job_id": job_id,
                "rec_id": matched_rec_id,
                "comp_id": matched_comp_id,
                "fp_score": fp_score,
                "emb_score": emb_score,
                "match_type": cascade_result.get("match_type", "NO_MATCH"),
                "risk_level": risk_lvl,
                "confidence": cascade_result.get("score", 0.0),
                "reason": reason_msg,
                "latency": latency_ms,
                "model_ver": "MERT-v1-95M"
            })
            db.commit()
        except Exception as log_err:
            print(f"⚠️ Lỗi ghi log analysis_results: {log_err}")

        # 6. Trả về Response đầy đủ cho Client
        return {
            "job_id": job_id,
            "latency_ms": round(latency_ms, 2),
            "search_result": cascade_result,
            "rights_inspection": rights_detail
        }

    except Exception as e:
        print(f"Lỗi API Search Internal Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Lỗi khi xử lý file audio: {str(e)}"
        )
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@app.get("/api/v1/rights/{recording_id}", tags=["Copyright & Licensing"])
def get_rights_by_id(recording_id: str, db: Session = Depends(get_db)):
    result = get_full_music_rights(str(recording_id), db)
    if result.get("status") == "NOT_FOUND":
        raise HTTPException(status_code=404, detail=result["message"])
    return result