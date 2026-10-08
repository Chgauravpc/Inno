"""Deterministic simulated index paths for demo charts (seeded, calibrated to long-run assumptions)."""
from __future__ import annotations

import math
import random
from typing import Dict, List

from .assets import ASSETS, TWIN_CLASSES, corr


def cholesky(m: List[List[float]]) -> List[List[float]]:
    n = len(m)
    L = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1):
            s = sum(L[i][k] * L[j][k] for k in range(j))
            L[i][j] = math.sqrt(max(m[i][i] - s, 1e-12)) if i == j else (m[i][j] - s) / L[j][j]
    return L


def corr_matrix(keys: List[str]) -> List[List[float]]:
    return [[corr(a, b) for b in keys] for a in keys]


def correlated_normals(rng: random.Random, L: List[List[float]]) -> List[float]:
    z = [rng.gauss(0, 1) for _ in L]
    return [sum(L[i][k] * z[k] for k in range(i + 1)) for i in range(len(L))]


def class_paths(months: int = 60, seed: int = 11) -> Dict[str, List[float]]:
    """Monthly price-index paths (base 100) with exact long-run price drift."""
    rng = random.Random(seed)
    L = cholesky(corr_matrix(TWIN_CLASSES))
    draws = [correlated_normals(rng, L) for _ in range(months)]
    out: Dict[str, List[float]] = {}
    for i, k in enumerate(TWIN_CLASSES):
        a = ASSETS[k]
        zs = [d[i] for d in draws]
        mean = sum(zs) / months
        sd = math.sqrt(sum((z - mean) ** 2 for z in zs) / months) or 1.0
        mu_m = math.log(1 + a["price_g"]) / 12
        sig_m = a["vol"] / math.sqrt(12)
        v, path = 100.0, [100.0]
        for z in zs:
            v *= math.exp(mu_m + sig_m * (z - mean) / sd)
            path.append(v)
        out[k] = path
    return out
