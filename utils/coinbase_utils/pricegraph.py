import numpy as np
import matplotlib.pyplot as plt
from utils.coinbase_utils import CoinbaseAPI as wpr
import os
import json


class Graphs:
    def __init__(self, wrapper, currencies, colors, current_path=None, graph_directory_name="graphs"):
        self.wrapper = wrapper
        self.currencies = currencies
        self.colors = colors
        self.current_path = current_path
        self.graph_directory_name = "/" + graph_directory_name + "/"

        if not self.current_path:
            self.current_path = os.path.abspath(os.path.dirname(__file__))
            self.current_path = "/".join(self.current_path.split("/")[:-2])

    def save_figure(self, file_name: str, figure: plt.Figure) -> None:
        """
        Saves a plt figure into the directory specified in the constructor

        :param file_name: Name of the file (including type, .png, .jpg, etc)
        :param figure: plt Figure object
        """

        if not os.path.exists(self.current_path + self.graph_directory_name):
            os.mkdir(self.current_path + self.graph_directory_name)
        figure.savefig(self.current_path + self.graph_directory_name + file_name)

    def save_individual_graphs(self, current_path: str = None) -> None:
        """
        saves graphs of prices for each coin in currencies list with respect to CHF.

        :param current_path: path to save graphs
        """

        for coin in self.currencies:
            times, prices = self.wrapper.get_historical(coin)

            plt.plot(np.array(range(len(prices))) - len(prices), prices)
            plt.xlabel("Time (min)")
            plt.ylabel(coin + " price (CHF)")

            plot = plt.get_current_fig_manager()
            self.save_figure("hourprices_" + coin + ".png", plot)

            plt.close()

    def _plot_percentage_change(self, prices_list, coin, percentage_change, clear_plot, sign) -> None:
        percentage_change_graph = 100 * (np.array(prices_list[coin]) / prices_list[coin][0] - 1)
        plt.plot(np.linspace(-24, 0, len(prices_list[coin])), percentage_change_graph, label=coin,
                 color=self.colors[coin])

        # add coin labels to plot
        plt.text(1.5, percentage_change_graph[-1], sign + "%.0f%%" % (np.abs(percentage_change[coin] * 100)) + " "
                 + coin, color=self.colors[coin], fontsize=10)
        if not clear_plot:
            plt.pause(0.001)  # the pause statements are required such that an interactive graph updates properly.

    def normalised_price_graph(self, fig: plt.Figure, period: str = "day", filename: str = "trend_graph.png",
                               clear_plot: bool = True) -> None:
        """
        saves a plot of the most significant changing currencies on a normalized graph. By default the pyplot is cleared,
        but this can be changed using clear_plot.

        :param period: the time period to be graphed.
        :param filename: the filename of the output image.
        :param fig: figure to plot to
        :param clear_plot: specifies whether the plot should be cleared. (default = True)
        :return: None
        """

        plt.clf()

        prices_list = {}
        times_list = {}
        percentage_change = {}

        for coin in self.currencies:
            times, prices = self.wrapper.get_historical(coin, period)
            prices_list.update({coin: prices})
            times_list.update({coin: times})
            percentage_change.update({coin: (prices[-1] - prices[0]) / prices[0]})

        # sorted in order of decreasing percentage change
        sorted_currencies = (sorted(percentage_change.keys(), key=lambda x: percentage_change[x], reverse=True))
        plt.style.use('dark_background')

        fig.add_subplot(2, 1, 1)
        plt.plot([-25, 1], [0, 0], linestyle="--", color="black", linewidth=1.5)

        plt.title("Increasing Currencies")
        for coin in sorted_currencies[:3]:  # include first 3 most increasing coins.
            if percentage_change[coin] < 0:
                continue
            self._plot_percentage_change(prices_list, coin, percentage_change, clear_plot, "+")

        # plot labels etc.
        plt.xlim(-25, 1)
        plt.grid()
        if percentage_change[sorted_currencies[0]] < 0.:
            plt.text(-12, 0, "It's a bad day for crypto.", ha="center", va="center", fontsize=25, color="darkred")
        else:
            plt.legend()
        plt.xlabel("Time")
        plt.ylabel("Price Change (%)")
        fig.add_subplot(2, 1, 2)
        plt.plot([-25, 1], [0, 0], linestyle = "--", color = "black", linewidth = 1.5)

        always_show_threshold = 10/100
        plt.title("Decreasing Currencies")
        for coin in sorted_currencies[-3:]:  # include first 3 most increasing coins.
            if percentage_change[coin] > 0:
                continue
            self._plot_percentage_change(prices_list, coin, percentage_change, clear_plot, "-")
        for coin in sorted_currencies[3:-3]:
            if percentage_change[coin] >= always_show_threshold:
                self._plot_percentage_change(prices_list, coin, percentage_change, clear_plot, "+")
            if percentage_change[coin] <= -always_show_threshold:
                self._plot_percentage_change(prices_list, coin, percentage_change, clear_plot, "-")
        # plot labels etc.
        plt.xlim(-25, 1)
        plt.grid()
        if percentage_change[sorted_currencies[-1]] > 0.:
            plt.text(-12, 0, "It's a good day for crypto!", ha="center", va="center", fontsize=25, color="green")
        else:
            plt.legend()
        plt.xlabel("Time")
        plt.ylabel("Price Change (%)")

        if not clear_plot:
            plt.pause(0.1)  # the pause statements are required such that an interactive graph updates properly.

        self.save_figure(filename, fig)

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
        fig = plt.figure(figsize=(9,16), facecolor="black")

        while True:
            self.normalised_price_graph(fig, period, filename, clear_plot=False)
            plt.pause(delay)


if __name__ == "__main__":
    CURRENT_PATH = os.path.abspath(os.path.dirname(__file__))
    CURRENT_PATH = "/".join(CURRENT_PATH.split("/")[:-2])
    API_FILE = open(CURRENT_PATH + "/credentials/API_key.json")

    API_KEY_DICT = json.load(API_FILE)
    WRAPPER = wpr.CoinbaseAPI(API_KEY_DICT["key"], API_KEY_DICT["secret"])

    CURRENCIES = ["BTC", "EOS", "ETH", "ZRX", "XLM", "OMG", "XTZ", "BCH", "LTC", "GRT", "FIL", "ANKR", "COMP"]

    # create dictionary containing colors for each coin (for plots)
    COLORS = ["orange", "lightyellow", "blue", "grey", "blue", "purple", "green", "darkblue", "red", "lightblue", "pink",
              "darkred", "darkgreen"]
    COLORS = {coin: COLORS[i] for i, coin in enumerate(CURRENCIES)}
    
    graph = Graphs(WRAPPER, CURRENCIES, COLORS)
    graph.thread_price_graph()
