import acoustid
import uuid
import os
from sqlalchemy.orm import Session
from sqlalchemy import text

# Ngưỡng quyết định (Threshold) cho Chromaprint (Có thể tinh chỉnh sau EXP-01)
FP_THRESHOLD = 0.85

def extract_query_fingerprint(audio_path: str):
    """Trích xuất Fingerprint từ file audio truy vấn."""
    try:
        duration, fp = acoustid.fingerprint_file(audio_path)
        # Chuyển kiểu bytes sang chuỗi string nếu cần
        fp_str = fp.decode('utf-8') if isinstance(fp, bytes) else str(fp)
        return duration, fp_str
    except Exception as e:
        print(f"Lỗi trích xuất fingerprint: {e}")
        return None, None

def calculate_similarity(fp_query: str, fp_db: str):
    """Tính độ tương đồng giữa hai fingerprint."""
    try:
        score = acoustid.compare_fingerprints(fp_query, fp_db)
        return score
    except Exception:
        return 0.0

def search_fingerprint(db: Session, audio_path: str):
    """
    1. Trích xuất FP từ file.
    2. So khớp với database.
    3. Trả về EXACT_MATCH nếu điểm >= Threshold.
    """
    duration, query_fp = extract_query_fingerprint(audio_path)
    
    if not query_fp:
        return {"status": "ERROR", "message": "Không thể phân tích audio."}

    # Lấy toàn bộ fingerprint từ database 
    # (Trong dự án thực tế lớn hơn, sẽ dùng các thuật toán indexing chuyên dụng, 
    # nhưng với <10.000 bản ghi, lấy ra memory để so sánh vẫn rất nhanh)
    db_fingerprints = db.execute(text("SELECT recording_id, fingerprint FROM fingerprints")).fetchall()

    best_match_id = None
    best_score = 0.0

    # Duyệt qua toàn bộ DB để tìm best match
    for row in db_fingerprints:
        rec_id = str(row[0])
        db_fp = str(row[1])
        
        score = calculate_similarity(query_fp, db_fp)
        if score > best_score:
            best_score = score
            best_match_id = rec_id

    # Đưa ra quyết định theo Ngưỡng
    if best_score >= FP_THRESHOLD:
        return {
            "match_type": "EXACT_MATCH",
            "recording_id": best_match_id,
            "fingerprint_score": best_score
        }
    else:
        return {
            "match_type": "NO_MATCH",
            "recording_id": None,
            "fingerprint_score": best_score,
            "message": "Không tìm thấy kết quả chính xác, cần kích hoạt MERT Retrieval."
        }
    