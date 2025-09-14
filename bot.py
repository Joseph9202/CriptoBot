import os
from dotenv import load_dotenv
from binance.spot import Spot  # provisto por binance-sdk-spot
load_dotenv()

API_KEY    = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

# Usa Testnet primero:
client = Spot(api_key=API_KEY, api_secret=API_SECRET,
              base_url="https://testnet.binance.vision")

# Precio actual
print(client.ticker_price("BTCUSDT"))

# Info de filtros del exchange (minQty, minNotional, etc.)
ex_info = client.exchange_info()
print([s for s in ex_info["symbols"] if s["symbol"]=="BTCUSDT"][0])