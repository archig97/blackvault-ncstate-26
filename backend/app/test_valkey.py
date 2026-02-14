from valkey_store import ValkeyStore

def main():
    store = ValkeyStore()
    
    print("Testing connection...")
    result = store.ping()
    
    print("PING response:", result)

if __name__ == "__main__":
    main()