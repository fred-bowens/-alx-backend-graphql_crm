import graphene
from graphene import relay
from graphene_django.types import DjangoObjectType
from django.core.exceptions import ValidationError
from django.db import transaction
from datetime import datetime
import re

from .models import Customer, Product, Order

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone")


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "products", "order_date", "total_amount")

class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False)


class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int(required=False, default_value=0)


class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()
    error = graphene.String()

    def mutate(root, info, input):
        
        if input.phone:
            phone_re = re.compile(r'^(\+?\d{10,15}|\d{3}-\d{3}-\d{4})$')
            if not phone_re.match(input.phone):
                return CreateCustomer(error="Invalid phone format")

        if Customer.objects.filter(email=input.email).exists():
            return CreateCustomer(error="Email already exists")

        customer = Customer(name=input.name, email=input.email, phone=input.phone)
        customer.save()
        return CreateCustomer(customer=customer, message="Customer created")

class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        inputs = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    def mutate(root, info, inputs):
        created = []
        errs = []

        with transaction.atomic():
            for idx, cust_in in enumerate(inputs):
                try:
                    
                    if cust_in.phone:
                        phone_re = re.compile(r'^(\+?\d{10,15}|\d{3}-\d{3}-\d{4})$')
                        if not phone_re.match(cust_in.phone):
                            raise ValidationError("Invalid phone format")

                    if Customer.objects.filter(email=cust_in.email).exists():
                        raise ValidationError("Email already exists")

                    cust = Customer(name=cust_in.name, email=cust_in.email, phone=cust_in.phone)
                    cust.save()
                    created.append(cust)

                except ValidationError as e:
                    errs.append(f"Item {idx}: {e.messages[0]}")

        return BulkCreateCustomers(customers=created, errors=errs)

class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)
    error = graphene.String()

    def mutate(root, info, input):
        if input.price <= 0:
            return CreateProduct(error="Price must be positive")
        if input.stock < 0:
            return CreateProduct(error="Stock cannot be negative")

        product = Product(name=input.name, price=input.price, stock=input.stock)
        product.save()
        return CreateProduct(product=product)

class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.ID, required=True)
        order_date = graphene.DateTime(required=False)

    order = graphene.Field(OrderType)
    error = graphene.String()

    def mutate(root, info, customer_id, product_ids, order_date=None):
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            return CreateOrder(error="Invalid customer ID")

        products = list(Product.objects.filter(pk__in=product_ids))
        if not products:
            return CreateOrder(error="No valid products selected")
        if len(products) != len(set(product_ids)):
            return CreateOrder(error="One or more invalid product IDs")
        order = Order(customer=customer, order_date=order_date or datetime.now())
        order.total_amount = sum([p.price for p in products])
        order.save()
        order.products.set(products)

        return CreateOrder(order=order)

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()


class Query(graphene.ObjectType):
    customers = graphene.List(CustomerType)
    products = graphene.List(ProductType)
    orders = graphene.List(OrderType)

    def resolve_customers(root, info):
        return Customer.objects.all()

    def resolve_products(root, info):
        return Product.objects.all()

    def resolve_orders(root, info):
        return Order.objects.select_related('customer').prefetch_related('products').all()

import graphene
from crm.schema import Query as CRMQuery, Mutation as CRMMutation

class Query(CRMQuery, graphene.ObjectType):
    pass

class Mutation(CRMMutation, graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)


mutation {
  createCustomer(input: {
    name: "Alice", email: "alice@example.com", phone: "+1234567890"
  }) {
    customer { id name email phone }
    message
    error
  }
}

mutation {
  bulkCreateCustomers(inputs: [
    { name: "Bob", email: "bob@example.com", phone: "123-456-7890" },
    { name: "Carol", email: "carol@example.com" }
  ]) {
    customers { id name email }
    errors
  }
}

mutation {
  createProduct(input: { name: "Laptop", price: 999.99, stock: 10 }) {
    product { id name price stock }
    error
  }
}


mutation {
  createOrder(customerId: "1", productIds: ["1","2"]) {
    order {
      id
      customer { name }
      products { name price }
      totalAmount
      orderDate
    }
    error
  }
}
