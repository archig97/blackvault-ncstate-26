#!/usr/bin/env python3
"""
Step 1: Standalone transaction simulator core (no FastAPI, no Valkey).

- Normal mode: realistic traffic distribution
- Attack mode: burst + fan-out + contamination to bad actor
- Outputs JSON lines to stdout (one tx per line)
"""

from __future__ import annotations

import sys
import signal
import json
import random
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

# Exit quietly when piping into tools like `head` that close stdout early.
signal.signal(signal.SIGPIPE, signal.SIG_DFL)


Mode = Literal["normal", "attack"]



def safe_print_json(tx: dict) -> None:
    try:
        print(json.dumps(tx), flush=True)
    except BrokenPipeError:
        raise SystemExit(0)

def make_accounts(n: int = 200, prefix: str = "acct_") -> List[str]:
    """Generate a stable population of account IDs."""
    if n <= 0:
        raise ValueError("n must be > 0")
    return [f"{prefix}{i}" for i in range(1, n + 1)]


def now_ts() -> int:
    return int(time.time())


def make_tx(
    sender: str,
    receiver: str,
    amount: float,
    tx_type: str = "bank",
    currency: str = "USD",
    channel: str = "p2p",
    ts: Optional[int] = None,
) -> Dict:
    """Create a transaction dict following the shared schema."""
    if sender == receiver:
        raise ValueError("sender and receiver must be different")
    if amount <= 0:
        raise ValueError("amount must be positive")

    return {
        "id": str(uuid.uuid4()),
        "ts": ts if ts is not None else now_ts(),
        "type": tx_type,
        "sender": sender,
        "receiver": receiver,
        "amount": round(float(amount), 2),
        "currency": currency,
        "channel": channel,
        # meta intentionally omitted in Step 1; can be added later
    }


def _pick_distinct(accounts: List[str]) -> tuple[str, str]:
    """Pick sender, receiver ensuring they're different."""
    sender = random.choice(accounts)
    receiver = random.choice(accounts)
    while receiver == sender:
        receiver = random.choice(accounts)
    return sender, receiver


def _normal_amount() -> float:
    """
    Normal traffic amount distribution:
    - Mostly small ($10–$500)
    - Some medium ($500–$1500)
    - Rare larger ($1500–$4000)
    """
    p = random.random()
    if p < 0.85:
        return random.uniform(10, 500)
    elif p < 0.98:
        return random.uniform(500, 1500)
    else:
        return random.uniform(1500, 4000)


def generate_normal_tx(accounts: List[str]) -> Dict:
    sender, receiver = _pick_distinct(accounts)
    amount = _normal_amount()
    return make_tx(sender=sender, receiver=receiver, amount=amount, tx_type="bank", channel="p2p")


@dataclass
class AttackState:
    """
    State to create coherent attack behavior:
    - A fixed attacker sends bursts and fan-outs
    - Uses rotating unique receivers
    - Occasionally routes to a known bad actor for contamination
    """
    attacker: str = "acct_attack"
    bad_actor: str = "acct_999"
    phase: int = 0
    used_receivers: set = field(default_factory=set)
    phase_tx_count: int = 0


def generate_attack_tx(accounts: List[str], state: AttackState) -> Dict:
    """
    Attack mode patterns (combined):
    1) Burst: same sender repeatedly sends fast
    2) Fan-out: many unique receivers within a short window
    3) Contamination: sometimes link to bad actor
    """
    sender = state.attacker
    state.phase_tx_count += 1

    # Simple phased behavior:
    # phase 0: burst to a small pool (build some edges)
    # phase 1: fan-out to many unique receivers (laundering feel)
    # phase 2: chain-hop simulation (attacker -> mid -> bad) by sometimes hitting bad_actor
    if state.phase == 0:
        # burst: small pool of receivers
        pool = random.sample(accounts, k=min(8, len(accounts)))
        receiver = random.choice(pool)
        amount = random.uniform(50, 300)  # moderate
        if state.phase_tx_count >= 25:
            state.phase = 1
            state.phase_tx_count = 0

    elif state.phase == 1:
        # fan-out: try to pick a receiver not used recently
        receiver = random.choice(accounts)
        tries = 0
        while receiver in state.used_receivers and tries < 20:
            receiver = random.choice(accounts)
            tries += 1
        state.used_receivers.add(receiver)

        amount = random.uniform(5, 200)  # smurfing-ish

        # After enough unique receivers, move to contamination phase
        if len(state.used_receivers) >= 20 or state.phase_tx_count >= 40:
            state.phase = 2
            state.phase_tx_count = 0

    else:
        # contamination: occasionally send to bad actor to create short paths
        if random.random() < 0.25:
            receiver = state.bad_actor
        else:
            receiver = random.choice(accounts)

        # keep amounts small-ish to resemble laundering/structuring
        amount = random.uniform(5, 150)

        # Reset attack cycle to keep the demo repeating
        if state.phase_tx_count >= 40:
            state.phase = 0
            state.phase_tx_count = 0
            state.used_receivers.clear()

    # Ensure receiver != sender
    if receiver == sender:
        receiver = random.choice([a for a in accounts if a != sender])

    return make_tx(sender=sender, receiver=receiver, amount=amount, tx_type="bank", channel="p2p")


class SimulatorCore:
    """
    Standalone simulator runner.
    - normal: ~3 tx/sec
    - attack: ~10 tx/sec
    """
    def __init__(self, accounts: List[str], seed: Optional[int] = None):
        self.accounts = accounts
        self.mode: Mode = "normal"
        self.running = False
        self.attack_state = AttackState()

        if seed is not None:
            random.seed(seed)

    def set_mode(self, mode: Mode) -> None:
        if mode not in ("normal", "attack"):
            raise ValueError("mode must be 'normal' or 'attack'")
        self.mode = mode

    def start(self, mode: Mode = "normal") -> None:
        self.set_mode(mode)
        self.running = True

    def stop(self) -> None:
        self.running = False

    def _sleep_interval(self) -> float:
        # target rates: normal ~3/s (0.33s), attack ~10/s (0.10s)
        return 0.33 if self.mode == "normal" else 0.10

    def next_tx(self) -> Dict:
        if self.mode == "normal":
            return generate_normal_tx(self.accounts)
        return generate_attack_tx(self.accounts, self.attack_state)

    def run_loop(self) -> None:
        """
        Runs until Ctrl+C or stop() called.
        Prints one JSON per line.
        """
        self.running = True
        try:
            while self.running:
                tx = self.next_tx()
                safe_print_json(tx)
                time.sleep(self._sleep_interval())
        except KeyboardInterrupt:
            self.running = False


def main():
    accounts = make_accounts(n=200)
    sim = SimulatorCore(accounts=accounts, seed=42)

    # Demo: run normal for 5 seconds, then attack for 8 seconds, then back to normal.
    sim.start("normal")
    t0 = time.time()
    try:
        while True:
            elapsed = time.time() - t0
            if 5 <= elapsed < 13:
                sim.set_mode("attack")
            else:
                sim.set_mode("normal")

            tx = sim.next_tx()
            safe_print_json(tx)
            time.sleep(sim._sleep_interval())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
