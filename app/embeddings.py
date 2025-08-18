import numpy as np
from functools import lru_cache
from sentence_transformers import SentenceTransformer

from .config import Config

try:  # Prefer DirectML for GPU acceleration when available
    import torch_directml

    _DEVICE = torch_directml.device()
except Exception:  # pragma: no cover - fallback to CPU if DirectML unavailable
    _DEVICE = "cpu"


@lru_cache()
def get_model() -> SentenceTransformer:
    """Return a cached ``SentenceTransformer`` instance."""
    return SentenceTransformer(Config.EMBED_MODEL, device=_DEVICE)

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
