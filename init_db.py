import os
import pandas as pd
from sqlalchemy import create_engine, text

# 1. Chuỗi kết nối PostgreSQL (User, Password, Host, Port, DB Name)
DATABASE_URL = "postgresql://postgres:postgrespassword@localhost:5432/music_rights_ai"
engine = create_engine(DATABASE_URL)

def init_database():
    print("=== BẮT ĐẦU TẠO BẢNG & NẠP DỮ LIỆU VÀO POSTGRESQL ===")
    
    # 2. Định nghĩa Schema cấu trúc các bảng bắt buộc theo Đề cương dự án
    create_tables_sql = """
    CREATE TABLE IF NOT EXISTS compositions (
        composition_id UUID PRIMARY KEY,
        title TEXT,
        composer TEXT,
        year INTEGER,
        public_domain_status VARCHAR(50),
        source TEXT,
        verified_at TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS recordings (
        recording_id UUID PRIMARY KEY,
        composition_id UUID REFERENCES compositions(composition_id),
        title TEXT,
        artist TEXT,
        album TEXT,
        release_year INTEGER,
        duration FLOAT,
        source_dataset TEXT,
        source_track_id TEXT,
        audio_path TEXT,
        metadata_verified BOOLEAN
    );

    CREATE TABLE IF NOT EXISTS rights (
        rights_id UUID PRIMARY KEY,
        recording_id UUID REFERENCES recordings(recording_id),
        composition_id UUID REFERENCES compositions(composition_id),
        license_type VARCHAR(100),
        copyright_status VARCHAR(50),
        attribution_required BOOLEAN,
        commercial_use_allowed BOOLEAN,
        modification_allowed BOOLEAN,
        monetization_allowed BOOLEAN,
        revenue_share_required BOOLEAN,
        territory VARCHAR(50),
        platform VARCHAR(50),
        valid_from DATE,
        valid_until DATE,
        source TEXT,
        source_url TEXT,
        verified_at TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS fingerprints (
        fingerprint_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        recording_id UUID REFERENCES recordings(recording_id),
        algorithm VARCHAR(50) DEFAULT 'chromaprint',
        fingerprint TEXT,
        duration FLOAT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    with engine.connect() as conn:
        conn.execute(text(create_tables_sql))
        conn.commit()
    print("-> Da khoi tao xong khung cac bang (Schema)!")

    # 3. Import các file CSV dữ liệu vào CSDL
    data_dir = "data/processed" # Đường dẫn chứa các file master CSV của bạn trên Codespace
    
    files_to_import = [
        ("compositions_master.csv", "compositions"),
        ("metadata_master.csv", "recordings"),
        ("rights_master.csv", "rights"),
        ("fingerprints_master.csv", "fingerprints")
    ]

    for csv_file, table_name in files_to_import:
        file_path = os.path.join(data_dir, csv_file)
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            # Nạp dữ liệu vào bảng tương ứng trong Postgres
            df.to_sql(table_name, engine, if_exists='append', index=False, method='multi')
            print(f"-> Nap thanh cong {len(df)} ban ghi vao bang '{table_name}' tu {csv_file}")
        else:
            print(f"-> Canh bao: Khong tim thay file {file_path}, bo qua napping bang '{table_name}'")

    print("\n=== HOÀN THÀNH QUÁ TRÌNH TẠO VÀ NẠP CSDL ===")

if __name__ == "__main__":
    init_database()