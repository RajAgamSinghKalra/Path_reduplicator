import pathlib

from training import train_ranker


def test_missing_training_data(tmp_path: pathlib.Path):
    """Ensure a helpful response when the training data file is absent."""

    missing = tmp_path / "does-not-exist.csv"
    result = train_ranker.main(str(missing))
    assert result["success"] is False
    assert "Training data not found" in result["message"]

