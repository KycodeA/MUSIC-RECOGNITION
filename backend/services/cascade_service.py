from sqlalchemy.orm import Session
from backend.services.fingerprint_service import search_fingerprint
from backend.services.embedding_service import extract_mert_embedding
from backend.services.retrieval_service import search_top_k

def process_music_query(audio_path: str, db: Session, faiss_index, rec_id_map: list, top_k: int = 5):
    """
    Phễu Cascade xử lý truy vấn âm thanh:
    Tầng 1: Chromaprint Exact Match
    Tầng 2: MERT Deep Retrieval (nếu Tầng 1 thất bại)
    """
    # -------------------------------------------------------------
    # TẦNG 1: CHROMAPRINT EXACT MATCH
    # -------------------------------------------------------------
    fp_result = search_fingerprint(db, audio_path)
    
    if fp_result.get("match_type") == "EXACT_MATCH":
        return {
            "pipeline_stage": "STAGE_1_CHROMAPRINT",
            "match_type": "EXACT_MATCH",
            "recording_id": fp_result["recording_id"],
            "score": fp_result["fingerprint_score"],
            "candidates": []
        }

    # -------------------------------------------------------------
    # TẦNG 2: MERT DEEP RETRIEVAL (Kích hoạt khi Chromaprint = NO_MATCH)
    # -------------------------------------------------------------
    query_vector = extract_mert_embedding(audio_path, max_duration=30.0)
    
    if query_vector is None:
        return {
            "pipeline_stage": "FAILED",
            "match_type": "ERROR",
            "message": "Không thể xử lý file audio."
        }

    scores, indices = search_top_k(faiss_index, query_vector, top_k=top_k)
    
    candidates = []
    for score, idx in zip(scores, indices):
        if idx < len(rec_id_map):
            candidates.append({
                "recording_id": rec_id_map[idx],
                "similarity_score": float(score)
            })

    return {
        "pipeline_stage": "STAGE_2_MERT_RETRIEVAL",
        "match_type": "NEAR_MATCH",
        "recording_id": candidates[0]["recording_id"] if candidates else None,
        "score": candidates[0]["similarity_score"] if candidates else 0.0,
        "candidates": candidates
    }