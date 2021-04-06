from coinbase.wallet.client import Client


class API_wrapper:
    def __init__(self, key, secret):
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
        historic = self.client.get_historic_prices(currency_pair = coin + "-CHF", period = period)

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
        times, prices = self.get_historical(coin)
        diff = prices[-1] - prices[0]
        relative_diff = diff / prices[0]
        return float(relative_diff*100)


    def get_account_balance(self, currencies: list):
        accounts = []
        for coin in currencies:
            accounts.append(self.client.get_account(coin))

        balances = {account["balance"]["currency"]: float(account["balance"]["amount"]) for account in accounts}
        return balances

