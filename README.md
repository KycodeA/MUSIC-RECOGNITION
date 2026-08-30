# 🎵 MUSIC RECOGNITION & RIGHTS INSPECTION PLATFORM

> Hệ thống AI nhận diện âm nhạc đa tầng (Hybrid Cascade) kết hợp Audio Fingerprinting và Deep Retrieval 768-dim tra cứu bản quyền tự động.

---

## 📌 Tổng quan Kiến trúc

- **Tầng 1 (Exact Match):** Chromaprint Audio Fingerprinting (Bitwise Hamming Distance).
- **Tầng 2 (Deep Retrieval):** MERT-v1-95M Feature Extractor + FAISS Vector Search (Cosine Similarity).
- **Business Engine:** Tra cứu bản quyền & cấp phép (Public Domain, Creative Commons, Revenue Share).
- **RESTful API:** FastAPI + Uvicorn Server.

---

## 📂 Cấu trúc Dự án

```text
.
├── Dockerfile
├── README.md
├── backend
│   ├── main.py
│   └── services
│       ├── audio_service.py
│       ├── cascade_service.py
│       ├── decision_service.py
│       ├── embedding_service.py
│       ├── fingerprint_service.py
│       ├── retrieval_service.py
│       └── rights_service.py
├── data
│   └── processed
│       ├── compositions_master.csv
│       ├── embeddings_master.csv
│       ├── fingerprints_master.csv
│       ├── metadata_master.csv
│       ├── rights_master.csv
│       └── test_queries_master.csv
├── docker-compose.yml
├── init_db.py
├── requirements.txt
├── scripts
│   ├── add_test_track.py
│   ├── build_full_mert_index.py
│   ├── evaluate_benchmark.py
│   ├── generate_missing_csvs.py
│   ├── generate_test_queries.py
│   └── sync_data.py
├── test.mp3
├── test_audio
│   └── bai_hat_test.mp3
├── test_fingerprint.py
└── tests
    ├── test_api.py
    ├── test_cascade_service.py
    ├── test_fingerprint_service.py
    ├── test_mert_embedding.py
    ├── test_retrieval_service.py
    └── test_rights_service.py

8 directories, 34 files
```

---

## 🚀 Hướng dẫn Cài đặt & Khởi chạy

### 1. Khởi tạo môi trường
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Khởi chạy FastAPI Server
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
TRUY CẬP SWAGGER UI: `http://localhost:8000/docs`

### 3. Chạy Kiểm thử (Pytest)
```bash
python -m pytest tests/ -W ignore::DeprecationWarning
```

---
*Tự động cập nhật bởi GitHub Action Workflow.*
