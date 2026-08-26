import pytest
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.services.retrieval_service import build_faiss_index
from backend.services.cascade_service import process_music_query

DATABASE_URL = "postgresql://postgres:postgrespassword@localhost:5432/music_rights_ai"

@pytest.fixture
def setup_env():
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    # Tạo dữ liệu giả lập cho FAISS Index
    dummy_embeddings = np.random.randn(5, 768).astype('float32')
    norms = np.linalg.norm(dummy_embeddings, axis=1, keepdims=True)
    dummy_embeddings /= norms
    
    index = build_faiss_index(dummy_embeddings)
    rec_id_map = [f"rec_id_{i}" for i in range(5)]
    
    yield db, index, rec_id_map
    db.close()

def test_full_cascade_pipeline(setup_env):
    db, index, rec_id_map = setup_env
    test_audio = "test.mp3"
    
    result = process_music_query(test_audio, db, index, rec_id_map, top_k=3)
    
    assert "pipeline_stage" in result
    assert result["pipeline_stage"] in ["STAGE_1_CHROMAPRINT", "STAGE_2_MERT_RETRIEVAL"]
    assert "candidates" in result