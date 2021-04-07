import numpy as np
import os
import time
from utils.coinbase_utils import CoinbaseAPI as wpr
from typing import List

if os.name == 'nt':
    import winsound

CURRENCIES = ["BTC", "EOS", "ETH", "ZRX", "XLM", "OMG", "XTZ", "BCH", "LTC", "GRT", "FIL", "ANKR", "COMP"]


def beep(freq, duration):
    if os.name == 'nt':
        winsound.Beep(freq, duration)


def get_spike_alerts(is_console=False) -> List[str]:
    """
    Queries the coinbase API to get updates on significant changes in currencies
    :param is_console: Flag set for console usage vs Telegram Bot usage to get time readout
    :return: A list of strings which pertain to a currency
    """
    increasing_list = list()
    decreasing_list = list()
    changes = []  # list containing the percentage price change,

    for coin in CURRENCIES:
        change = wrapper.get_price_change(coin)
        changes.append(change)

        # notify if the price changed significantly today, if this increased by more than the notification_threshold
        # from the previous notification.
        if change > day_threshold and change - notified[coin] > notification_threshold:
            increasing_list.append(" ↑ " + coin + " increased by " + "%.2f" % change + " %")
            notified[coin] = change

        elif change < -day_threshold and change - notified[coin] < -notification_threshold:
            decreasing_list.append(" ↓ " + coin + " decreased by " + "%.2f" % (-change) + " %")
            notified[coin] = change

        # if np.abs(change) < day_threshold / 2 < np.abs(notified[coin]):
        #     if notified[coin] > 0:
        #         messages.append("Spike has ended for " + coin + ".")
        #     elif notified[coin] < 0:
        #         messages.append("Dip has ended for " + coin + ".")
        #     notified[coin] = 0

    message = increasing_list + decreasing_list
    if is_console:
        current_time = time.strftime("%H:%M:%S", time.localtime())
        time_stamp = "checked at " + str(current_time) + "\n\n"
        message.append(time_stamp)

    return message


if __name__ == '__main__':
    current_path = os.path.abspath(os.path.dirname(__file__))
    api_file = str(current_path + "/API_key.json")
    wrapper = wpr.CoinbaseAPI(api_file)

    day_threshold = 10
    hour_threshold = 10
    delay = 5*60

    # dictionary containing the previously notified price percentage change, which is used to prevent repeated
    # notifications.
    notified = {coin: 0 for coin in CURRENCIES}
    notification_threshold = 5  # threshold for sending a new notification (%)

    while True:
        results = get_spike_alerts(is_console=True)
        for change in results:
            print(change)
        time.sleep(delay)
