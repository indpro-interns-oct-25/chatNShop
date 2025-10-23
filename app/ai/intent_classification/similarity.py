# app/ai/intent_classification/similarity.py
from typing import Union
import numpy as np

def l2_normalize(vecs: np.ndarray) -> np.ndarray:
    denom = np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-12
    return vecs / denom

def cosine_sim_matrix(a: np.ndarray, b: np.ndarray, already_normalized: bool = True) -> np.ndarray:
    if not already_normalized:
        a = l2_normalize(a)
        b = l2_normalize(b)
    return a @ b.T
