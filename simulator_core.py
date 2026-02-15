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
import requests
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
class SimulationScenario:
    """
    Configurable attack scenario with realistic account ecosystem.
    Replaces single hardcoded attacker model.
    """
    normal_accounts: List[str]         # Regular users (low activity)
    merchant_accounts: List[str]       # High-freq legitimate (baseline)
    fraudster_accounts: List[str]      # Primary attackers
    laundering_hubs: List[str]         # Compromised intermediaries
    sanctioned_accounts: List[str]     # Known bad destinations
    
    phase: int = 0
    phase_tx_count: int = 0
    current_fraudster_idx: int = 0


def create_attack_scenario(
    normal_count: int = 150,
    merchant_count: int = 30,
    fraudster_count: int = 3,
    laundering_hub_count: int = 5,
    sanctioned_count: int = 3,
) -> SimulationScenario:
    """
    Build a realistic multi-actor attack scenario.
    
    Default: 150 normal users + 30 merchants (cover)
             3 fraudsters + 5 laundering hubs + 3 sanctioned
             Total: ~191 accounts (much better than acct_attack + acct_999)
    """
    return SimulationScenario(
        normal_accounts=[f"acct_user_{i}" for i in range(normal_count)],
        merchant_accounts=[f"acct_merchant_{i}" for i in range(merchant_count)],
        fraudster_accounts=[f"acct_fraud_{i}" for i in range(fraudster_count)],
        laundering_hubs=[f"acct_launder_{i}" for i in range(laundering_hub_count)],
        sanctioned_accounts=[f"acct_sanctioned_{i}" for i in range(sanctioned_count)],
    )


def generate_attack_tx(scenario: SimulationScenario) -> Dict:
    """
    Multi-phase attack pattern showing realistic fraud lifecycle.
    
    Phase 0: Reconnaissance - fraudster probes target accounts (merchants + hubs)
    Phase 1: Exploitation - fraudster sends to laundering hubs
    Phase 2: Routing - hubs distribute to sanctioned accounts
    Phase 3: Cover - merchants conduct normal transactions
    """
    sender = None
    receiver = None
    amount = 0.0
    
    scenario.phase_tx_count += 1
    
    # Cycle through fraudsters
    if scenario.phase_tx_count >= 100:
        scenario.phase_tx_count = 0
        scenario.current_fraudster_idx = (scenario.current_fraudster_idx + 1) % len(scenario.fraudster_accounts)
        scenario.phase = (scenario.phase + 1) % 4
    
    if scenario.phase == 0:  # RECONNAISSANCE
        # Fraudster probes merchants and laundering hubs
        sender = scenario.fraudster_accounts[scenario.current_fraudster_idx]
        receiver = random.choice(scenario.merchant_accounts + scenario.laundering_hubs)
        amount = random.uniform(100, 500)  # Small probes
        
    elif scenario.phase == 1:  # EXPLOITATION
        # Fraudster sends larger amounts to laundering hubs
        sender = scenario.fraudster_accounts[scenario.current_fraudster_idx]
        receiver = random.choice(scenario.laundering_hubs)
        amount = random.uniform(1000, 5000)  # Larger transfers
        
    elif scenario.phase == 2:  # ROUTING
        # Laundering hub routes to sanctioned accounts
        sender = random.choice(scenario.laundering_hubs)
        receiver = random.choice(scenario.sanctioned_accounts)
        amount = random.uniform(500, 2000)  # Split amounts
        
    else:  # PHASE 3: COVER
        # Merchants conduct normal high-freq transactions
        sender = random.choice(scenario.merchant_accounts)
        receiver = random.choice(scenario.normal_accounts)
        amount = random.uniform(50, 300)
    
    # Ensure sender != receiver
    if sender == receiver:
        receiver = random.choice(scenario.normal_accounts + scenario.merchant_accounts + 
                                scenario.laundering_hubs + scenario.fraudster_accounts)
        while receiver == sender:
            receiver = random.choice(scenario.normal_accounts)

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
