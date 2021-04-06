import numpy as np
import os
import time
from multiprocessing import Process
import json
from utils import API_wrapper as wpr
from utils import pricegraph as graph


current_path = os.path.abspath(os.path.dirname(__file__))
API_FILE = open(current_path + "/API_key.json")

API_KEY_DICT = json.load(API_FILE)
wrapper = wpr.API_wrapper(API_KEY_DICT["key"], API_KEY_DICT["secret"])

CURRENCIES = ["BTC", "EOS", "ETH", "ZRX", "XLM", "OMG", "XTZ", "BCH", "LTC", "GRT", "FIL", "ANKR", "COMP"]

# create dictionary containing colors for each coin (for plots)
COLORS = ["orange", "black", "blue", "grey", "blue", "purple", "green", "darkblue", "red", "lightblue", "pink",
          "darkred", "darkgreen"]
COLORS = {coin: COLORS[i] for i, coin in enumerate(CURRENCIES)}


if __name__ == '__main__':
    day_threshold = 10
    hour_threshold = 10
    delay = 5*60

    # dictionary containing the previously notified price percentage change, which is used to prevent repeated
    # notifications.
    notified = {coin: 0 for coin in CURRENCIES}
    notification_threshold = 5  # threshold for sending a new notification (%)

    while True:
        changes = []                # list containing the percentage price change,
        new_notifications = False   # specifies whether a notification is new or not.

        balances = wrapper.get_account_balance(CURRENCIES)

        for coin in CURRENCIES:
            change = wrapper.get_price_change(coin)
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

        time.sleep(delay)
