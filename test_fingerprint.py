from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.services.fingerprint_service import search_fingerprint

# Kết nối đến DB PostgreSQL trong Docker
DATABASE_URL = "postgresql://postgres:postgrespassword@localhost:5432/music_rights_ai"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Dùng file MP3 thật vừa tải về
test_audio = "test.mp3" 

print(f"Đang phân tích: {test_audio}")
result = search_fingerprint(db, test_audio)
print("Kết quả:", result)

db.close()