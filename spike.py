import numpy as np
import matplotlib.pyplot as plt
import os
from coinbase.wallet.client import Client
import time
from multiprocessing import Process
import json
import cbpro

current_path = os.path.abspath(os.path.dirname(__file__))
API_file = open(current_path+"/API_key.json")

API_key_dict = json.load(API_file)
client = Client(API_key_dict["key"], API_key_dict["secret"])

currencies = ["BTC", "EOS", "ETH", "ZRX", "XLM", "OMG", "XTZ", "BCH", "LTC", "GRT", "FIL", "ANKR", "COMP"]

# create dictionary containing colors for each coin (for plots)
colors = ["orange", "black", "blue", "grey", "blue", "purple", "green", "darkblue", "red", "lightblue", "pink",
          "darkred", "darkgreen"]
colors = {coin: colors[i] for i, coin in enumerate(currencies)}


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


def update_graphs(currencies: list) -> None:
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


def normalised_price_graph(currencies: list, period: str = "day", filename: str = "trend_graph.png",
                           clear_plot: bool = True, significance_threshold: float = 0.05) -> None:
    """
    saves a plot of the most significant changing currencies on a normalized graph. By default the pyplot is cleared,
    but this can be changed using clear_plot.
    :param currencies: the list of currencies to be graphed.
    :param period: the time period to be graphed.
    :param filename: the filename of the output image.
    :param clear_plot: specifies whether the plot should be cleared. (default = True)
    :param significance_threshold: defines at which point a change becomes significant
    :return: None
    """
    plt.clf()   # clear graph
    plt.grid()  # plot grid

    prices_list = {}
    times_list = {}
    percentage_change = {}

    for coin in currencies:
        times, prices = get_historical(coin, period)
        prices_list.update({coin: prices})
        times_list.update({coin: times})
        percentage_change.update({coin: (prices[-1] - prices[0]) / prices[0]})

    sorted_currencies = (sorted(percentage_change)[::-1])          # sorted in order of decreasing percentage change
    for coin in sorted_currencies[:3] + sorted_currencies[-3:]:    # include first 3 most increasing/decreasing coins.
        percentage_change_graph = 100*(np.array(prices_list[coin]) / prices_list[coin][0] - 1)
        plt.plot(np.linspace(-24, 0, len(prices_list[coin])), percentage_change_graph, label=coin,
                 color = colors[coin])

        # add coin labels to plot
        sign = np.sign(percentage_change[coin])
        if sign >= 0:
            sign = "+"
        else:
            sign = "-"
        plt.text(1.5, percentage_change_graph[-1], sign + "%2.0f%%" % (np.abs(percentage_change[coin]*100)) + " "
                 + coin, color = colors[coin],fontsize=7)
        if not clear_plot:
            plt.pause(0.001)  # the pause statements are required such that an interactive graph updates properly.

    # plot labels etc.
    plt.legend()
    plt.xlabel("Time")
    plt.ylabel("Price Change (%)")

    if not clear_plot:
        plt.pause(0.1)  # the pause statements are required such that an interactive graph updates properly.

    plt.savefig(current_path + "/graphs/" + filename)

    if clear_plot:
        plt.clf()


def thread_price_graph(currencies: list, period: str = "day", filename: str = "trend_graph.png", delay: int = 5*60)\
        -> None:
    """
    displays an interactive price plot which is updated on a periodic basis.
    :param currencies: the currencies to be considered for plotting.
    :param period: the time period to be graphed.
    :param filename: the filename of the output image.
    :param delay: specifies the delay between plot updates.
    :return: None
    """
    plt.ion()   # enable interactive mode (allows for live updating of the plot)
    while True:
        normalised_price_graph(currencies, period, filename, clear_plot = False)
        plt.pause(delay)


def get_price_change(coin: str, period: str = "day") -> float:
    """
    calculates percentage change for a coin over the past hour.
    :param coin: the coin for which the percentage is calculated
    :param period: the period for which the price change is calculated.
    :return: percentage change over the past hour
    """
    times, prices = get_historical(coin)
    diff = prices[-1] - prices[0]
    relative_diff = diff / prices[0]
    return float(relative_diff*100)


def get_account_balance():
    accounts = client.get_accounts()["data"]

    balances = {account["balance"]["currency"]: float(account["balance"]["amount"]) for account in accounts}
    return balances


if __name__ == '__main__':
    # run interactive plot in a separate process
    process = Process(target = thread_price_graph, args = (currencies, ))
    process.start()

    day_threshold = 10
    hour_threshold = 10
    delay = 5*60

    # dictionary containing the previously notified price percentage change, which is used to prevent repeated
    # notifications.
    notified = {coin: 0 for coin in currencies}
    notification_threshold = 5  # threshold for sending a new notification (%)

    while True:
        changes = []                # list containing the percentage price change,
        new_notifications = False   # specifies whether a notification is new or not.

        balances = get_account_balance()

        for coin in currencies:
            change = get_price_change(coin)
            changes.append(change)

            # notify if the price changed significantly today, if this increased by more than the notification_threshold
            # from the previous notification.
            if change > day_threshold and change - notified[coin] > notification_threshold:
                print(" ↑ " + coin + " increased by " + "%.2f" % change + " %")
                notified[coin] = change
                new_notifications = True
            elif change < -day_threshold and change - notified[coin] < notification_threshold:
                print(" ↓ "+coin + " decreased by " + "%.2f" % (-change) + " %")
                notified[coin] = change
                new_notifications = True
            if np.abs(change) < day_threshold < np.abs(notified[coin]):
                if notified[coin] > 0:
                    print("Spike has ended for " + coin + ".")
                elif notified[coin] < 0:
                    print("Dip has ended for " + coin + ".")
                notified[coin] = 0

        if not new_notifications:
            print("No significant changes.")

        current_time = time.strftime("%H:%M:%S", time.localtime())
        print("checked at " + str(current_time), end="\n\n")

        print(client.get_accounts())

        time.sleep(delay)

    # currently won't be executed, but I left it in case we use break statements later.
    process.kill()
