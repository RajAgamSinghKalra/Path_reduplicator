import sys
import pathlib
import array

import pytest

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from app.db import to_vec_array
from app.config import Config


def test_to_vec_array_length_ok():
    vec = [0.0] * Config.VECTOR_DIM
    arr = to_vec_array(vec)
    assert isinstance(arr, array.array)
    assert len(arr) == Config.VECTOR_DIM


def test_to_vec_array_length_mismatch():
    vec = [0.0] * (Config.VECTOR_DIM - 1)
    with pytest.raises(ValueError):
        to_vec_array(vec)

