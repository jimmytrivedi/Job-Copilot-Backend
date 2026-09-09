from backend.qdrant_client_db import client, init_dqrant

if __name__ == "__main__":
    init_dqrant()
    print("Ingest complete.")