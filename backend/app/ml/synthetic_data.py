from __future__ import annotations

import numpy as np


def make_synthetic_dataset(n: int = 9000, seed: int = 42):
    rng = np.random.default_rng(seed)

    velocity = np.clip(rng.gamma(2.0, 0.9, n), 0, 5)
    dispersion = np.clip(rng.gamma(1.8, 0.8, n), 0, 5)
    entropy = np.clip(rng.normal(0.4, 0.6, n), 0, 5)
    drain = np.clip(rng.beta(2, 6, n), 0, 1)
    long_drift = np.clip(rng.beta(2, 8, n), 0, 1)
    micro = np.clip(rng.beta(1.8, 8, n), 0, 1)
    structural = np.clip(rng.beta(2, 5, n), 0, 1)
    density = np.clip(rng.beta(2, 6, n), 0, 1)
    maturity = np.clip(rng.beta(2, 7, n), 0, 1)
    behavioral_drift = np.clip(rng.gamma(1.6, 0.8, n), 0, 5)
    suspicion = np.clip(rng.gamma(1.5, 2.2, n), 0, 20)
    hops_score = np.clip(rng.beta(2, 4, n), 0, 1)

    x = np.column_stack(
        [
            velocity,
            dispersion,
            entropy,
            drain,
            long_drift,
            micro,
            structural,
            density,
            maturity,
            behavioral_drift,
            suspicion,
            hops_score,
        ]
    )

    # Weak-label synthesis approximates fraud pressure from multi-signal alignment.
    fraud_pressure = (
        0.15 * velocity
        + 0.12 * dispersion
        + 0.05 * entropy
        + 0.18 * drain
        + 0.10 * long_drift
        + 0.08 * micro
        + 0.20 * structural
        + 0.12 * density
        + 0.10 * behavioral_drift
        + 0.04 * suspicion
        + 0.18 * hops_score
        + rng.normal(0.0, 0.08, n)
    )
    y = (fraud_pressure > 0.95).astype(int)

    return x, y
