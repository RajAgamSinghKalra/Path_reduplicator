import sys, pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from app.model_store import load_model, predict_proba


def test_default_model_predicts_zero(tmp_path):
    """When no saved model exists, predictions should return 0.0."""
    model_path = tmp_path / "model.bin"
    model = load_model(str(model_path))
    proba = predict_proba(model, [[0] * 10])[0]
    assert proba == 0.0

