import time
from valkey_store import ValkeyStore


def print_section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def main():
    store = ValkeyStore()

    print_section("1. Testing Connection")
    assert store.ping() is True
    print("PING OK")

    # Clean database
    store.r.flushall()

    # Sample transaction
    tx = {
        "id": "tx_1",
        "ts": int(time.time()),
        "sender": "acct_1",
        "receiver": "acct_2",
        "amount": 150
    }

    print_section("2. Testing Stream Storage")
    stream_id = store.add_transaction_to_stream(tx)
    assert stream_id is not None
    print("Stream ID:", stream_id)

    recent = store.get_recent(5)
    assert len(recent) == 1
    print("Stream entry stored correctly")

    print_section("3. Testing Transaction Hash Storage")
    store.store_transaction_hash(tx)
    stored_hash = store.r.hgetall(store.get_tx_key("tx_1"))
    assert stored_hash["sender"] == "acct_1"
    print("Transaction hash stored correctly")

    print_section("4. Testing Graph Storage")
    store.update_graph(tx["sender"], tx["receiver"])
    neighbors = store.get_neighbors("acct_1")
    assert "acct_2" in neighbors
    print("Graph adjacency stored correctly")

    print_section("5. Testing Rolling Behavior Metrics")
    store.update_behavior(tx)

    bucket = store.minute_bucket(tx["ts"])
    cnt_key = store.get_count_key("acct_1", bucket)
    vol_key = store.get_volume_key("acct_1", bucket)
    uniq_key = store.get_unique_recipient_key("acct_1", bucket)

    count_val = int(store.r.get(cnt_key))
    volume_val = float(store.r.get(vol_key))
    uniq_count = store.r.pfcount(uniq_key)

    assert count_val == 1
    assert volume_val == 150.0
    assert uniq_count == 1

    print("Rolling metrics working correctly")

    print_section("6. Testing Decision Storage + Leaderboard")
    store.store_decision("tx_1", "acct_1", risk=75, hops=2)

    tx_hash = store.r.hgetall("tx:tx_1")
    node_hash = store.r.hgetall("node:acct_1")
    leaderboard = store.get_top_risk(5)

    assert tx_hash["risk"] == "75"
    assert node_hash["risk"] == "75"
    assert leaderboard[0][0] == "acct_1"

    print("Decision + leaderboard working correctly")

    print_section("7. Testing Bad Node Seeding")
    store.seed_bad_node("acct_bad")
    assert store.r.sismember(store.BAD_NODES, "acct_bad") == 1
    print("Bad node seeded correctly")

    print_section("ALL TESTS PASSED")
    print("Valkey Data Engine is functioning correctly.")


if __name__ == "__main__":
    main()
