import numpy as np
from backend.services.retrieval_service import build_faiss_index, search_top_k

def test_faiss_search():
    # Tạo giả lập 10 vector embedding (kích thước 10 x 768)
    dummy_db = np.random.randn(10, 768).astype('float32')
    # Chuẩn hóa L2 cho các vector giả lập
    norms = np.linalg.norm(dummy_db, axis=1, keepdims=True)
    dummy_db = dummy_db / norms

    # Khởi tạo FAISS Index
    index = build_faiss_index(dummy_db)
    assert index is not None
    assert index.ntotal == 10

    # Lấy vector thứ 0 làm query vector
    query_vec = dummy_db[0]
    scores, indices = search_top_k(index, query_vec, top_k=3)

    # Kết quả gần nhất (top-1) phải chính là chỉ số 0 với score gần 1.0
    assert indices[0] == 0
    assert abs(scores[0] - 1.0) < 1e-4