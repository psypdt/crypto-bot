import numpy as np
import matplotlib.pyplot as plt
import os
from coinbase.wallet.client import Client
import time

current_path = os.path.abspath(os.path.dirname(__file__))
API_file = open(current_path+"/API_key.txt")

key = API_file.readline().strip("\n")
secret = API_file.readline().strip("\n")

client = Client(key, secret)



times = []
hprice = []

'''
h = client.get_historic_prices(currency_pair = "BTC-CHF",)

for h1 in h["prices"]:
    hprice.append(h1["price"])
    times.append(h1["time"])
buygraph = np.array(hprice).astype(float)[::-1]*1.005
sellgraph = np.array(hprice).astype(float)[::-1]*0.995
print(buygraph)
times = np.array(times)[::-1]
'''

'''
for h1 in h["prices"]:
    hprice.append(h1["price"])
    times.append(h1["time"])
buygraph = np.array(hprice).astype(float)[::-1]*1.005
sellgraph = np.array(hprice).astype(float)[::-1]*0.995
print(buygraph)
times = np.array(times)[::-1]
'''








'''
EOS_BTC = []
while True:
    EOS_rates = client.get_exchange_rates(currency="EOS")
    EOS_BTC.append(EOS_rates.get("rates")["BTC"])

    time.sleep(20)



while True:
    buy = float(client.get_buy_price(currency_pair = 'XRP-BTC')["amount"])
    buygraph["EOS"].append(buy)
    sell = float(client.get_sell_price(currency_pair = 'XRP-BTC')["amount"])
    sellgraph["EOS"].append(sell)

    print(buygraph["EOS"])
    print(sellgraph["EOS"])

    time.sleep(20)'''

