import datetime
from celery import shared_task
import requests

@shared_task
def generate_crm_report():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = "/tmp/crm_report_log.txt"

    query = """
    query {
      totalCustomers: allCustomers {
        id
      }
      totalOrders: allOrders {
        id
        totalAmount
      }
    }
    """

    try:
        response = requests.post(
            "http://localhost:8000/graphql/",
            json={"query": query},
            timeout=5
        )

        data = response.json()["data"]
        customers = data["totalCustomers"]
        orders = data["totalOrders"]

        total_customers = len(customers)
        total_orders = len(orders)
        total_revenue = sum([float(o["totalAmount"]) for o in orders])

        with open(log_file, "a") as f:
            f.write(f"{timestamp} - Report: {total_customers} customers, {total_orders} orders, ${total_revenue:.2f} revenue\n")

    except Exception as e:
        with open(log_file, "a") as f:
            f.write(f"{timestamp} - ERROR generating report: {e}\n")
