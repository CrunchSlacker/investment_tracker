import os
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.conf import settings

from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from plaid.model.country_code import CountryCode
from plaid.model.products import Products
from plaid import Configuration, ApiClient, Environment

# Map environment string to Plaid enum
env = {"sandbox": Environment.Sandbox, "production": Environment.Production}
plaid_env = env[settings.PLAID_ENV]

# Set up Plaid configuration and client
configuration = Configuration(
    host=plaid_env,
    api_key={
        "clientId": settings.PLAID_CLIENT_ID,
        "secret": settings.PLAID_SECRET,
    },
)
api_client = ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)


def home(request):
    return render(request, "plaidapp/index.html")


def create_link_token(request):
    user_id = str(request.user.id) if request.user.is_authenticated else "anonymous"

    request_body = LinkTokenCreateRequest(
        user=LinkTokenCreateRequestUser(client_user_id=user_id),
        client_name="PartnerTrade",
        products=[Products("transactions")],
        country_codes=[CountryCode("US")],
        language="en",
    )

    response = client.link_token_create(request_body)
    print(response)
    return JsonResponse(response.to_dict())


@csrf_exempt
def exchange_public_token(request):
    data = json.loads(request.body)
    public_token = data.get("public_token")

    exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
    exchange_response = client.item_public_token_exchange(exchange_request)

    access_token = exchange_response["access_token"]

    # Save this token in your DB securely for later use (not shown here)
    return JsonResponse({"access_token": access_token})
