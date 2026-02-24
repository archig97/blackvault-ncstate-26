from __future__ import annotations

from pathlib import Path

from .trainer import train_score_and_save


def main():
    model_path = Path(__file__).resolve().parents[1] / "models" / "risk_hybrid_model.joblib"
    artifact, scores = train_score_and_save(model_path)
    print("Model saved to:", model_path)
    print("Model:", artifact.get("model_name"), artifact.get("model_version"))
    print("Scores:")
    for k, v in scores.items():
        print(f"  {k}: {v:.6f}" if isinstance(v, float) else f"  {k}: {v}")


if __name__ == "__main__":
    main()
