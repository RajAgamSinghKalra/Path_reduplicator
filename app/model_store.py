import os, pickle
from sklearn.linear_model import LogisticRegression
import numpy as np

DEFAULT = LogisticRegression(max_iter=1000, class_weight="balanced")

def load_model(path="model.bin"):
    if os.path.exists(path):
        with open(path, "rb") as f: return pickle.load(f)
    return DEFAULT

def save_model(model, path="model.bin"):
    with open(path, "wb") as f: pickle.dump(model, f)

def predict_proba(model, X):
    return model.predict_proba(np.asarray(X))[:,1]
