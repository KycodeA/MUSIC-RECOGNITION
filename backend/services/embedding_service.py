import torch
import librosa
import gc
from transformers import Wav2Vec2FeatureExtractor, AutoModel

MODEL_NAME = "m-a-p/MERT-v1-95M"

# Load processor & model MERT
processor = Wav2Vec2FeatureExtractor.from_pretrained(MODEL_NAME, trust_remote_code=True)
model = AutoModel.from_pretrained(MODEL_NAME, trust_remote_code=True)
model.eval()

def extract_mert_embedding(audio_path: str, target_sr: int = 24000, max_duration: float = 30.0):
    """Trích xuất Vector Embedding 768-dim tối ưu RAM tuyệt đối cho Codespace."""
    try:
        # 1. Chỉ nạp 15 giây đầu tiên
        audio_array, _ = librosa.load(audio_path, sr=target_sr, mono=True, duration=max_duration)

        # 2. Đưa vào Processor
        inputs = processor(audio_array, sampling_rate=target_sr, return_tensors="pt")
        
        # 3. Dùng inference_mode để triệt tiêu toàn bộ việc lưu trữ gradient/intermediate state
        with torch.inference_mode():
            outputs = model(**inputs)
            embeddings = outputs.last_hidden_state
            
            # Mean Pooling over time (P1 Strategy)
            track_embedding = torch.mean(embeddings, dim=1)
            
            # Chuẩn hóa L2 vector
            norm_embedding = torch.nn.functional.normalize(track_embedding, p=2, dim=1)
            
            result_vector = norm_embedding.squeeze().numpy()

        # 4. Giải phóng bộ nhớ đệm rác lập tức
        del inputs, outputs, embeddings, track_embedding, norm_embedding, audio_array
        gc.collect()

        return result_vector
    except Exception as e:
        print(f"Lỗi extract MERT embedding: {e}")
        return None