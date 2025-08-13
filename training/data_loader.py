"""Utility functions for loading training or ingestion datasets.

This module provides :func:`load_dataframe` which accepts a path to either a
CSV file, a Parquet file, or a directory containing a dataset saved from
Hugging Face's ``datasets`` library.  It returns a ``pandas.DataFrame`` so the
rest of the code can operate agnostically of the underlying storage format.
"""

from __future__ import annotations

import glob
import os
from typing import List

import pandas as pd
from datasets import load_from_disk


def _parquet_files(path: str) -> List[str]:
    """Return a sorted list of parquet files contained in ``path``."""

    return sorted(glob.glob(os.path.join(path, "*.parquet")))


def load_dataframe(path: str) -> pd.DataFrame:
    """Load a dataset from ``path`` into a :class:`pandas.DataFrame`.

    Parameters
    ----------
    path:
        Path to a CSV/Parquet file or a directory containing a Hugging Face
        dataset (as created by ``datasets.save_to_disk``) or a collection of
        Parquet files.

    Returns
    -------
    pandas.DataFrame
        Data loaded into a dataframe.
    """

    if os.path.isdir(path):
        # Common layout for datasets downloaded via ``datasets.load_dataset``
        # and saved with ``save_to_disk`` includes a ``data`` subdirectory
        # containing parquet shards.
        data_dir = path
        possible = os.path.join(path, "data")
        if os.path.isdir(possible):
            data_dir = possible

        parquet_files = _parquet_files(data_dir)
        if parquet_files:
            frames = [pd.read_parquet(p) for p in parquet_files]
            return pd.concat(frames, ignore_index=True)

        # If no parquet files were found, fall back to Hugging Face
        # ``load_from_disk`` which understands the dataset metadata structure.
        ds = load_from_disk(path)
        # Prefer the ``train`` split if present, otherwise combine all splits
        if isinstance(ds, dict):
            # ``load_from_disk`` returns a ``DatasetDict`` when multiple splits
            # are available.
            if "train" in ds:
                return ds["train"].to_pandas()
            frames = [split.to_pandas() for split in ds.values()]
            return pd.concat(frames, ignore_index=True)

        return ds.to_pandas()

    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        return pd.read_csv(path)
    if ext in (".parquet", ".pq"):
        return pd.read_parquet(path)

    raise ValueError(f"Unsupported data format for '{path}'")


__all__ = ["load_dataframe"]

