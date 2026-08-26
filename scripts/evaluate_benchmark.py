import sys
import os

# Thêm thư mục gốc của project vào Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.services.cascade_service import process_music_query
from backend.services.retrieval_service import build_faiss_index

DATABASE_URL = "postgresql://postgres:postgrespassword@localhost:5432/music_rights_ai"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def run_benchmark():
    db = SessionLocal()
    
    # Dữ liệu giả lập
    dummy_embeddings = np.random.randn(10, 768).astype('float32')
    norms = np.linalg.norm(dummy_embeddings, axis=1, keepdims=True)
    dummy_embeddings /= norms
    faiss_index = build_faiss_index(dummy_embeddings)
    rec_id_map = [f"rec_id_{i}" for i in range(10)]
    
    test_audio = "test.mp3"
    
    # Đo Latency
    start_time = time.time()
    result = process_music_query(test_audio, db, faiss_index, rec_id_map, top_k=5)
    latency_ms = (time.time() - start_time) * 1000
    
    print("\n========= KẾT QUẢ BENCHMARK KĨ THUẬT =========")
    print(f"1. Stage kích hoạt : {result.get('pipeline_stage')}")
    print(f"2. Match Type      : {result.get('match_type')}")
    print(f"3. Latency (Độ trễ): {latency_ms:.2f} ms")
    print(f"4. Số Candidates   : {len(result.get('candidates', []))}")
    print("==============================================\n")
    
    db.close()

if __name__ == "__main__":
    run_benchmark()