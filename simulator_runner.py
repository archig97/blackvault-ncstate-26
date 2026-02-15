import time
import requests
from simulator_core import SimulatorCore, make_accounts

accounts = make_accounts(200)
sim = SimulatorCore(accounts)

# Mixed traffic profile:
# - mostly normal traffic (many accounts)
# - short periodic attack bursts (acct_attack)
sim.start("normal")
t0 = time.time()

while True:
    elapsed = time.time() - t0
    cycle_s = int(elapsed) % 30
    sim.set_mode("attack" if 20 <= cycle_s < 30 else "normal")

    tx = sim.next_tx()

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
            timeout=3,
        )
        if resp.status_code >= 400:
            print(f"POST /tx failed: {resp.status_code} {resp.text}")
    except Exception as exc:
        print(f"POST /tx error: {exc}")

    time.sleep(sim._sleep_interval())
