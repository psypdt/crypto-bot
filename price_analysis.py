import numpy as np
import matplotlib.pyplot as plt
import os
from coinbase.wallet.client import Client
import time

current_path = os.path.abspath(os.path.dirname(__file__))
API_file = open(current_path+"/API_key.txt")

key = API_file.readline().strip("\n")
secret = API_file.readline().strip("\n")
print(key)
print(secret)

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


i=1
stop = False
buygraph = {"EOS" : []}
sellgraph = {"EOS" : []}
while not stop:
    buy = float(client.get_buy_price(currency_pair = 'XRP-BTC')["amount"])
    buygraph["EOS"].append(buy)
    sell = float(client.get_sell_price(currency_pair = 'XRP-BTC')["amount"])
    sellgraph["EOS"].append(sell)

    print(buygraph["EOS"])
    print(sellgraph["EOS"])

    time.sleep(20)

