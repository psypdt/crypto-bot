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


def get_price_change(coin : str) -> float:
    """
    calculates percentage change for a coin over the past hour.
    :param coin: the coin for which the percentage is calculated
    :return: percentage change over the past hour
    """
    times, prices = get_historical(coin)
    diff = prices[-1] - prices[0]
    relative_diff =  diff / prices[0]
    return float(relative_diff)


def get_trend(coin, threshold):
    """
    checks if the difference falls within a threshold for increasing and decreasing price.
    :param coin: coin that will be checked.
    :param threshold: percentage change that defines a spike.
    :return: 1, 0 or -1 if increasing, stagnant or decreasing respectively.
    """
    if get_price_change(coin) >= threshold:
        return 1
    if get_price_change(coin) <= threshold:
        return -1
    return 0


if __name__ == '__main__':
    while True:
        changes = []
        for coin in currencies:
            change = get_price_change(coin)
            changes.append(change)
            print(coin + " : " + "%.2f" % (change*100) )
        time.sleep(5*60)
