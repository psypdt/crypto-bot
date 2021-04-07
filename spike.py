from utils.coinbase_utils import CoinbaseAPI as cbapi
import utils.coinbase_utils.GlobalStatics as statics
import time
import os


class Spike:
    def __init__(self, currencies: list, notification_threshold: float, day_threshold: float,
                 coinbase_api: cbapi.CoinbaseAPI):
        """
        :param currencies: List of crypto currency identifiers (BTC, XRP, etc.)
        :param notification_threshold: Amount in (%) needed for another notification to be sent for a coin
        :param day_threshold: Minimum (%) change over an entire day needed to send notification
        :param coinbase_api: Coinbase API object to fetch data for crypto currencies
        """
        self.currencies = currencies
        self.notification_threshold = notification_threshold  # threshold for sending a new notification (%)
        self.day_threshold = day_threshold
        self.coinbase_api = coinbase_api

        # dictionary containing the previously notified price percentage change, used to prevent repeated notifications.
        self.notified = {coin: 0 for coin in statics.CURRENCIES}

    def get_spike_alerts(self, is_console=False) -> [(float, str)]:
        """
        Queries the coinbase API to get updates on significant changes in currencies

        :param is_console: Flag set for console usage vs Telegram Bot usage to get time readout
        :return: A list of tuples where the key is percentage change & value is the entire message string
        """
        message = list()
        changes = []  # list containing the percentage price change,

        for coin in statics.CURRENCIES:
            percentage_change = self.coinbase_api.get_price_change(coin)
            changes.append(percentage_change)

            # notify if the price changed significantly today, if this increased by more than the notification_threshold
            # from the previous notification.
            if percentage_change > self.day_threshold and percentage_change - self.notified[coin] > \
                    self.notification_threshold:
                message.append((percentage_change, "↑ " + coin + " increased by " +
                                        "%.2f" % percentage_change + " %"))
                self.notified[coin] = percentage_change

            elif percentage_change < -self.day_threshold and percentage_change - self.notified[coin] < \
                    -self.notification_threshold:
                message.append((percentage_change, "↓ " + coin + " decreased by " +
                                        "%.2f" % (-percentage_change) + " %"))
                self.notified[coin] = percentage_change

            # if np.abs(change) < day_threshold / 2 < np.abs(notified[coin]):
            #     if notified[coin] > 0:
            #         messages.append("Spike has ended for " + coin + ".")
            #     elif notified[coin] < 0:
            #         messages.append("Dip has ended for " + coin + ".")
            #     notified[coin] = 0

        message.sort(key=lambda tup: tup[0], reverse=True)
        message = [value for key, value in message]

        if is_console:
            current_time = time.strftime("%H:%M:%S", time.localtime())
            time_stamp = "checked at " + str(current_time) + "\n\n"
            message.append(time_stamp)

        return message


if __name__ == '__main__':
    current_path = os.path.abspath(os.path.dirname(__file__))
    api_file = str(current_path + "/API_key.json")
    cb_api = cbapi.CoinbaseAPI(api_file)
    spike = Spike(statics.CURRENCIES, day_threshold=10, notification_threshold=5, coinbase_api=cb_api)

    delay = 5*60

    while True:
        results = spike.get_spike_alerts(is_console=True)
        for result in results:
            print(result)
        time.sleep(delay)
