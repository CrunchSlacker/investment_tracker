import os
from dotenv import load_dotenv
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.configuration import Configuration
from plaid.api_client import ApiClient
from plaid.model.item_public_token_exchange_response import ItemPublicTokenExchangeResponse
from .models import PlaidAccount
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect

# Load environment variables
load_dotenv()

def home(request):
    return HttpResponse("<h1>Welcome to the Investment Tracker</h1><a href='/plaid/link/'>Link Your Account</a>")

@login_required
def link_account_page(request):
    return render(request, 'plaidapp/link_account.html')

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # log them in automatically
            return redirect('link_account_page')  # go to Plaid flow or dashboard
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

# Set up Plaid configuration
PLAID_ENV = os.getenv("PLAID_ENV", "sandbox").lower()
PLAID_HOST = {
    "sandbox": "https://sandbox.plaid.com",
    "development": "https://development.plaid.com",
    "production": "https://production.plaid.com"
}[PLAID_ENV]

configuration = Configuration(
    host=PLAID_HOST,
    api_key={
        "clientId": os.getenv("PLAID_CLIENT_ID"),
        "secret": os.getenv("PLAID_SECRET"),
    }
)

api_client = ApiClient(configuration)
plaid_client = plaid_api.PlaidApi(api_client)


# ----------- Create Link Token -----------
@login_required
def create_link_token(request):
    user = request.user
    request_data = LinkTokenCreateRequest(
        user=LinkTokenCreateRequestUser(client_user_id=str(user.id)),
        client_name="Investment Tracker",
        products=[Products.INVESTMENTS],
        country_codes=[CountryCode("US")],
        language="en"
    )
    response = plaid_client.link_token_create(request_data)
    return JsonResponse({'link_token': response['link_token']})


# ----------- Exchange Public Token -----------
@csrf_exempt
@login_required
@require_http_methods(["POST"])
def exchange_public_token(request):
    public_token = request.POST.get("public_token")

    if not public_token:
        return JsonResponse({'error': 'Missing public_token'}, status=400)

    exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
    exchange_response: ItemPublicTokenExchangeResponse = plaid_client.item_public_token_exchange(exchange_request)

    access_token = exchange_response.access_token
    item_id = exchange_response.item_id

    # Save to DB
    PlaidAccount.objects.create(
        user=request.user,
        access_token=access_token,
        item_id=item_id
    )

    return JsonResponse({'status': 'linked', 'item_id': item_id})
