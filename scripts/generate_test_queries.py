import os
import uuid
import pandas as pd
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:postgrespassword@localhost:5432/music_rights_ai"
engine = create_engine(DATABASE_URL)

OUTPUT_CSV = "data/processed/test_queries_master.csv"

def generate_test_queries_csv():
    # Lấy thử một số recording_id có thật trong DB làm bài hát gốc
    with engine.connect() as conn:
        result = conn.execute(text("SELECT recording_id, composition_id FROM recordings LIMIT 20")).fetchall()
        
    if not result:
        print("⚠️ Chưa có dữ liệu trong bảng recordings. Hãy chạy init_db.py trước!")
        return

    test_queries = []
    
    # Sinh các biến đổi (Transformations) cho từng bài hát theo Đề cương
    transformations = [
        {"type": "clean_exact", "snr": None, "pitch": 0.0, "tempo": 1.0, "codec": "wav", "bitrate": 1411},
        {"type": "crop_15s", "snr": None, "pitch": 0.0, "tempo": 1.0, "codec": "wav", "bitrate": 1411},
        {"type": "mp3_compression_128k", "snr": None, "pitch": 0.0, "tempo": 1.0, "codec": "mp3", "bitrate": 128},
        {"type": "pitch_shift_plus_1", "snr": None, "pitch": 1.0, "tempo": 1.0, "codec": "mp3", "bitrate": 320},
        {"type": "tempo_change_0_95", "snr": None, "pitch": 0.0, "tempo": 0.95, "codec": "mp3", "bitrate": 320},
        {"type": "background_noise_snr10", "snr": 10.0, "pitch": 0.0, "tempo": 1.0, "codec": "wav", "bitrate": 1411},
    ]

    for row in result:
        rec_id = str(row[0])
        comp_id = str(row[1]) if row[1] else None
        
        for trans in transformations:
            test_queries.append({
                "query_id": str(uuid.uuid4()),
                "recording_id": rec_id,
                "composition_id": comp_id,
                "transformation": trans["type"],
                "snr": trans["snr"],
                "pitch_shift": trans["pitch"],
                "tempo_factor": trans["tempo"],
                "codec": trans["codec"],
                "bitrate": trans["bitrate"],
                "segment_start": 0.0,
                "duration": 15.0,
                "expected_match_type": "EXACT_MATCH" if trans["type"] == "clean_exact" else "NEAR_MATCH"
            })

    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    df = pd.DataFrame(test_queries)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"✅ Đã tạo thành công {len(df)} kịch bản test tại: {OUTPUT_CSV}")

if __name__ == "__main__":
    generate_test_queries_csv()