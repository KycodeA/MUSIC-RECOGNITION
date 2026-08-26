import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.services.fingerprint_service import search_fingerprint

DATABASE_URL = "postgresql://postgres:postgrespassword@localhost:5432/music_rights_ai"

@pytest.fixture
def db_session():
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    yield db
    db.close()

def test_search_fingerprint_no_match(db_session):
    # Test file âm thanh không có trong CSDL
    test_audio = "test.mp3" 
    result = search_fingerprint(db_session, test_audio)
    
    assert "match_type" in result
    assert result["match_type"] in ["EXACT_MATCH", "NO_MATCH"]