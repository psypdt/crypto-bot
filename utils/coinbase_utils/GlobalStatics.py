import sys

CURRENCIES = ["BTC", "EOS", "ETH", "ZRX", "XLM", "OMG", "XTZ", "BCH", "LTC", "GRT", "FIL", "ANKR", "COMP"]
COLORS = ["orange", "lightyellow", "blue", "grey", "blue", "purple", "green", "darkblue", "red", "lightblue", "pink",
          "darkred", "darkgreen"]
COLORS = {coin: COLORS[i] for i, coin in enumerate(CURRENCIES)}

PATH_DELIM = "/"
if sys.platform == "win32":
    PATH_DELIM = "\\"
