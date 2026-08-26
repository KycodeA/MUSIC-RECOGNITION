import faiss
import numpy as np

def build_faiss_index(embeddings_matrix: np.ndarray):
    """
    Khởi tạo chỉ mục FAISS dùng Cosine Similarity (IndexFlatIP trên L2 Normalized Vectors).
    Input: embeddings_matrix có dạng (N, 768)
    """
    if len(embeddings_matrix) == 0:
        return None
        
    dimension = embeddings_matrix.shape[1]
    # IndexFlatIP = Inner Product. Vì vector đã chuẩn hóa L2, Inner Product chính là Cosine Similarity.
    index = faiss.IndexFlatIP(dimension)  
    index.add(embeddings_matrix.astype('float32'))
    return index

def search_top_k(index, query_vector: np.ndarray, top_k: int = 5):
    """
    Tìm Top-K bài hát giống nhất trong chỉ mục FAISS.
    Trả về: scores (độ tương đồng Cosine), indices (chỉ số vị trí)
    """
    if query_vector is None or index is None:
        return [], []
        
    # Chuyển query_vector về dạng matrix 2D (1, 768)
    if len(query_vector.shape) == 1:
        query_vector = np.expand_dims(query_vector, axis=0)
        
    scores, indices = index.search(query_vector.astype('float32'), top_k)
    return scores[0].tolist(), indices[0].tolist()