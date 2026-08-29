import os
import uuid
from datetime import datetime
import pandas as pd

os.makedirs("data/processed", exist_ok=True)

# 1. Sinh file embeddings_master.csv chuẩn 100% Schema Đề cương
emb_data = [{
    "embedding_id": str(uuid.uuid4()),
    "recording_id": str(uuid.uuid4()),
    "segment_start": 0.0,
    "segment_end": 15.0,
    "model": "MERT",
    "model_version": "MERT-v1-95M",
    "dimension": 768,
    "vector": ",".join(["0.0"] * 768),
    "created_at": datetime.now().isoformat()
}]
pd.DataFrame(emb_data).to_csv("data/processed/embeddings_master.csv", index=False)

# 2. Sinh file test_queries_master.csv chuẩn Schema Đề cương
test_data = [{
    "query_id": str(uuid.uuid4()),
    "recording_id": str(uuid.uuid4()),
    "composition_id": None,
    "transformation": "crop_15s",
    "snr": 15.0,
    "pitch_shift": 0.0,
    "tempo_factor": 1.0,
    "codec": "mp3",
    "bitrate": 320,
    "segment_start": 0.0,
    "duration": 15.0,
    "expected_match_type": "EXACT_MATCH"
}]
pd.DataFrame(test_data).to_csv("data/processed/test_queries_master.csv", index=False)

print("✅ Đã sinh xong 2 file CSV thiếu chuẩn Schema!")