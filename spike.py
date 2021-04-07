import numpy as np
import os
import time
from utils import CoinbaseAPI as wpr
if os.name == 'nt':
    import winsound

CURRENCIES = ["BTC", "EOS", "ETH", "ZRX", "XLM", "OMG", "XTZ", "BCH", "LTC", "GRT", "FIL", "ANKR", "COMP"]


def beep(freq, duration):
    if os.name == 'nt':
        winsound.Beep(freq, duration)


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
                beep(880, 500)
                notified[coin] = change
                new_notifications = True
            elif change < -day_threshold and change - notified[coin] < -notification_threshold:
                print(" ↓ "+coin + " decreased by " + "%.2f" % (-change) + " %")
                beep(220, 500)
                notified[coin] = change
                new_notifications = True
            if np.abs(change) < day_threshold/2 < np.abs(notified[coin]):
                beep(440, 1000)
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
