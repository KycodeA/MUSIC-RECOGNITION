import os
import pytest
import numpy as np
from backend.services.embedding_service import extract_mert_embedding

def test_extract_mert_embedding():
    test_audio = "test.mp3"
    assert os.path.exists(test_audio), "File test.mp3 không tồn tại!"
    
    vector = extract_mert_embedding(test_audio)
    
    # Kiểm tra vector đầu ra
    assert vector is not None
    assert isinstance(vector, np.ndarray)
    assert vector.shape[0] == 768  # Kích thước embedding của MERT-v1-95M
    
    # Kiểm tra chuẩn hóa L2 (Độ dài vector xấp xỉ 1.0)
    norm = np.linalg.norm(vector)
    assert pytest.approx(norm, 0.01) == 1.0