import requests
from simulator_core import SimulatorCore, make_accounts

accounts = make_accounts(200)
sim = SimulatorCore(accounts)

sim.start("attack")

while True:
    tx = sim.next_tx()

    requests.post(
        "http://127.0.0.1:8000/tx",
        json={
            "id": tx["id"],
            "ts": tx["ts"],
            "sender": tx["sender"],
            "receiver": tx["receiver"],
            "amount": tx["amount"]
        }
    )
