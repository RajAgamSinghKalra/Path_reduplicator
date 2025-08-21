import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from app.model_store import load_model, predict_proba


def test_rule_based_model_high_score(tmp_path):
    model = load_model(path=str(tmp_path / "missing.bin"))
    feats = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0]
    prob = predict_proba(model, [feats])[0]
    assert prob > 0.95


def test_rule_based_model_low_score(tmp_path):
    model = load_model(path=str(tmp_path / "missing2.bin"))
    feats = [0.0] * 9 + [9999.0]
    prob = predict_proba(model, [feats])[0]
    assert prob == 0.0
