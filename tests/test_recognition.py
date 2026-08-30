import subprocess
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:postgrespassword@localhost:5432/music_rights_ai"
engine = create_engine(DATABASE_URL)

def get_chromaprint(audio_path):
    try:
        result = subprocess.run(["fpcalc", "-raw", audio_path], stdout=subprocess.PIPE, text=True, check=True)
        duration, fingerprint = 0.0, ""
        for line in result.stdout.splitlines():
            if line.startswith("DURATION="): 
                duration = float(line.split("=")[1])
            elif line.startswith("FINGERPRINT="): 
                fingerprint = line.split("=")[1]
        return fingerprint, duration
    except Exception as e:
        print(f"Lỗi fpcalc: {e}")
        return None, 0.0

def test_audio_recognition(test_audio_path):
    print(f"🔍 Đang trích xuất dữ liệu từ file test: {test_audio_path}")
    fp, duration = get_chromaprint(test_audio_path)
    
    if not fp:
        print("❌ Không thể trích xuất fingerprint từ file test!")
        return

    with engine.connect() as conn:
        # Bật extension fuzzystrmatch để dùng hàm LEVENSHTEIN nếu chưa kích hoạt
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;"))
            conn.commit()
        except Exception as ext_err:
            conn.rollback()

        # Query 1: So sánh độ tương đồng bằng thuật toán Levenshtein
        query = text("""
            SELECT 
                r.recording_id,
                r.title AS song_title,
                r.artist,
                c.title AS composition_title,
                rg.license_type,
                rg.copyright_status,
                f.fingerprint
            FROM fingerprints f
            JOIN recordings r ON f.recording_id = r.recording_id
            JOIN compositions c ON r.composition_id = c.composition_id
            LEFT JOIN rights rg ON r.recording_id = rg.recording_id
            ORDER BY LEVENSHTEIN(f.fingerprint, :query_fp) ASC
            LIMIT 1;
        """)
        
        try:
            result = conn.execute(query, {"query_fp": fp}).fetchone()
        except Exception as e:
            # QUAN TRỌNG: Rollback transaction bị hỏng trước khi thực thi truy vấn dự phòng
            conn.rollback()
            
            # Query 2: Fallback query kiểm tra trùng khớp tuyệt đối hoặc theo độ dài duration
            fallback_query = text("""
                SELECT 
                    r.recording_id, 
                    r.title AS song_title, 
                    r.artist, 
                    c.title AS composition_title, 
                    rg.license_type, 
                    rg.copyright_status
                FROM fingerprints f
                JOIN recordings r ON f.recording_id = r.recording_id
                JOIN compositions c ON r.composition_id = c.composition_id
                LEFT JOIN rights rg ON r.recording_id = rg.recording_id
                WHERE f.fingerprint = :query_fp 
                   OR f.duration BETWEEN (:dur - 2.0) AND (:dur + 2.0)
                LIMIT 1;
            """)
            result = conn.execute(fallback_query, {"query_fp": fp, "dur": duration}).fetchone()

        if result:
            print("\n🎉 === KẾT QUẢ NHẬN DIỆN THÀNH CÔNG ===")
            print(f"🎵 Tên bài hát: {result.song_title}")
            print(f"🎤 Ca sĩ/Artist: {result.artist}")
            print(f"🎼 Tác phẩm gốc: {result.composition_title}")
            print(f"📜 Loại bản quyền: {result.license_type}")
            print(f"🛡️ Trạng thái bản quyền: {result.copyright_status}")
            print(f"🆔 Recording ID: {result.recording_id}")
        else:
            print("\n❌ Không tìm thấy bài hát tương thích trong CSDL.")

if __name__ == "__main__":
    test_audio_recognition("test_audio/bai_hat_test.mp3")