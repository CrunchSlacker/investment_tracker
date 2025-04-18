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
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.accounts_get_response import AccountsGetResponse
from plaid.model.institutions_get_by_id_request import InstitutionsGetByIdRequest
from plaid.model.investments_holdings_get_request import InvestmentsHoldingsGetRequest
from plaid.model.investments_holdings_get_response import InvestmentsHoldingsGetResponse
from plaid.model.investments_holdings_get_request import InvestmentsHoldingsGetRequest

from .models import PlaidAccount

load_dotenv()

COINBASE_API_KEY = os.getenv("COINBASE_API_KEY")
COINBASE_API_SECRET = os.getenv("COINBASE_API_SECRET")

from coinbase.wallet.client import Client as CoinbaseClient
coinbase_client = CoinbaseClient(COINBASE_API_KEY, COINBASE_API_SECRET)

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


def get_investment_accounts(access_token):
    request = AccountsGetRequest(access_token=access_token)
    response: AccountsGetResponse = plaid_client.accounts_get(request)

    # Filter only investment accounts
    accounts = [
        {
            "name": acct.name,
            "subtype": acct.subtype.value,
            "balance": acct.balances.current,
        }
        for acct in response.accounts
        if acct.type.value == "investment"
    ]

    return accounts


def get_investment_total_value(access_token):
    try:
        holdings_request = InvestmentsHoldingsGetRequest(access_token=access_token)
        holdings_response: InvestmentsHoldingsGetResponse = (
            plaid_client.investments_holdings_get(holdings_request)
        )

        # Map security_id to price
        security_prices = {
            sec.security_id: sec.close_price or 0
            for sec in holdings_response.securities
        }

        total_value = 0.0
        for holding in holdings_response.holdings:
            price = security_prices.get(holding.security_id, 0)
            total_value += (holding.quantity or 0) * price

        return round(total_value, 2)

    except Exception as e:
        print(f"Error fetching holdings: {e}")
        return 0.0


def get_holdings_summary(access_token):
    try:
        request = InvestmentsHoldingsGetRequest(access_token=access_token)
        response = plaid_client.investments_holdings_get(request)

        security_map = {
            sec.security_id: {
                "name": sec.name,
                "ticker": sec.ticker_symbol,
                "price": sec.close_price or 0,
            }
            for sec in response.securities
        }

        total_value = 0
        holding_details = []

        for holding in response.holdings:
            sec_info = security_map.get(holding.security_id, {})
            quantity = holding.quantity or 0
            price = sec_info.get("price", 0)
            value = quantity * price

            total_value += value

            holding_details.append(
                {
                    "name": sec_info.get("name", "Unknown"),
                    "ticker": sec_info.get("ticker", ""),
                    "quantity": quantity,
                    "price": price,
                    "value": value,
                }
            )

        return round(total_value, 2), holding_details

    except Exception as e:
        print(f"Error fetching holdings: {e}")
        return 0, []


##########################################################################


@login_required
def plaid_home(request):
    accounts = PlaidAccount.objects.filter(user=request.user)
    linked_data = []

    for acc in accounts:
        institution_name = "Unknown Institution"
        if acc.institution_id:
            try:
                inst_request = InstitutionsGetByIdRequest(
                    institution_id=acc.institution_id, country_codes=["US"]
                )
                inst_response = plaid_client.institutions_get_by_id(inst_request)
                institution_name = inst_response.institution.name
            except Exception as e:
                print(f"Error fetching institution name: {e}")

        total_value, holdings = get_holdings_summary(acc.access_token)

        linked_data.append(
            {
                "institution_name": institution_name,
                "total_value": total_value,
                "holdings": holdings,
                "account_id": acc.id,
            }
        )

    context = {
        "linked_data": linked_data,
        "has_accounts": len(linked_data) > 0,
    }

    return render(request, "plaidapp/index.html", context)

@login_required
def coinbase_transactions(request):
    try:
        accounts = coinbase_client.get_accounts()
        all_txs = []

        for acct in accounts.data:
            txs = coinbase_client.get_transactions(acct.id)
            for tx in txs.data:
                all_txs.append({
                    "account_name": acct.name,
                    "type": tx.type,
                    "amount": tx.amount.amount,
                    "currency": tx.amount.currency,
                    "native_amount": tx.native_amount.amount,
                    "date": tx.created_at,
                    "status": tx.status,
                    "description": tx.details.get('title', '')
                })

        return render(request, "plaidapp/coinbase.html", {"transactions": all_txs})

    except Exception as e:
        print(f"Coinbase error: {e}")
        return JsonResponse({"error": "Failed to load Coinbase transactions"})


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
        products=[Products("investments")],
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
    institution_id = data.get("institution_id")

    if not public_token:
        return JsonResponse({"error": "Missing public_token"}, status=400)

    exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
    exchange_response = plaid_client.item_public_token_exchange(exchange_request)

    access_token = exchange_response.access_token
    item_id = exchange_response.item_id

    PlaidAccount.objects.create(
        user=request.user,
        access_token=access_token,
        item_id=item_id,
        institution_id=institution_id,
    )

    return JsonResponse({"status": "linked", "item_id": item_id})


@login_required
def delete_account(request, account_id):
    account = get_object_or_404(PlaidAccount, id=account_id, user=request.user)
    account.delete()
    return redirect("plaid_home")
