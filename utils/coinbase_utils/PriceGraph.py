import numpy as np
import matplotlib.pyplot as plt
from utils.coinbase_utils import CoinbaseAPI as cbapi
from utils.coinbase_utils import GlobalStatics
from PIL import Image
import warnings
import os
import io
import json

warnings.filterwarnings( "ignore", module = "matplotlib\..*")
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib\..*")


class PriceGraph:
    def __init__(self, coinbase_api: cbapi.CoinbaseAPI, currencies: list = GlobalStatics.CURRENCIES,
                 colors: dict = GlobalStatics.COLORS, graph_directory_name: str = "graphs",
                 screen_size: (float, float) = (6, 10), color_style: str = "dark_background",
                 base_path=os.path.abspath(os.path.dirname(__file__))):
        """
        Constructor which initializes a Graphs object

        :param coinbase_api: CoinbaseAPI object used to access data for graphs
        :param currencies: Currencies which will be displayed
        :param colors: Colors corresponding to currencies array
        :param graph_directory_name: Name of directory where graphs are saved
        :param screen_size: Size of screen for which graphs are exported and shown
        :param color_style: Style of graph background
        :param base_path: The path from where the this class is being run from
        """
        self.coinbase_api = coinbase_api
        self.currencies = currencies
        self.colors = colors
        self.current_path = base_path
        self.graph_directory_name = "/" + graph_directory_name + "/"
        self.figure = plt.figure(figsize=screen_size, facecolor="black")

        plt.style.use(color_style)  # set style for all graphs

        if not self.currencies:
            self.currencies = GlobalStatics.CURRENCIES

    def save_figure(self, file_name: str, figure: plt.Figure) -> None:
        """
        Saves a plt figure into the directory specified in the constructor

        :param file_name: Name of the file (including type, .png, .jpg, etc)
        :param figure: plt Figure object
        """

        if not os.path.exists(self.current_path + self.graph_directory_name):
            os.mkdir(self.current_path + self.graph_directory_name)
        figure.savefig(self.current_path + self.graph_directory_name + file_name)

    @staticmethod
    def convert_figure_to_pil_image(figure: plt.Figure) -> Image:
        """
        Saves a plt.Figure object into bytes so it doesn't have to be saved to disk
        :param figure: Pyplot figure which will be converted to bytes
        :return: A PIL Image which can be used later on
        """

        # Convert figure to PIL Image
        pil_image = Image.frombytes('RGB', figure.canvas.get_width_height(), figure.canvas.tostring_rgb())

        return pil_image

    def save_individual_graphs(self) -> None:
        """
        saves graphs of prices for each coin in currencies list with respect to CHF.
        """

        for coin in self.currencies:
            times, prices = self.coinbase_api.get_historical(coin)

            plt.plot(np.array(range(len(prices))) - len(prices), prices)
            plt.xlabel("Time (min)")
            plt.ylabel(coin + " price (CHF)")

            plot = plt.get_current_fig_manager()
            self.save_figure("hourprices_" + coin + ".png", plot)

            plt.close()

    def __plot_percentage_change(self, prices_dict: dict, coin: str, percentage_changes: dict,
                                 is_interactive: bool, sign: str) -> None:
        """
        Plots percentage change graphs and annotates graph with percentage changes for a specified currency

        :param prices_dict: Dictionary which contains the arrays of prices (for each currency) over 24 hours
        :param coin: Coin which will be graphed
        :param percentage_changes: Dictionary of percentage changes for each currency
        :param is_interactive: Flag which activates pause statements to update graphs properly in interactive mode
        :param sign: Sign corresponding to the percentage change (increase or decrease)
        """
        period = -7  # -24 for days and -7 for week
        percentage_change_graph = 100 * (np.array(prices_dict[coin]) / prices_dict[coin][0] - 1)
        plt.plot(np.linspace(period, 0, len(prices_dict[coin])), percentage_change_graph, label=coin,
                 color=self.colors[coin])

        # add coin labels to plot
        plt.text(0.5, percentage_change_graph[-1], sign + "%.0f%%" % (np.abs(percentage_changes[coin] * 100)) + " "
                 + coin, color=self.colors[coin], fontsize=10)
        if is_interactive:
            plt.pause(0.001)  # the pause statements are required such that an interactive graph updates properly.

    def normalised_price_graph(self, period: str = "day", filename: str = "trend_graph.png",
                               is_interactive: bool = True, get_pil_image: bool = False) -> Image:
        """
        Saves a plot of the most significant changing currencies on a normalized graph. If interactive mode is active,
        then the plot is also shown

        :param period: The time period to be graphed.
        :param filename: The filename of the output image.
        :param is_interactive: Specifies whether the plot is in interactive mode. (default = True)
        :param get_pil_image: Flag which will return None if False or PIL.Image if True
        """
        ret = None
        plt.clf()

        prices_dict = {}
        times_dict = {}
        percentage_change_dict = {}

        # Create dict of prices for each currency
        for coin in self.currencies:
            times, prices = self.coinbase_api.get_historical(coin, period)
            prices_dict.update({coin: prices})
            times_dict.update({coin: times})
            percentage_change_dict.update({coin: (prices[-1] - prices[0]) / prices[0]})

        # sorted in order of decreasing percentage change
        sorted_currencies = (sorted(percentage_change_dict.keys(), key=lambda x: percentage_change_dict[x], reverse=True))

        self.figure.add_subplot(2, 1, 1)

        period_spacing = -8
        plt.plot([period_spacing, 1], [0, 0], linestyle="--", color="black", linewidth=1.5)

        plt.title("Increasing Currencies")
        for coin in sorted_currencies[:3]:  # include first 3 most increasing coins.
            if percentage_change_dict[coin] < 0:
                continue
            self.__plot_percentage_change(prices_dict, coin, percentage_change_dict, is_interactive, "+")

        # plot labels etc.
        plt.xlim(period_spacing, 1)
        plt.grid()

        if percentage_change_dict[sorted_currencies[0]] < 0.:
            plt.text(-12, 0, "It's a bad day for crypto.", ha="center", va="center", fontsize=25, color="darkred")
        else:
            plt.legend()

        plt.xlabel("Time")
        plt.ylabel("Price Change (%)")
        self.figure.add_subplot(2, 1, 2)
        plt.plot([period_spacing, 1], [0, 0], linestyle="--", color="black", linewidth=1.5)

        always_show_threshold = 10/100
        plt.title("Decreasing Currencies")

        for coin in sorted_currencies[-3:]:  # include first 3 most increasing coins.
            if percentage_change_dict[coin] > 0:
                continue
            self.__plot_percentage_change(prices_dict, coin, percentage_change_dict, is_interactive, "-")

        for coin in sorted_currencies[3:-3]:
            if percentage_change_dict[coin] >= always_show_threshold:
                self.__plot_percentage_change(prices_dict, coin, percentage_change_dict, is_interactive, "+")
            if percentage_change_dict[coin] <= -always_show_threshold:
                self.__plot_percentage_change(prices_dict, coin, percentage_change_dict, is_interactive, "-")

        # plot labels etc.
        plt.xlim(period_spacing, 1)
        plt.grid()

        if percentage_change_dict[sorted_currencies[-1]] > 0.:
            plt.text(-12, 0, "It's a good day for crypto!", ha="center", va="center", fontsize=25, color="green")
        else:
            plt.legend()

        plt.xlabel("Time")
        plt.ylabel("Price Change (%)")

        if is_interactive:
            plt.pause(0.1)  # the pause statements are required such that an interactive graph updates properly.

        self.save_figure(filename, self.figure)

        if get_pil_image:
            ret = self.convert_figure_to_pil_image(self.figure)

        if is_interactive:
            plt.clf()

        return ret

    def display_live_plot(self, period: str = "day", filename: str = "trend_graph.png", delay: int = 5 * 60)\
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
            self.normalised_price_graph(period, filename, is_interactive=False)
            plt.pause(delay)


if __name__ == "__main__":
    current_path = os.path.abspath(os.path.dirname(__file__))
    current_path = "/".join(current_path.split("/")[:-2])
    api_file = open(current_path + "/credentials/API_key.json")

    api_key_dict = json.load(api_file)
    coinbase_api = cbapi.CoinbaseAPI(api_key_dict["key"], api_key_dict["secret"])

    CURRENCIES = ["BTC", "EOS", "ETH", "ZRX", "XLM", "OMG", "XTZ", "BCH", "LTC", "GRT", "FIL", "ANKR", "COMP"]

    # create dictionary containing colors for each coin (for plots)
    COLORS = ["orange", "lightyellow", "blue", "grey", "blue", "purple", "green", "darkblue", "red", "lightblue", "pink",
              "darkred", "darkgreen"]
    COLORS = {coin: COLORS[i] for i, coin in enumerate(CURRENCIES)}
    
    graph = PriceGraph(coinbase_api, CURRENCIES, COLORS, screen_size=(8, 8), base_path=current_path)
    graph.display_live_plot()
