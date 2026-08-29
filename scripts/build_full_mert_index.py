import os
import glob
import re
import uuid
from datetime import datetime
import faiss
import numpy as np
import pandas as pd
from backend.services.embedding_service import extract_mert_embedding

# Thay vì dùng đường dẫn /content/drive/MyDrive/...
DATASET_FOLDERS = [
    ("data/dataset_A_jamendo/processed_audio_24k", "Jamendo"),
    ("data/dataset_B_fma/processed_audio_24k", "FMA"),
    ("data/dataset_C_youtube/processed_audio_24k", "YouTube_Audio_Library"),
    ("data/dataset_E_public_domain/processed_audio_24k", "Public_Domain"),
    ("data/dataset_F_cover_song/processed_audio_24k", "Cover_Song")
]

# File đầu ra
OUTPUT_CSV_PATH = "data/processed/embeddings_master.csv"
OUTPUT_FAISS_INDEX_PATH = "data/processed/mert_faiss.index"

vectors_list = []
metadata_records = []

print("🚀 BẮT ĐẦU TRÍCH XUẤT MERT EMBEDDING TỪ TOÀN BỘ DATASET 24kHZ...\n")

total_processed = 0

for folder_path, dataset_name in DATASET_FOLDERS:
    if not os.path.exists(folder_path):
        print(f"⚠️ Bỏ qua thư mục không tồn tại: {folder_path}")
        continue

    # Lấy toàn bộ file .wav trong thư mục
    wav_files = glob.glob(os.path.join(folder_path, "*.wav"))
    print(f"📂 [{dataset_name}] Tìm thấy {len(wav_files)} file WAV 24kHz...")

    for idx, file_path in enumerate(wav_files):
        file_name = os.path.basename(file_path)
        
        # 1. Tách recording_id gốc từ tên file (Ví dụ: track123_seg0_10s.wav -> track123)
        recording_id = file_name.split("_seg")[0] if "_seg" in file_name else os.path.splitext(file_name)[0]

        # 2. Phân tích segment_start từ tên file (Ví dụ: ..._10s.wav -> 10.0)
        match_start = re.search(r'_(\d+)s\.wav$', file_name)
        if match_start:
            segment_start = float(match_start.group(1))
        else:
            segment_start = 0.0
            
        segment_end = segment_start + 15.0  # Mỗi segment dài 15s

        # 3. Trích xuất MERT Embedding (Vector 768-dim)
        vector = extract_mert_embedding(file_path, target_sr=24000, max_duration=15.0)

        if vector is not None and len(vector) == 768:
            vectors_list.append(vector)
            
            # Cấu trúc Bảng embeddings chuẩn theo Đề cương
            metadata_records.append({
                "embedding_id": str(uuid.uuid4()),
                "recording_id": recording_id,
                "segment_start": segment_start,
                "segment_end": segment_end,
                "model": "MERT",
                "model_version": "MERT-v1-95M",
                "dimension": 768,
                "vector": ",".join(map(str, vector)),  # Chuỗi vector lưu Postgres
                "created_at": datetime.now().isoformat()
            })
            total_processed += 1

        if (idx + 1) % 100 == 0:
            print(f"   -> Đã trích xuất {idx + 1}/{len(wav_files)} file của dataset {dataset_name}")

print(f"\n✅ Hoàn thành trích xuất tổng cộng {total_processed} vectors!")

# 4. Xuất dữ liệu ra file embeddings_master.csv khớp 100% Schema Đề cương
if metadata_records:
    os.makedirs(os.path.dirname(OUTPUT_CSV_PATH), exist_ok=True)
    df_emb = pd.DataFrame(metadata_records)
    
    # Sắp xếp đúng thứ tự các cột theo Schema Bảng embeddings
    df_emb = df_emb[[
        "embedding_id",
        "recording_id",
        "segment_start",
        "segment_end",
        "model",
        "model_version",
        "dimension",
        "vector",
        "created_at"
    ]]
    
    df_emb.to_csv(OUTPUT_CSV_PATH, index=False)
    print(f"💾 Đã lưu metadata vector chuẩn Schema vào: {OUTPUT_CSV_PATH}")

# 5. Dựng và lưu file FAISS Index THẬT
if vectors_list:
    matrix_np = np.array(vectors_list).astype('float32')
    
    # IndexFlatIP (Inner Product trên L2 Normalized Vectors = Cosine Similarity)
    dimension = 768
    index = faiss.IndexFlatIP(dimension)
    index.add(matrix_np)

    faiss.write_index(index, OUTPUT_FAISS_INDEX_PATH)
    print(f"🎉 Đã lưu file FAISS Index thật tại: {OUTPUT_FAISS_INDEX_PATH}")