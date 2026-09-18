import requests as r
import os
import time
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

def increment_payment(non_returns: list, headers:str):
    for value in non_returns:
        post_intent_response = r.post(f"https://api.stripe.com/v1/payment_intents/{value}/increment_authorization",
            headers=headers,
            data={"amount": 5000, "description": "Charger not returned - non-return fee applied"},
            timeout=30
            )
        try:
            post_intent_response.raise_for_status() 
        except r.exceptions.HTTPError:
            raise RuntimeError(post_intent_response.json())
        
        return post_intent_response.json()

def filter_payments(json_response: list):
    non_returns = []

    for value in json_response:
        if time.time() - value.get("created") > 16200 and value.get("status") == "requires_capture":
            non_returns.append(value.get("id"))
        else:
            print(f"No values to increment, {value.get('id')}")

    return non_returns
          

def fetch_payments(headers: str, time_cut: dict):
        params = {
        "limit": 100,
        "created[gte]": time_cut}

        response = r.get("https://api.stripe.com/v1/payment_intents",
              headers=headers,
              params=params,
              timeout=30)
        try:
            response.raise_for_status()
        except:
             raise RuntimeError(response.json())

        parsed_response = response.json().get("data")

        return filter_payments(parsed_response)


def main():
    one_day_ago = int(
            (datetime.now(timezone.utc) - timedelta(days=1)).timestamp())
    key = os.getenv("PROD_KEY")
    headers = {
         "Authorization": f"Bearer {key}"
    }
    if not key:
        raise RuntimeError("Missing API key env variable")

    non_returns = fetch_payments(headers, one_day_ago)

    increment_payment(non_returns, headers)

if __name__ == "__main__":
    main()