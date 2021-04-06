import numpy as np
import matplotlib.pyplot as plt
from utils import API_wrapper as wpr
import os
import json


class Graphs:
    def __init__(self, wrapper, currencies, colors, current_path = None):
        self.wrapper = wrapper
        self.currencies = currencies
        self.colors = colors
        self.current_path = current_path

        if not self.current_path:
            self.current_path = os.path.abspath(os.path.dirname(__file__)) + "/.."

    def update_graphs(self, current_path: str = None) -> None:
        """
        saves graphs of prices for each coin in currencies list with respect to CHF.
        :param current_path: path to save graphs
        :return: None
        """
        if not current_path:
            current_path = self.current_path

        for coin in self.currencies:
            times, prices = self.wrapper.get_historical(coin)

            plt.plot(np.array(range(len(prices))) - len(prices), prices)
            plt.xlabel("Time (min)")
            plt.ylabel(coin + " price (CHF)")

            plt.savefig(current_path + "/graphs/hourprices_" + coin + ".png")
            plt.close()

    def normalised_price_graph(self, period: str = "day", filename: str = "trend_graph.png",
                               clear_plot: bool = True, current_path = None) -> None:
        """
        saves a plot of the most significant changing currencies on a normalized graph. By default the pyplot is cleared,
        but this can be changed using clear_plot.
        :param period: the time period to be graphed.
        :param filename: the filename of the output image.
        :param clear_plot: specifies whether the plot should be cleared. (default = True)
        :param current_path: alternate path to save graphs
        :return: None
        """
        if not current_path:
            current_path = self.current_path

        plt.clf()   # clear graph
        plt.grid()  # plot grid

        prices_list = {}
        times_list = {}
        percentage_change = {}

        for coin in self.currencies:
            times, prices = self.wrapper.get_historical(coin, period)
            prices_list.update({coin: prices})
            times_list.update({coin: times})
            percentage_change.update({coin: (prices[-1] - prices[0]) / prices[0]})

        sorted_currencies = (sorted(percentage_change)[::-1])          # sorted in order of decreasing percentage change
        for coin in sorted_currencies[:2] + sorted_currencies[-2:]:    # include first 3 most increasing/decreasing coins.
            percentage_change_graph = 100*(np.array(prices_list[coin]) / prices_list[coin][0] - 1)
            plt.plot(np.linspace(-24, 0, len(prices_list[coin])), percentage_change_graph, label=coin,
                     color = self.colors[coin])

            # add coin labels to plot
            sign = np.sign(percentage_change[coin])
            if sign >= 0:
                sign = "+"
            else:
                sign = "-"
            plt.text(1.5, percentage_change_graph[-1], sign + "%2.0f%%" % (np.abs(percentage_change[coin]*100)) + " "
                     + coin, color = self.colors[coin], fontsize=7)
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

    def thread_price_graph(self, period: str = "day", filename: str = "trend_graph.png", delay: int = 5*60)\
            -> None:
        """
        displays an interactive price plot which is updated on a periodic basis.
        :param period: the time period to be graphed.
        :param filename: the filename of the output image.
        :param delay: specifies the delay between plot updates.
        :return: None
        """
        plt.ion()   # enable interactive mode (allows for live updating of the plot)
        while True:
            self.normalised_price_graph(period, filename, clear_plot = False)
            plt.pause(delay)


if __name__ == "__main__":
    current_path = os.path.abspath(os.path.dirname(__file__)) + "/.."
    API_FILE = open(current_path + "/API_key.json")

    API_KEY_DICT = json.load(API_FILE)
    wrapper = wpr.API_wrapper(API_KEY_DICT["key"], API_KEY_DICT["secret"])

    CURRENCIES = ["BTC", "EOS", "ETH", "ZRX", "XLM", "OMG", "XTZ", "BCH", "LTC", "GRT", "FIL", "ANKR", "COMP"]

    # create dictionary containing colors for each coin (for plots)
    COLORS = ["orange", "black", "blue", "grey", "blue", "purple", "green", "darkblue", "red", "lightblue", "pink",
              "darkred", "darkgreen"]
    COLORS = {coin: COLORS[i] for i, coin in enumerate(CURRENCIES)}

    graph = Graphs(wrapper, CURRENCIES, COLORS)
    graph.thread_price_graph()
