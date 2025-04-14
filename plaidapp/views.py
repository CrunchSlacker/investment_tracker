import os
import json
from dotenv import load_dotenv

from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.urls import reverse

from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from plaid.model.item_public_token_exchange_response import (
    ItemPublicTokenExchangeResponse,
)
from plaid.configuration import Configuration
from plaid.api_client import ApiClient

from .models import PlaidAccount

load_dotenv()

PLAID_ENV = os.getenv("PLAID_ENV", "sandbox").lower()
PLAID_HOST = {
    "sandbox": "https://sandbox.plaid.com",
    "development": "https://development.plaid.com",
    "production": "https://production.plaid.com",
}[PLAID_ENV]

configuration = Configuration(
    host=PLAID_HOST,
    api_key={
        "clientId": os.getenv("PLAID_CLIENT_ID"),
        "secret": os.getenv("PLAID_SECRET"),
    },
)

api_client = ApiClient(configuration)
plaid_client = plaid_api.PlaidApi(api_client)


@login_required
def plaid_home(request):
    accounts = PlaidAccount.objects.filter(user=request.user)

    context = {
        'accounts': accounts,
        'has_accounts': accounts.exists(),
    }
    return render(request, "plaidapp/index.html", context)


@login_required
def link_account_page(request):
    return render(request, "plaidapp/link_account.html")


def signup_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("link_account_page")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})


@login_required
def create_link_token(request):
    user_id = str(request.user.id)
    request_body = LinkTokenCreateRequest(
        user=LinkTokenCreateRequestUser(client_user_id=user_id),
        client_name="PartnerTrade",
        products=[Products("transactions")],
        country_codes=[CountryCode("US")],
        language="en",
    )

    response = plaid_client.link_token_create(request_body)
    return JsonResponse(response.to_dict())


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def exchange_public_token(request):
    data = json.loads(request.body)
    public_token = data.get("public_token")

    if not public_token:
        return JsonResponse({'error': 'Missing public_token'}, status=400)

    exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
    exchange_response: ItemPublicTokenExchangeResponse = plaid_client.item_public_token_exchange(exchange_request)

    access_token = exchange_response.access_token
    item_id = exchange_response.item_id

    PlaidAccount.objects.create(
        user=request.user,
        access_token=access_token,
        item_id=item_id
    )

    return JsonResponse({'status': 'linked', 'item_id': item_id})

@login_required
def delete_account(request, account_id):
    account = get_object_or_404(PlaidAccount, id=account_id, user=request.user)
    account.delete()
    return redirect('plaid_home')
