from valkey_store import ValkeyStore
import time

store = ValkeyStore()

# Clear previous data (optional but good for testing)
store.r.flushall()

tx = {
    "id": "tx_1",
    "ts": int(time.time()),
    "sender": "acct_1",
    "receiver": "acct_2",
    "amount": 100
}

stream_id = store.add_transaction_to_stream(tx)

print("Stream ID:", stream_id)

recent = store.r.xrevrange(store.TX_STREAM, count=5)
print("Recent Stream Entries:")
print(recent)