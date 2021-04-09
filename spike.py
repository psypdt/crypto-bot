from utils.coinbase_utils import CoinbaseAPI as cbapi
import utils.coinbase_utils.GlobalStatics as statics
import numpy as np
import time
import os


class Spike:
    def __init__(self, currencies: list, coinbase_api: cbapi.CoinbaseAPI, notification_threshold: float,
                 day_threshold: float = 0, week_threshold: float = 0.):
        """
        :param currencies: List of crypto currency identifiers (BTC, XRP, etc.)
        :param notification_threshold: Amount in (%) needed for another notification to be sent for a coin
        :param day_threshold: Minimum (%) change over an entire day needed to trigger a notification
        :param week_threshold: Minimum (%) change over a week needed to trigger a notification
        :param coinbase_api: Coinbase API object to fetch data for crypto currencies
        """
        self.currencies = currencies
        self.notification_threshold = notification_threshold  # threshold for sending a new notification (%)
        self.day_threshold = day_threshold
        self.week_threshold = week_threshold
        self.coinbase_api = coinbase_api

        # dictionary containing the previously notified price percentage change, used to prevent repeated notifications.
        self.notified = {coin: 0 for coin in statics.CURRENCIES}

    def __generate_alert_string(self, coin: str, percentage_change: float, period: str):
        alert_string = ""
        if percentage_change >= 0:
            if period == "week":
                alert_string = "+" + "%2.2f" % percentage_change + " " + coin + " this week"

        return alert_string

    def __generate_alert(self, coin: str, period: str) -> (float, str):
        """
        Generates a tuple containing the percentage change and alert message.

        :param coin: The coin for which the alert message is to be generated.
        :param period: The period for which the percentage change should be considered
        :return: A tuple containing the percentage change and alert message.
        """
        alert_tuple = None
        percentage_change = self.coinbase_api.get_price_change(coin, period=period)
        threshold = 10

        if period == "week":
            threshold = self.week_threshold
        elif period == "day":
            threshold = self.day_threshold

        # notify if the price changed significantly today, if this increased by more than the notification_threshold
        # from the previous notification.
        if np.abs(percentage_change) > threshold and np.abs(percentage_change - self.notified[coin]) > \
            self.notification_threshold:
            alert_tuple = (percentage_change, self.__generate_alert_string(coin, percentage_change, period))

        # if percentage_change > threshold and percentage_change - self.notified[coin] > \
        #         self.notification_threshold:
        #     alert_tuple = (percentage_change,
        #                     "↑ " + coin + " increased by " + "%.2f" % percentage_change + " %")
        #
        #     self.notified[coin] = percentage_change
        #
        # elif percentage_change < -threshold and percentage_change - self.notified[coin] < \
        #         -self.notification_threshold:
        #     alert_tuple = (percentage_change,
        #              "↓ " + coin + " decreased by " + "%.2f" % (-percentage_change) + " %")
        #
        #    self.notified[coin] = percentage_change

        return alert_tuple

    def get_spike_alerts(self, is_console=False) -> [(float, str)]:
        """
        Queries the coinbase API to get updates on significant changes in currencies

        :param is_console: Flag set for console usage vs Telegram Bot usage to get time readout
        :return: A list of tuples where the key is percentage change & value is the entire message string
        """
        message = list()

        for coin in statics.CURRENCIES:
            alert_tuple = self.__generate_alert(coin, period = "week")
            if alert_tuple:
                message.append(alert_tuple)

        message.sort(key=lambda tup: tup[0], reverse=True)
        message = [value for key, value in message]

        if is_console:
            current_time = time.strftime("%H:%M:%S", time.localtime())
            time_stamp = "checked at " + str(current_time) + "\n\n"
            message.append(time_stamp)

        return message


if __name__ == '__main__':
    current_path = os.path.abspath(os.path.dirname(__file__))
    api_file = str(current_path + "/credentials/API_key.json")
    cb_api = cbapi.CoinbaseAPI(api_file)
    spike = Spike(statics.CURRENCIES, coinbase_api=cb_api, day_threshold=1, week_threshold=1,
                  notification_threshold=5)

    delay = 5*60

    while True:
        results = spike.get_spike_alerts(is_console=True)
        for result in results:
            print(result)
        time.sleep(delay)
