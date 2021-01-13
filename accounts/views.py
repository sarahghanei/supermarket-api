from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from market.models import Customer
from django.db import IntegrityError
from django.db.models import Q


@csrf_exempt
def customer_register(request):
    if request.method != "POST":
        return JsonResponse(data={"message": "Wrong http method"}, status=400)
    try:
        data = json.loads(request.body.decode('utf-8'))
        user = User(username=data['username'], first_name=data['first_name'],
                    last_name=data['last_name'],
                    email=data['email'])
        user.set_password(data['password'])
        user.save()
    except IntegrityError:
        return JsonResponse({"message": "Username already exists."}, status=400)
    except Exception as e1:
        return JsonResponse({"message": str(e1)}, status=400)
    try:
        customer = Customer(user=user, phone=data['phone'], address=data['address'])
        customer.save()
    except Exception as e2:
        user.delete()
        return JsonResponse({"message": str(e2)}, status=400)
    return JsonResponse(data={"id": user.id}, status=201)


@csrf_exempt
def customer_list(request):
    if request.method != 'GET':
        return JsonResponse({'message': 'Wrong http method.'}, status=400)
        # try:
    customers = Customer.objects.all()
    if 'search' in request.GET:
        from django.db.models import Q
        searched = request.GET['search']
        customers = customers.filter(Q(user__first_name__icontains=searched) |
                                     Q(user__last_name__icontains=searched) |
                                     Q(user__username__icontains=searched) |
                                     Q(address__icontains=searched))
    # except Exception as e:
    #     return JsonResponse({"message": str(e)}, status=400)
    return JsonResponse(data={'customers': [customer.to_dict() for customer in customers]},
                        status=200)


@csrf_exempt
def customer_info(request, customer_id):
    if request.method != 'GET':
        return JsonResponse({'message': 'Wrong http method.'}, status=400)
    try:
        customer = Customer.objects.get(user__id__exact=customer_id)
        return JsonResponse(data=customer.to_dict(), status=200)

    except Customer.DoesNotExist:
        return JsonResponse(data={"message": "Customer Not Found."}, status=404)
    # except Exception as e:
    #     return JsonResponse({"message": str(e)}, status=400)


@csrf_exempt
def customer_edit(request, customer_id):
    if request.method != 'POST':
        return JsonResponse({'message': 'Wrong http method.'}, status=400)
    data = json.loads(request.body.decode('utf-8'))
    try:
        customer = Customer.objects.get(user__id__exact=customer_id)
    except Customer.DoesNotExist:
        return JsonResponse(data={"message": "Customer Not Found."}, status=404)
    try:
        if 'username' in data or 'password' in data or 'id' in data:
            return JsonResponse(data={"message": "Cannot edit customer's identity and credentials."}, status=403)
        if 'first_name' in data:
            customer.user.first_name = data['first_name']
        if 'last_name' in data:
            customer.user.last_name = data['last_name']
        if 'email' in data:
            customer.user.email = data['email']
        if 'phone' in data:
            customer.phone = data['phone']
        if 'address' in data:
            customer.address = data['address']
        if 'balance' in data:
            customer.balance = data['balance']
        customer.save()
        return JsonResponse(data=customer.to_dict(), status=200)
    except Exception as e:
        return JsonResponse({"message": str(e)}, status=400)


@csrf_exempt
def customer_login(request):
    if request.method != 'POST':
        return JsonResponse({'message': 'Wrong http method.'}, status=400)
    try:
        credentials = json.loads(request.body.decode('utf-8'))
    except:
        return JsonResponse({'message': 'Cant read message body.'}, status=400)
    try:
        user = authenticate(request, username=credentials['username'], password=credentials['password'])
        # this function returns a user matching inputs with database or if there is no user with these info, it will return None.
        if user is not None:
            login(request, user)
            return JsonResponse(data={"message": "You are logged in successfully."}, status=200)
        else:
            return JsonResponse(data={"message": "Username or Password is incorrect."}, status=404)
    except Exception as e:
        return JsonResponse({"message": str(e)}, status=400)


@csrf_exempt
def customer_logout(request):
    if request.method != 'POST':
        return JsonResponse({'message': 'Wrong http method.'}, status=400)
    try:
        if request.user.is_authenticated:
            logout(request)
            return JsonResponse(data={"message": "You are logged out successfully."}, status=200)
        else:
            return JsonResponse(data={"message": "You are not logged in."}, status=403)
    except Exception as e:
        return JsonResponse({'message': str(e)}, status=400)


@csrf_exempt
def customer_profile(request):
    if request.method != 'GET':
        return JsonResponse({'message': 'Wrong http method.'}, status=400)
    # try:
    if not request.user.is_authenticated:
        return JsonResponse(data={"message": "You are not logged in."}, status=403)
    else:
        return JsonResponse(request.user.customer.to_dict(), status=200)
    # except Exception as e:
    #     return JsonResponse({'message': str(e)}, status=400)
