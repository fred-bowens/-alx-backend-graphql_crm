import datetime
import requests

def log_crm_heartbeat():
    now = datetime.datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    message = f"{now} CRM is alive"

    with open("/tmp/crm_heartbeat_log.txt", "a") as f:
        f.write(message + "\n")

    # Optional: verify GraphQL endpoint responsiveness
    try:
        response = requests.post(
            "http://localhost:8000/graphql/",
            json={"query": "{ hello }"},
            timeout=3
        )
        if response.status_code == 200 and "data" in response.json():
            print("GraphQL responded:", response.json()["data"].get("hello"))
        else:
            print("GraphQL did not respond properly.")
    except Exception as e:
        print("GraphQL check failed:", e)
