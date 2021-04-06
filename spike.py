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

currencies = ["BTC", "EOS", "ETH", "ZRX", "XLM", "OMG", "XTZ", "BCH", "LTC", "GRT", "FIL", "ANKR", "COMP"]


def get_historical(coin: str, period: str = "day") -> (list, list):
    """
    calls get_historical_prices to construct price and time arrays over the given period for the given coin.
    :param coin: coin for which data is fetched
    :param period: period for which data is fetched ("hour","day", "week", "month", "all")
    :return: returns times and price lists respectively
    """
    historic = client.get_historic_prices(currency_pair = coin + "-CHF", period = period)

    prices, times = [], []
    for price_dict in historic["prices"]:
        times.append((price_dict["time"]))
        prices.append(float(price_dict["price"]))
    prices.reverse()
    times.reverse()
    return times, prices


def update_graphs(currencies : list) -> None:
    """
    saves graphs of prices for each coin in currencies list with respect to CHF.
    :param currencies: list containing coin strings.
    :return: None
    """
    for coin in currencies:
        times, prices = get_historical(coin)

        plt.plot(np.array(range(len(prices))) - len(prices), prices)
        plt.xlabel("Time (min)")
        plt.ylabel(coin + " price (CHF)")

        plt.savefig(current_path + "/graphs/hourprices_" + coin + ".png")
        plt.close()


def get_price_change(coin : str, period: str = "day") -> float:
    """
    calculates percentage change for a coin over the past hour.
    :param coin: the coin for which the percentage is calculated
    :param period: the period for which the price change is calculated.
    :return: percentage change over the past hour
    """
    times, prices = get_historical(coin)
    diff = prices[-1] - prices[0]
    relative_diff =  diff / prices[0]
    return float(relative_diff)


if __name__ == '__main__':
    day_threshold = 10
    hour_threshold = 10
    while True:
        changes = []
        for coin in currencies:
            change = get_price_change(coin)
            changes.append(change)
            #print(coin + " : " + "%.2f" % (change*100))

            if change*100 > day_threshold:
                print(coin + " increased by " + "%.2f"%(change*100) + " %")
            elif change*100 < -day_threshold:
                print(coin + " decreased by " + "%.2f"%(-change*100) + " %")
        time.sleep(5*60)
