from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


# from django.core.exceptions import ValidationError
# from django.utils.translation import gettext_lazy as _

#
# def validate_nonNegative(value):
#     if value < 0:
#         raise ValidationError(
#             _('%(value)s is not a non-negative number!'),
#             params={'value': value},
#         )
class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    phone = models.CharField(max_length=30, null=True)
    address = models.TextField()
    balance = models.PositiveIntegerField(default=20000, null=True)

    def deposit(self, amount):
        self.balance += amount
        self.save()

    def spend(self, amount):
        if amount > self.balance:
            raise Exception("amount is bigger than customer's balance")
        else:
            self.balance -= amount
            self.save()

    def to_dict(self):
        return {
            "id": self.user.id,
            "username": self.user.username,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "email": self.user.email,
            "phone": self.phone,
            "address": self.address,
            "balance": self.balance
        }

    def __str__(self):
        return "Customer{address:%s, balance:%i, phone:%s, user:%s}" \
               % (self.address, self.balance, self.phone, str(self.user))


class Product(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    price = models.PositiveIntegerField()
    inventory = models.PositiveIntegerField(default=0, null=True)

    def __str__(self):
        return "Product{code:%s, name:%s, price:%i, inventory:%i}" \
               % (self.code, self.name, self.price, self.inventory)

    def increase_inventory(self, amount):
        self.inventory += amount
        self.save()

    def decrease_inventory(self, amount):
        if amount > self.inventory:
            raise Exception("Not enough inventory. (or other messages)")
        else:
            self.inventory -= amount
            self.save()

    def to_dict(self):
        return {'id': self.id, 'code': self.code, 'name': self.name,
                'price': self.price, 'inventory': self.inventory}


class Order(models.Model):
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE)
    order_time = models.DateTimeField()
    total_price = models.PositiveIntegerField()

    STATUS_SHOPPING = 1
    STATUS_SUBMITTED = 2
    STATUS_CANCELED = 3
    STATUS_SENT = 4

    status_choices = (
        (STATUS_SHOPPING, "shopping"),
        (STATUS_SUBMITTED, "submitted"),
        (STATUS_CANCELED, "canceled"),
        (STATUS_SENT, "sent")
    )
    status = models.IntegerField(choices=status_choices)

    @staticmethod
    def initiate(customer: Customer):
        """
                initiates and returns a new order
                :param customer:Customer
                :return:Order
                """

        if Order.STATUS_SHOPPING in [item.status for item in Order.objects.filter(customer=customer)]:
            return Order.objects.filter(status=Order.STATUS_SHOPPING).get(customer=customer)
            # item is those orders involved with this customer
        order = Order(customer=customer,
                      status=Order.STATUS_SHOPPING,
                      order_time=timezone.now(), total_price=0)
        order.save()
        order.getRows()
        return order

    def add_product(self, product: Product, amount: int):
        # self.status = 1
        # if self.orderrow_set.filter(product=product).exists():
        #     preexisting_order_row = OrderRow.objects.get(product=product, order=self)
        #     preexisting_order_row.amount += amount
        #     preexisting_order_row.save()
        # else:
        #     # new_order_row = OrderRow(product=product, order=self)
        #     # new_order_row.amount += amount
        #     # new_order_row.save()
        #     new_order_row = OrderRow.objects.create(
        #         order=self,
        #         product=product,
        #         amount=amount
        #     )
        #     # create saves already

        """Adds <amount> number of <product> into order card.
                :param product:Product
                :param amount:int
                :return:void
                """

        if amount <= 0:
            raise Exception("Wrong operation.")
        if amount > Product.objects.get(code=product.code).inventory:
            raise Exception("Not enough inventory.")
        if product.code in [item.product.code for item in self.getRows()]:
            # this product have been in order before. so we just increase the amount.
            order_row = self.getOrderRow(product)
            # order-row is instance of OrderRow class, so it's an object and has save(), delete() and ...
            # we just retrieve the row related with this product to update the amount.
            order_row.amount += amount
            if order_row.amount > Product.objects.get(code=product.code).inventory:
                raise Exception("Not enough inventory.")
            order_row.save()
        else:
            order_row = OrderRow(product=product, amount=amount, order=self)
            order_row.save()

        self.order_time = timezone.now()
        self.total_price += product.price * amount
        self.save()

    def remove_product(self, product: Product, amount: int = None):
        # if self.orderrow_set.filter(product=product).exists():
        #     order_row = OrderRow.objects.get(order=self, product=product)
        #     order_row.amount -= amount
        # else:
        #     raise ValueError

        """Removes <amount> number of <product>s existing in order card.
                If amount would not be given all the <product>s will be removed.
                :param product:Product
                :param amount:int Optional
                :return:void
                """

        if amount and amount <= 0 or not Product.objects.filter(code=product.code).exists():
            raise Exception("Wrong operation.")

        if product.code in [item.product.code for item in self.getRows()]:
            order_row = self.getOrderRow(product)
            if amount is None or order_row.amount == amount:
                order_row.delete()
                self.total_price -= product.price * order_row.amount
            elif order_row.amount > amount:
                order_row.amount -= amount
                self.total_price -= product.price * amount
                order_row.save()
            else:
                raise Exception("Entered amount is more than the amount in the card.")

        else:
            raise Exception("Product not found in cart.")

        from django.utils import timezone
        self.order_time = timezone.now()
        self.save()

    def submit(self):
        # # if self.customer.balance >= self.total_price and self.status == 1:
        # #     order_products = OrderRow.objects.filter(order=self)
        # #     for p in order_products:
        # #         if p.amount <= p.product.inventory:
        # #             self.status = 2
        #
        # """Saves the order and turn's order status to STATUS_SHOPPING
        #         if enough amount of ordered products could be satisfied.
        #         :return:void
        #         """
        #
        # #       validation
        #
        # # It's better to reduce product's inventories before validating inorder
        # # to prevent conflict between the shopping.
        # # If the submit was not success full the inventories will be increased by the decreased value.
        #
        # if self.status != Order.STATUS_SHOPPING:
        #     raise Exception("This order is not submittable.")
        # if len(self.getRows()) == 0:
        #     raise Exception("The cart is empty.")
        #
        # temporarily_reduced = dict()
        #
        # def recharge_inventories(max_):
        #     """Increases inventories by reduced value, for all of manipulated products.
        #     :param max_:int last index of manipulated products in orderRows list. #exlusive!"""
        #     for order_row_ in self.getRows():
        #         order_row_.product.increase_inventory(temporarily_reduced[order_row_.id])
        #
        # i = 0
        # for order_row in self.getRows():
        #     if order_row.amount > order_row.product.inventory:
        #         recharge_inventories(i)
        #         raise Exception(
        #             """The product \"%s\" has been bought by other customers while you where shopping.
        #             Now the product's inventory is %i numbers.""" \
        #             % (order_row.product.name, order_row.product.inventory))
        #     else:
        #         temporarily_reduced[order_row.id] = order_row.amount
        #         order_row.product.decrease_inventory(order_row.amount)
        #     i += 1
        # price_sum = sum([item.product.price * item.amount for item in self.getRows()])
        # customer_balance = self.customer.balance
        # if price_sum > customer_balance:
        #     recharge_inventories(i)
        #     raise Exception("Not enough balance.")
        #     #       submit
        # self.customer.balance -= price_sum
        # self.customer.save()
        # self.status = Order.STATUS_SUBMITTED
        # from django.utils import timezone
        # self.order_time = timezone.now()
        # self.save()
        '''This function is overridden by me'''
        if self.status != Order.STATUS_SHOPPING:
            raise Exception("This order can't be submitted.")
        if len(self.getRows()) == 0:
            raise Exception("Shopping cart is empty.")
        for order_row in self.getRows():
            order_row.product.decrease_inventory(order_row.amount)
            order_row.product.save()
        customer_balance = self.customer.balance
        price_sum = sum([item.product.price * item.amount for item in self.getRows()])
        if price_sum > customer_balance:
            raise Exception("Not enough money")
        self.customer.balance -= customer_balance
        self.customer.save()
        self.status = Order.STATUS_SUBMITTED
        self.order_time = timezone.now()
        self.save()

    def cancel(self):
        # if self.status != 4 and self.status == 2:
        #     order_rows = OrderRow.objects.filter(order=self)
        #     for row in order_rows:
        #         row.delete()
        #     self.status = 3
        #     self.customer.balance += self.total_price

        """Cancels the order (if is submitted) and gives back the customers charge.
                Gives back ordered product's to products inventory.
                And changes order status to STATUS_CANCELED
                :return:void
                """
        if self.status != Order.STATUS_SUBMITTED:
            raise Exception("Not permitted operation.")

        if self.status == Order.STATUS_SUBMITTED:
            for order_row in self.getRows():
                self.customer.balance += order_row.product.price * order_row.amount
                self.customer.save()
                order_row.product.increase_inventory(order_row.amount)

        self.status = Order.STATUS_CANCELED
        self.save()

    def send(self):
        # if self.status == 2:
        #     self.status = 4
        """Changes order's status from STATUS_SUBMITTED to STATUS_SENT
                :return:void"""
        if self.status != Order.STATUS_SUBMITTED:
            raise Exception("The order is not submitted or has been cancelled.")
        self.status = Order.STATUS_SENT
        self.save()

    def getOrderRow(self, product: Product):
        return self.orderrow_set.get(product=product)

    def __str__(self):
        dic = dict(Order.status_choices)
        return "Order{customer:%s, order_time:%s, rows:%s, status:%s, total_price:%i}" \
               % (str(self.customer), str(self.order_time), str(self.getRows()), dic[self.status], self.total_price)

    def to_dict(self, errors=None):
        out = {
            'total_price': self.total_price,
        }
        if errors:
            out['errors'] = errors
        out['items'] = [item.to_dict() for item in OrderRow.objects.filter(order=self.id)]
        return out

    def toDict(self):
        return {
            'id': self.id,
            'order_time': self.order_time.strftime("%Y-%m-%d %H:%M:%S"),
            'status': dict(Order.status_choices)[self.status],
            'total_price': self.total_price,
            'rows': [item.to_dict() for item in self.getRows()]
        }

    def getRows(self):
        # this function retrieve all rows of this order.
        self.rows = list(self.orderrow_set.all())
        return self.rows


class OrderRow(models.Model):
    # product = models.ForeignKey('Product', on_delete=models.DO_NOTHING)
    # order = models.ForeignKey('Order', on_delete=models.CASCADE)
    # amount = models.IntegerField()

    """Represents orders one single item.
        product : int - foreign key referring to Product.
        amount : positive int - count of ordered products.
        order : Order - foreign key referring to parent order
        """
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    amount = models.IntegerField()

    def __str__(self):
        return "OrderRow{product:%s, amount: %i}" \
               % (str(self.product), self.amount)

    def to_dict(self):
        return {
            'code': self.product.code,
            'name': self.product.name,
            'price': self.product.price,
            'amount': self.amount
        }
