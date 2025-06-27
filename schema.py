import graphene
from crm.schema import Query as CRMQuery, Mutation as CRMMutation
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
import re

from .models import Customer, Product, Order

class Query(graphene.ObjectType):
   
    hello = graphene.String()

    def resolve_hello(root, info):
        return "Hello, GraphQL!"
schema = graphene.Schema(query=Query)

class Query(CRMQuery, graphene.ObjectType):
    pass

class Mutation(CRMMutation, graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)

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
        fields = ("id", "customer", "products", "total_amount", "order_date")

class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()

class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Float(required=True)
    stock = graphene.Int(default_value=0)

class CreateOrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime()

class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()
    error = graphene.String()

    def mutate(self, info, input):
        if Customer.objects.filter(email=input.email).exists():
            return CreateCustomer(error="Email already exists")

        if input.phone:
            phone_pattern = re.compile(r'^(\+?\d{10,15}|\d{3}-\d{3}-\d{4})$')
            if not phone_pattern.match(input.phone):
                return CreateCustomer(error="Invalid phone format")

        customer = Customer.objects.create(
            name=input.name, email=input.email, phone=input.phone
        )
        return CreateCustomer(customer=customer, message="Customer created successfully")

class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, input):
        created = []
        errors = []

        for idx, customer_data in enumerate(input):
            try:
                if Customer.objects.filter(email=customer_data.email).exists():
                    raise ValidationError(f"Email '{customer_data.email}' already exists")

                if customer_data.phone:
                    phone_pattern = re.compile(r'^(\+?\d{10,15}|\d{3}-\d{3}-\d{4})$')
                    if not phone_pattern.match(customer_data.phone):
                        raise ValidationError("Invalid phone format")

                customer = Customer.objects.create(
                    name=customer_data.name,
                    email=customer_data.email,
                    phone=customer_data.phone
                )
                created.append(customer)

            except ValidationError as e:
                errors.append(f"Record {idx}: {str(e)}")

        return BulkCreateCustomers(customers=created, errors=errors)

class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)
    error = graphene.String()

    def mutate(self, info, input):
        if input.price <= 0:
            return CreateProduct(error="Price must be positive")

        if input.stock < 0:
            return CreateProduct(error="Stock cannot be negative")

        product = Product.objects.create(
            name=input.name,
            price=input.price,
            stock=input.stock
        )
        return CreateProduct(product=product)

class CreateOrder(graphene.Mutation):
    class Arguments:
        input = CreateOrderInput(required=True)

    order = graphene.Field(OrderType)
    error = graphene.String()

    def mutate(self, info, input):
        try:
            customer = Customer.objects.get(pk=input.customer_id)
        except Customer.DoesNotExist:
            return CreateOrder(error="Invalid customer ID")

        products = Product.objects.filter(id__in=input.product_ids)
        if not products:
            return CreateOrder(error="No valid products selected")

        if products.count() != len(set(input.product_ids)):
            return CreateOrder(error="One or more invalid product IDs")

        total = sum([p.price for p in products])
        order_date = input.order_date or timezone.now()

        order = Order.objects.create(
            customer=customer,
            order_date=order_date,
            total_amount=total
        )
        order.products.set(products)
      return CreateOrder(order=order)

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()


