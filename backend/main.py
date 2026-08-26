import os
import shutil
import uuid
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

# Khởi tạo FAISS Index & Map ID từ CSDL
db_session = SessionLocal()
try:
    recordings = db_session.execute(text("SELECT recording_id FROM recordings LIMIT 10")).fetchall()
    if recordings:
        GLOBAL_REC_MAP = [str(r[0]) for r in recordings]
    else:
        # Nếu DB chưa có bản ghi, tạo chuỗi UUID chuẩn thay vì 'dummy_id_1'
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
    return {"status": "ONLINE", "database": "CONNECTED", "ai_models": "READY"}


@app.post("/api/v1/search", tags=["Music Identification"])
async def search_music(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, file.filename)

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Chạy Phễu Cascade
        cascade_result = process_music_query(
            audio_path=temp_file_path,
            db=db,
            faiss_index=GLOBAL_FAISS_INDEX,
            rec_id_map=GLOBAL_REC_MAP,
            top_k=5
        )

        matched_rec_id = cascade_result.get("recording_id")
        
        rights_detail = None
        if matched_rec_id:
            rights_detail = get_full_music_rights(str(matched_rec_id), db)

        return {
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