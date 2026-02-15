from risk_engine import RiskEngine


def test_basic_risk():
    engine = RiskEngine()

    features = {
        "velocity_z": 3.2,
        "dispersion_z": 2.5,
        "entropy_shift": 1.8,
        "drain_ratio": 0.6,
        "long_term_drift": 0.3,
        "micro_pattern_score": 0.7,
        "structural_risk": 0.9,
        "risk_density": 0.6,
        "maturity_penalty": 0.2,
        "behavioral_drift_score": 2.1,
        "suspicion": 12,
        "previous_risk": 45
    }

    result = engine.score(features)

    print(result)


if __name__ == "__main__":
    test_basic_risk()
