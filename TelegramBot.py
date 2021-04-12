from __future__ import print_function

from utils.telegram_utils import UtilityMethods, ScheduleThread
from telegram.ext import Updater, CommandHandler, CallbackContext

from utils.coinbase_utils.PriceGraph import PriceGraph
import utils.coinbase_utils.CoinbaseAPI as cbapi
import utils.coinbase_utils.GlobalStatics as statics

import warnings
import spike
import schedule
import io
import logging
import json
import os

# Enable logging for Telegram bot
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Silence annoying matplot lib warnings
warnings.filterwarnings("ignore", module="matplotlib")
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")


# noinspection PyTypeChecker
class TelegramBot:
    """
    This class is designed to launch a telegram bot and expose all functionality to the user
    """

    def __init__(self):
        """
        Initializes a CoinbaseAPI object and a Spike object using credentials stored on file, and authorizes users from
        whitelist.
        """
        # Create instance of CoinbaseAPI to facilitate communication between bot & coinbase
        current_path = os.path.abspath(os.path.dirname(__file__))
        api_file = str(current_path + "/credentials/API_key.json")

        self.coinbase_api = cbapi.CoinbaseAPI(api_file)
        self.spike = spike.Spike(currencies=statics.CURRENCIES, coinbase_api=self.coinbase_api,
                                 notification_threshold=5, day_threshold=10, week_threshold=10)
        self.price_graph = PriceGraph(self.coinbase_api)
        self.notification_periodicity = 5  # in minutes

        # Get whitelist
        whitelist_file = str(current_path + "/credentials/whitelist.json")
        file = open(whitelist_file)
        whitelist_dict = json.load(file)
        self.whitelist_users = whitelist_dict["whitelisted"]
        # TODO: import password

        # Get the Telegram API Token
        dir_path = os.path.abspath(os.path.dirname(__file__))
        file_path = os.path.join(dir_path, 'credentials/telegram-bot-api-key.txt')
        telegram_api_token = UtilityMethods.get_telegram_api_token(file_path)

        # Create updater (front end for Bot) to receive updates from telegram (messages, etc) & send them to dispatcher
        self.updater = Updater(token=telegram_api_token, use_context=True)

        # Create a dispatcher where we can register our handlers for commands & other behaviours
        self.dispatcher = self.updater.dispatcher

        self.context = None
        self.id = None

        # Add handlers which dictate how to respond to different commands
        self.dispatcher.add_handler(CommandHandler("start", self.bot_command_start))
        self.dispatcher.add_handler(CommandHandler("latest", self.bot_command_latest))
        self.dispatcher.add_handler(CommandHandler("graph", self.bot_command_send_graph))
        self.dispatcher.add_handler(CommandHandler("gimmemoney", self.bot_command_gimme_money))
        self.dispatcher.add_handler(CommandHandler("portfolio", self.bot_command_portfolio))
        self.dispatcher.add_handler(CommandHandler("current", self.bot_command_exchange_current))
        self.dispatcher.add_handler(CommandHandler("profits", self.bot_command_profits))

        # Register callback behaviour with dispatcher
        # self.dispatcher.add_handler(CallbackQueryHandler(self.bot_helper_button_select_callback, pass_update_queue=True,
        #                                                  pass_user_data=True))

    def authenticate(self, update: Updater) -> bool:
        """
        Checks if a user is on the whitelist.

        :param update:
        :return:
        """
        username = update.message.from_user["username"]
        if username not in self.whitelist_users:
            print("Unauthorized user ", username)
            return False
        return True

    def start_telegram_bot(self) -> None:
        """
        Starts the bot by putting the updater into a polling mode, and making the bot wait for commands
        """
        self.updater.start_polling()
        self.updater.idle()

    def bot_command_start(self, update: Updater, context: CallbackContext) -> None:
        """
        Mandatory instance method because the bot needs the context initialized in order to send messages

        :param update: An updater object used to receive data from the telegram chat
        :param context: A context object which allows us to send data to the chat
        """
        if not self.authenticate(update):  # Verify that the user is allowed to access the bot
            return

        update.message.reply_text("Bot started. Let's make some money!")

        self.context = context
        self.id = update.effective_chat.id
        self.bot_send_spike_alerts()

        # Schedule a function to be executed at a given time interval until the bot is killed
        schedule.every((self.notification_periodicity*60)).seconds.do(self.bot_send_spike_alerts)
        ScheduleThread.ScheduleThread().start()

    def bot_command_latest(self, update: Updater, context: CallbackContext) -> None:
        """
        Retrieves latest spike notifications, independent of previous notifications via command "/latest".

        :param update: The update context required to reply to the command.
        :param context: Default CallbackContext.
        """
        if not self.authenticate(update):  # Verify that the user is allowed to access the bot
            return

        username = update.message.from_user["username"]
        print(username, " requested the latest changes.")
        messages = self.spike.get_spike_alerts(ignore_previous=True)

        if len(messages) == 0:
            update.message.reply_text("No updates to show.")
            return

        formatted_list = [str(message) + "\n" for message in messages]
        formatted_message = "".join(formatted_list)
        print(formatted_message)

        update.message.reply_text(formatted_message)

    def bot_command_send_graph(self, update: Updater, context: CallbackContext):
        """
        Sends an image generated by PriceGraph object to user requesting the graph

        :param update: Updater object
        :param context: Context object used to send photo to user requesting graph
        :return:
        """
        if not self.authenticate(update):  # Verify that the user is allowed to access the bot
            return
        username = update.message.from_user["username"]

        print(username, " requested a graph.")

        # Get PIL image from PriceGraph
        pil_image = self.price_graph.normalised_price_graph(period="week", is_interactive=False, get_pil_image=True)
        # pil_image.show()
        # Convert PIL Image into raw bytes
        buffer = io.BytesIO()
        buffer.name = 'image.jpeg'
        pil_image.save(buffer, 'JPEG')
        buffer.seek(0)

        context.bot.send_photo(update.effective_chat.id, photo=buffer)

    def bot_command_gimme_money(self, update: Updater, context: CallbackContext):
        if not self.authenticate(update):  # Verify that the user is allowed to access the bot
            return

        username = update.message.from_user["username"]
        print("A large sum of money was given to ", username, ".")
        update.message.reply_text("💸💸💸💸💸💸💸💸💸💸\n")

    def bot_command_portfolio(self, update: Updater, context: CallbackContext):
        if not self.authenticate(update):
            return
        username = update.message.from_user["username"]

        print(username, " requested portfolio")

        # Get period and coin from user
        coin = context.args[0]

        period = "month"

        try:
            period = context.args[1]
        except IndexError:
            pass

        # Get PIL image
        pil_image = self.price_graph.portfolio_price_graph(coin=coin, period=period)

        buffer = io.BytesIO()
        buffer.name = 'image.jpeg'
        pil_image.save(buffer, 'JPEG')
        buffer.seek(0)

        context.bot.send_photo(update.effective_chat.id, photo=buffer)

    def bot_command_exchange_current(self, update: Updater, context: CallbackContext):
        """
        Sends the current exchange rate in CHF of a coin passed as an argument.

        NOTE: The second argument must be a FIAT currency (CHF, USD, EUR, etc.)

        :param update: Updater used to reply to a message
        :param context: Context needed to fetch argument from user
        """
        coin = context.args[0].upper()
        to_currency = "CHF"

        if len(context.args) > 1:
            to_currency = context.args[1].upper()

        coin_currency_pair = coin + "-" + to_currency
        current_exchange = float(self.coinbase_api.client.get_spot_price(currency_pair=coin_currency_pair).amount)

        output = "1 {} is {:.2f} {}".format(coin.upper(), current_exchange, to_currency.upper())

        update.message.reply_text(str(output))

    def bot_command_profits(self, update: Updater, context: CallbackContext):
        """
        Used to see how much profit could be gain from selling a certain currency

        agr[0]: Currency which user wants to sell
        arg[1]: Amount of currency user wants to sell
        arg[2]: Currency in which profits are displayed (CHF, USD, etc.)

        :param update: Updater used to respond to message
        :param context: Context used to extract input arguments
        """
        sell_coin = context.args[0]
        sell_amount = float(context.args[1])
        profit_currency = context.args[2]
        message = self.spike.get_sell_profitability(coin=sell_coin, amount=sell_amount, profit_currency=profit_currency)

        update.message.reply_text(message)

    def bot_send_spike_alerts(self) -> None:
        """
        Sends a spike alert to the user in chat. This is not a callback hence why it doesn't take in a context
        or updater as arguments.
        """
        print("Checking for new alerts.")
        messages = self.spike.get_spike_alerts()

        if len(messages) == 0:
            return

        # formatted_list = [str(message) + "\n" for message in messages]
        formatted_message = "\n".join(messages)
        print(formatted_message)

        self.context.bot.send_message(self.id, formatted_message)


if __name__ == '__main__':
    bot = TelegramBot()
    bot.start_telegram_bot()

