#!/usr/bin/env python3

import datetime
import logging
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# Configure logging
timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
log_file = "/tmp/order_reminders_log.txt"

# Set up the GraphQL transport
transport = RequestsHTTPTransport(
    url="http://localhost:8000/graphql",
    verify=False,
    retries=3,
)

client = Client(transport=transport, fetch_schema_from_transport=False)

# Get the date 7 days ago
seven_days_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).date()

# GraphQL query to get recent orders
query = gql(
    """
    query ($since: Date!) {
      recentOrders: allOrders(orderDate_Gte: $since) {
        id
        customer {
          email
        }
      }
    }
    """
)

# Execute the query
params = {"since": str(seven_days_ago)}
result = client.execute(query, variable_values=params)

# Log each order
with open(log_file, "a") as log:
    for order in result["recentOrders"]:
        order_id = order["id"]
        email = order["customer"]["email"]
        log.write(f"{timestamp} - Order ID: {order_id}, Email: {email}\n")

print("Order reminders processed!")
