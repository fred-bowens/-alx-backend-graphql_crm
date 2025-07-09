import datetime
import requests

def update_low_stock():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_path = "/tmp/low_stock_updates_log.txt"

    mutation = """
    mutation {
      updateLowStockProducts {
        id
        name
        stock
      }
    }
    """

    try:
        response = requests.post(
            "http://localhost:8000/graphql/",
            json={"query": mutation},
            timeout=5
        )

        data = response.json()
        updated_products = data.get("data", {}).get("updateLowStockProducts", [])

        with open(log_path, "a") as log_file:
            log_file.write(f"{timestamp} - Updated Products:\n")
            for product in updated_products:
                name = product["name"]
                stock = product["stock"]
                log_file.write(f"  - {name}: Stock is now {stock}\n")
            log_file.write("\n")

    except Exception as e:
        with open(log_path, "a") as log_file:
            log_file.write(f"{timestamp} - Error during stock update: {str(e)}\n")
