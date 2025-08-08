import numpy as np
from sentence_transformers import SentenceTransformer
from .config import Config

_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(Config.EMBED_MODEL)
    return _model

def embed_identity(text: str):
    """
    Return float32 length-512 vector. If your model's dim != 512,
    add a small projection or switch schema VECTOR dim accordingly.
    """
    v = get_model().encode([text], normalize_embeddings=True)[0]  # np.float32
    v = np.asarray(v, dtype=np.float32)
    # If your model outputs 384/768, do a learned or fixed projection to 512.
    # Simple pad/truncate fallback (works but train a projection for best results).
    if v.shape[0] < 512:
        v = np.pad(v, (0, 512 - v.shape[0]))
    elif v.shape[0] > 512:
        v = v[:512]
    return v
