import time
import requests
from simulator_core import create_attack_scenario, generate_attack_tx

# Create 191-account ecosystem with realistic attack
scenario = create_attack_scenario(
    normal_count=150,
    merchant_count=30,
    fraudster_count=3,
    laundering_hub_count=5,
    sanctioned_count=3
)

t0 = time.time()

while True:
    elapsed = time.time() - t0
    
    # Generate next transaction from 4-phase attack
    tx = generate_attack_tx(scenario)

    try:
        resp = requests.post(
            "http://127.0.0.1:8000/tx",
            json={
                "id": tx["id"],
                "ts": tx["ts"],
                "sender": tx["sender"],
                "receiver": tx["receiver"],
                "amount": tx["amount"],
            },
            timeout=10,
        )
        if resp.status_code >= 400:
            print(f"POST /tx failed: {resp.status_code} {resp.text}")
    except Exception as exc:
        print(f"POST /tx error: {exc}")

    time.sleep(0.5)  # 500ms between transactions (was 100ms)
