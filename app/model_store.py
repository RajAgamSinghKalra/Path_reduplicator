import os, pickle
import numpy as np
from sklearn.dummy import DummyClassifier

#
# When a trained ``model.bin`` is absent we fall back to a trivial model so
# that the service can still operate (albeit always predicting "not a
# duplicate").  ``DummyClassifier`` is fitted on a single example so that
# ``predict_proba`` is available without raising ``NotFittedError``.
#
_DEFAULT = DummyClassifier(strategy="constant", constant=0)
_DEFAULT.fit(np.zeros((1, 10)), [0])  # feature_row outputs 10 features

# Cache loaded models keyed by path to avoid repeated disk I/O
_CACHE: dict[str, object] = {}

def load_model(path="model.bin"):
    if path in _CACHE:
        return _CACHE[path]
    if os.path.exists(path):
        with open(path, "rb") as f:
            _CACHE[path] = pickle.load(f)
    else:
        _CACHE[path] = _DEFAULT
    return _CACHE[path]

def save_model(model, path="model.bin"):
    with open(path, "wb") as f: pickle.dump(model, f)

def predict_proba(model, X):
    """Predict probability of the positive class.

    Some fallback models (e.g. the ``DummyClassifier`` used when no trained
    model is available) may only know about a single class.  In that case
    scikit-learn returns a single probability column.  We treat this as a
    zero probability for the positive class.
    """
    probs = model.predict_proba(np.asarray(X))
    if probs.shape[1] == 1:
        return np.zeros(probs.shape[0])
    return probs[:, 1]
