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
        coin_string = coin
        if len(coin) == 3:
            coin_string = coin_string + " "
        if percentage_change >= 0:
            if period == "week":
                alert_string = "↑ " + coin_string + " {:5.1f}".format(percentage_change) + "%" + " in the past week"
            elif period == "day":
                alert_string = "↑ " + coin_string + " {:5.1f}".format(percentage_change) + "%" + " in the past day"
        elif percentage_change < 0:
            if period == "week":
                alert_string = "↓ " + coin_string + " {:5.1f}".format(-percentage_change) + "%" + " in the past week"
            elif period == "day":
                alert_string = "↓ " + coin_string + " {:5.1f}".format(-percentage_change) + "%" + " in the past day"
        return alert_string

    def __generate_alert(self, coin: str, period: str, ignore_previous: bool = False) -> (float, str):
        """
        Generates a tuple containing the percentage change and alert message.

        :param coin: The coin for which the alert message is to be generated.
        :param period: The period for which the percentage change should be considered
        :param ignore_previous: Flag that denotes that messages should be sent regardless of notification_threshold.
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
        if np.abs(percentage_change) > threshold \
                and (ignore_previous or np.abs(percentage_change - self.notified[coin]) > self.notification_threshold):
            alert_tuple = (percentage_change, self.__generate_alert_string(coin, percentage_change, period))
            self.notified[coin] = percentage_change
        return alert_tuple

    def get_spike_alerts(self, is_console=False, ignore_previous = False) -> [(float, str)]:
        """
        Queries the coinbase API to get updates on significant changes in currencies

        :param is_console: Flag set for console usage vs Telegram Bot usage to get time readout
        :param ignore_previous: Flag that denotes that messages should be sent regardless of notification_threshold.
        :return: A list of tuples where the key is percentage change & value is the entire message string
        """
        day_message = list()
        week_message = list()

        for coin in statics.CURRENCIES:
            week_alert_tuple = self.__generate_alert(coin, period = "week",ignore_previous=ignore_previous)
            if week_alert_tuple:
                week_message.append(week_alert_tuple)

            day_alert_tuple = self.__generate_alert(coin, period="day", ignore_previous=ignore_previous)
            if day_alert_tuple:
                day_message.append(day_alert_tuple)

        week_message.sort(key=lambda tup: tup[0], reverse=True)
        week_message = [value for key, value in week_message]

        day_message.sort(key=lambda tup: tup[0], reverse=True)
        day_message = [value for key, value in day_message]

        if is_console:
            current_time = time.strftime("%H:%M:%S", time.localtime())
            time_stamp = "checked at " + str(current_time) + "\n\n"
            week_message.append(time_stamp)
        print(day_message, week_message)
        return day_message + week_message


if __name__ == '__main__':
    current_path = os.path.abspath(os.path.dirname(__file__))
    api_file = str(current_path + "/credentials/API_key.json")
    cb_api = cbapi.CoinbaseAPI(api_file)
    spike = Spike(statics.CURRENCIES, coinbase_api=cb_api, day_threshold=10, week_threshold=10,
                  notification_threshold=5)

    delay = 5*60

    while True:
        results = spike.get_spike_alerts(is_console=True)
        for result in results:
            print(result)
        time.sleep(delay)
