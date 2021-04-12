from coinbase.wallet.client import Client
import json
import os


class CoinbaseAPI:
    """
    This class wraps the coinbase API in order to provide a more high level interface for coinbase functionality. The
    class is intended to make it easier to market and account specific information from the coinbase API.

    Use this class to authenticate coinbase API access and retrieve raw information related to currencies and profiles.
    """

    def __init__(self, *args):
        """
        Constructor which builds and api wrapper object
        :param args: Can take in a maximum of 2 arguments which are the api key and secret respectively
        """

        # Case when user passes in path to API json file
        if len(args) == 1:
            api_file = open(args[0])  # Open file containing coinbase API keys
            api_key_dict = json.load(api_file)
            key, secret = api_key_dict["key"], api_key_dict["secret"]

        elif len(args) == 2:
            key = args[0]
            secret = args[1]
        else:
            raise Exception("Incorrect input. Should either be path to keys or (key,secret)")

        self.key = key
        self.secret = secret
        self.client = Client(key, secret)

    def get_historical(self, coin: str, period: str = "day") -> (list, list):
        """
        calls get_historical_prices to construct price and time arrays over the given period for the given coin.

        :param coin: coin for which data is fetched
        :param period: period for which data is fetched ("hour","day", "week", "month", "all")
        :return: returns times and price lists respectively
        """
        historic = self.client.get_historic_prices(currency_pair=coin + "-CHF", period=period)

        prices, times = [], []
        for price_dict in historic["prices"]:
            times.append((price_dict["time"]))
            prices.append(float(price_dict["price"]))
        prices.reverse()
        times.reverse()
        return times, prices

    def get_price_change(self, coin: str, period: str = "day") -> float:
        """
        calculates percentage change for a coin over the past hour.

        :param coin: the coin for which the percentage is calculated
        :param period: the period for which the price change is calculated.
        :return: percentage change over the past hour
        """
        times, prices = self.get_historical(coin, period=period)
        diff = prices[-1] - prices[0]
        relative_diff = diff / prices[0]
        return float(relative_diff*100)

    def get_account_balance(self, currencies: list) -> dict:
        """
        Retrieves the balance of a users account

        :param currencies: A list of crypto codes (BTC, XLM, etc.)
        :return: Dictionary of currency, balance pairs
        """
        accounts = []
        for coin in currencies:
            accounts.append(self.client.get_account(coin))

        balances = {account["balance"]["currency"]: float(account["balance"]["amount"]) for account in accounts}
        return balances

    def get_transaction_history(self, coin) -> [(float, str)]:
        """
        Gets all transactions that have been carried out with the given input currency.

        NOTE: When currencies are received the amount is positive, if a coin is traded for another one (BTC -> ZRX)
        then the BTC transaction will be negative

        :param coin: The code for a currency whose historical transactions will be queried (BTC, ZRX, etc.)
        :return: A list of coin_amount, timestamp tuples
        """
        transaction_list = self.client.get_transactions(coin).get('data')
        num_coins_traded = [float(trans["amount"].get("amount")) for trans in transaction_list]
        timestamps = [trans["created_at"] for trans in transaction_list]

        return list(zip(num_coins_traded, timestamps))

    def get_historic_exchange_rate(self, from_currency: str, to_currency: str, timestamp: str) -> float:
        """
        Used to get an exchange rate between 2 currencies at a given timestamp

        NOTE: To get the price of 1 BTC in CHF we would do get_historic_exchange_rate(BTC, CHF, time)

        :param from_currency: The currency which we want to convert
        :param to_currency: The currency which will express from_currency
        :param timestamp: The timestamp in the format YYYY-MM-DDTHH:MM:SSZ where T & Z must be included
        :return: The value of 1 from_currency expressed as to_currency at a given timestamp
        """
        rates = self.client.get_exchange_rates(currency=from_currency, date=timestamp)["rates"]
        return float(rates[to_currency])


if __name__ == '__main__':
    current_path = os.path.abspath(os.path.dirname(__file__))
    current_path = "/".join(current_path.split("/")[:-2])
    file_path = current_path + "/credentials/API_key.json"

    api = CoinbaseAPI(file_path)
    ret = api.get_transaction_history("BTC")
    print(api.get_historic_exchange_rate("BTC", "CHF", ret[0][1]))


