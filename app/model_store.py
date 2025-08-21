import os
import pickle
import numpy as np


class RuleBasedClassifier:
    """Light-weight classifier used when no trained model is available.

    The classifier implements a small set of heuristic rules that look at the
    feature vector produced by :func:`app.features.feature_row` and assigns a
    probability for the *duplicate* class.  It does not require any training
    and therefore provides consistent behaviour out of the box.

    The feature order is expected to be::

        [vdist_sim, name_sim, phone_match, email_match, govid_match,
         addr_overlap, city_sim, state_sim, pincode_match, dob_delta]

    The heuristics favour hard identifiers such as government ID, phone number
    and email.  Softer signals like name or address contribute small amounts to
    the final score.  The result is a number in the ``0..1`` range similar to a
    probability.
    """

    def fit(self, X=None, y=None):  # scikit-learn compatibility
        return self

    def predict_proba(self, X):
        X = np.asarray(X)
        probs = np.zeros((X.shape[0], 2), dtype=float)
        for i, row in enumerate(X):
            (
                vsim,
                name_sim,
                phone_match,
                email_match,
                govid_match,
                addr_overlap,
                city_sim,
                state_sim,
                pincode_match,
                dob_delta,
            ) = row

            # Strong identifiers dominate the score
            if govid_match >= 1.0:
                score = 0.99
            else:
                score = 0.0
                score += 0.4 * phone_match
                score += 0.4 * email_match
                score += 0.1 * vsim
                score += 0.1 * name_sim
                score += 0.05 * addr_overlap
                score += 0.05 * city_sim
                score += 0.03 * state_sim
                score += 0.05 * pincode_match
                if (phone_match or email_match or name_sim > 0.0) and dob_delta < 365:
                    if dob_delta < 30:
                        score += 0.1
                    else:
                        score += 0.05
                score = min(score, 0.99)

            probs[i, 0] = 1.0 - score
            probs[i, 1] = score
        return probs

#
# When a trained ``model.bin`` is absent we fall back to the
# :class:`RuleBasedClassifier` defined above.  It requires no training but we
# still call ``fit`` to mirror the behaviour of scikit-learn estimators and to
# document that the feature vector has 10 entries.
#
_DEFAULT = RuleBasedClassifier()
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
    with open(path, "wb") as f:
        pickle.dump(model, f)

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
