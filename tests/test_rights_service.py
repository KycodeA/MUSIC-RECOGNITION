import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.services.rights_service import get_full_music_rights

DATABASE_URL = "postgresql://postgres:postgrespassword@localhost:5432/music_rights_ai"

@pytest.fixture
def db_session():
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    yield db
    db.close()

def test_get_full_music_rights(db_session):
    # Lấy thử 1 recording_id có thật trong CSDL
    from sqlalchemy import text
    row = db_session.execute(text("SELECT recording_id FROM recordings LIMIT 1")).fetchone()
    
    if row:
        rec_id = str(row[0])
        result = get_full_music_rights(rec_id, db_session)
        
        assert result["status"] == "SUCCESS"
        assert "track_metadata" in result
        assert "rights_and_licensing" in result
        assert "usage_recommendation" in result