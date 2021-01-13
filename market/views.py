from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
import json
from django.db import IntegrityError
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from market.models import Product, Customer, Order


@csrf_exempt
def product_insert(request):
    if request.method != 'POST':
        return JsonResponse(data={"message": "Wrong method"}, status=400)
    try:
        data = json.loads(request.body.decode('utf-8'))
    except:
        return JsonResponse(data={"message": "Can't read request's body"}, status=400)
    product = Product(code=data['code'], name=data['name'], price=data['price'])
    if 'inventory' in data:
        product.inventory = data['inventory']
    try:
        product.save()
    except IntegrityError:
        return JsonResponse(data={"message": "Duplicate code (or other messages)"}, status=400)
    return JsonResponse(data={"id": product.id}, status=201)


@csrf_exempt
def product_list(request):
    if request.method != "GET":
        return JsonResponse(data={"message": "Wrong method"}, status=400)
    products = Product.objects.all()
    if 'search' in request.GET:
        products = products.filter(name__icontains=request.GET['search'])
    return JsonResponse(data={"products": [product.to_dict() for product in products]}, status=200)


@csrf_exempt
def product_detail(request, product_id):
    if request.method != "GET":
        return JsonResponse(data={"message": "Wrong method"}, status=400)
    # product = get_object_or_404(Product, pk=request.GET["product_id"])
    try:
        product = Product.objects.get(id=product_id)
        return JsonResponse(data=product.to_dict(), status=200)
    except Product.DoesNotExist:
        return JsonResponse(data={"message": "Product Not Found."}, status=404)


@csrf_exempt
def edit_inventory(request, product_id):
    if request.method != "POST":
        return JsonResponse(data={"message": "Wrong method"}, status=400)
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return JsonResponse(data={"message": "Product Not Found."}, status=404)
    try:
        body = json.loads(request.body.decode("utf-8"))
    except:
        return JsonResponse({'message': "Can't read request body."}, status=400)
    if "amount" not in body:
        return JsonResponse({'message': "Amount not found."}, status=400)
    amount = body["amount"]
    try:
        if amount > 0:
            product.increase_inventory(amount)
        else:
            amount *= -1
            product.decrease_inventory(amount)
    except Exception as e:
        return JsonResponse(data={"message": str(e)}, status=400)
    return JsonResponse(data=product.to_dict(), status=200)


def shopping_cart(request):
    if request.method != "GET":
        return JsonResponse(data={"message": "Wrong method"}, status=400)
    # is_active is a field for user model and is_authenticated is a function for user model.
    if request.user.is_authenticated and request.user.is_active:
        order = Order.initiate(request.user.customer)
        return JsonResponse(order.to_dict(), status=200)
    else:
        return JsonResponse(data={"message": "You are not logged in."}, status=403)


def add_items(request):
    if request.method != "POST":
        return JsonResponse(data={"message": "Wrong method"}, status=400)
    try:
        if request.user.is_authenticated and request.user.is_active:
            data = json.loads(request.body.decode('utf-8'))
            try:
                if not isinstance(data, list):
                    raise Exception()
            except:
                return JsonResponse(data={"message": "Can't read message body"}, status=400)
            order = Order.initiate(request.user.customer)
            errors = []
            for item in data:
                if 'code' in item and 'amount' not in item:
                    errors.append({'code': item['code'],
                                   'message': "Item has no 'amount' property."
                                   })
                    continue
                if 'code' not in item:
                    errors.append({'code': "???",
                                   'message': "Item has no 'code' property."
                                   })
                    continue
                try:
                    if Product.objects.filter(code=item['code']).exists():
                        order.add_product(Product.objects.get(code=item['code']), item['amount'])
                    else:
                        raise Exception("Product not found.")
                except Exception as e:
                    errors.append({'code': item['code'],
                                   'message': str(e)
                                   })
            if errors:
                return JsonResponse(order.to_dict(errors), status=400)
            else:
                return JsonResponse(order.to_dict(), status=200)
        else:
            return JsonResponse(data={"message": "You are not logged in."}, status=403)
    except Exception as e:
        return JsonResponse(data=str(e), status=400)


def remove_items(request):
    if request.method != "POST":
        return JsonResponse(data={"message": "Wrong method"}, status=400)
    try:
        if request.user.is_active and request.user.is_authenticated:
            try:
                data = json.loads(request.body.decode('utf-8'))
                if not isinstance(data, list):
                    raise Exception()
            except:
                return JsonResponse(data={"message": "Can't read message body"}, status=400)
            order = Order.initiate(request.user.customer)
            errors = []
            for item in data:
                if 'code' not in item:
                    errors.append({'code': "???",
                                   'message': "Item has no 'code' property."
                                   })
                    continue
                try:
                    if Product.objects.filter(code=item['code']).exists():
                        if 'amount' not in item:
                            item['amount'] = None
                        order.remove_product(Product.objects.get(code=item['code']), amount=item['amount'])
                    else:
                        raise Exception("Product not found.")
                except Exception as e:
                    errors.append({'code': item['code'],
                                   'message': str(e)
                                   })
            if errors:
                return JsonResponse(order.to_dict(errors), status=400)
            else:
                return JsonResponse(order.to_dict(), status=200)
        else:
            return JsonResponse(data={"message": "You are not logged in."}, status=403)
    except Exception as e:
        return JsonResponse(data=str(e), status=400)


def submit(request):
    if request.method != "POST":
        return JsonResponse(data={"message": "Wrong method"}, status=400)
    try:
        if len(json.loads(request.body.decode('utf-8'))):
            raise Exception("")
    except:
        return JsonResponse({"message": "Can't read request body."}, status=400)
    try:
        if request.user.is_active and request.user.is_authenticated:
            data = json.loads(request.body.decode('utf-8'))
            if not isinstance(data, dict):
                return JsonResponse({'message': 'Not able to read your request body.'}, status=404)
            order = Order.initiate(request.user.customer)
            try:
                order.submit()
            except Exception as e:
                return JsonResponse({"message": str(e)}, status=400)
            return JsonResponse(order.toDict(), status=200)
        else:
            return JsonResponse(data={"message": "You are not logged in."}, status=403)
    except Exception as e:
        return JsonResponse(data=str(e), status=400)
