import os
import subprocess

def extract_and_normalize_audio(input_file_path: str, output_dir: str = "temp_uploads") -> str:
    """
    Tách âm thanh từ file gốc (Video/MP3), chuẩn hóa tần số lấy mẫu 24kHz.
    Yêu cầu server đã cài đặt FFmpeg.
    """
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.basename(input_file_path)
    file_name_without_ext = os.path.splitext(base_name)[0]
    
    # File đầu ra luôn là WAV, 1 channel, 24kHz (Chuẩn bị cho MERT)
    output_wav_path = os.path.join(output_dir, f"{file_name_without_ext}_normalized.wav")
    
    # Lệnh FFmpeg: -vn (bỏ video), -ar 24000 (sample rate), -ac 1 (mono)
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-i", input_file_path,
        "-vn", "-ar", "24000", "-ac", "1", output_wav_path
    ]
    
    try:
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output_wav_path
    except subprocess.CalledProcessError as e:
        print(f"Lỗi khi xử lý FFmpeg: {e}")
        # Nếu FFmpeg lỗi hoặc không có, trả về file gốc để fallback
        return input_file_path