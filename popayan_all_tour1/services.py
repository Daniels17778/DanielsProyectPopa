# services.py
import requests

FAWAZ_URL = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1"
FAWAZ_FALLBACK = "https://currency-api.pages.dev/v1"

CURRENCIES_FALLBACK = {
    "usd": "US Dollar", "eur": "Euro", "cop": "Colombian Peso",
    "gbp": "British Pound", "jpy": "Japanese Yen", "brl": "Brazilian Real",
    "mxn": "Mexican Peso", "ars": "Argentine Peso", "clp": "Chilean Peso",
    "pen": "Peruvian Sol", "cad": "Canadian Dollar", "aud": "Australian Dollar",
    "chf": "Swiss Franc", "cny": "Chinese Yuan", "krw": "South Korean Won",
    "inr": "Indian Rupee", "rub": "Russian Ruble", "try": "Turkish Lira",
    "sek": "Swedish Krona", "nok": "Norwegian Krone",
}

def get_currencies():
    for base in [FAWAZ_URL, FAWAZ_FALLBACK]:
        try:
            res = requests.get(f"{base}/currencies.json", timeout=5)
            res.raise_for_status()
            return dict(sorted(res.json().items()))
        except Exception:
            continue
    return CURRENCIES_FALLBACK

def convert_currency(amount, from_currency, to_currency):
    from_cur = from_currency.lower()
    to_cur = to_currency.lower()
    for base in [FAWAZ_URL, FAWAZ_FALLBACK]:
        try:
            res = requests.get(f"{base}/currencies/{from_cur}.json", timeout=5)
            res.raise_for_status()
            data = res.json()
            rate = data[from_cur][to_cur]
            return round(amount * rate, 2)
        except Exception:
            continue
    raise Exception("No se pudo obtener la tasa de cambio. Intenta más tarde.")