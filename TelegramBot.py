from __future__ import print_function

from utils.telegram_utils import UtilityMethods, ScheduleThread
from telegram.ext import Updater, CommandHandler, CallbackContext


import schedule
import logging
import os

# Enable logging for Telegram bot
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


# noinspection PyTypeChecker
class TelegramBot:

    def __init__(self):
        # Get the Telegram API Token
        dir_path = os.path.abspath(os.path.dirname(__file__))
        file_path = os.path.join(dir_path, 'telegram-bot-api-key.txt')
        telegram_api_token = UtilityMethods.get_telegram_api_token(file_path)

        # Create updater (front end for Bot) to receive updates from telegram (messages, etc) & send them to dispatcher
        self.updater = Updater(token=telegram_api_token, use_context=True)

        # Create a dispatcher where we can register our handlers for commands & other behaviours
        self.dispatcher = self.updater.dispatcher

        self.context = None
        self.id = None

        # Add handlers which dictate how to respond to different commands
        self.dispatcher.add_handler(CommandHandler("start", self.bot_command_start))

        # Register callback behaviour with dispatcher
        # self.dispatcher.add_handler(CallbackQueryHandler(self.bot_helper_button_select_callback, pass_update_queue=True,
        #                                                  pass_user_data=True))

    def start_telegram_bot(self) -> None:
        """Starts the bot by putting the updater into a polling mode, and making the bot wait for commands
        """
        self.updater.start_polling()
        self.updater.idle()

    def test_function_message(self) -> None:
        """Just a stupid test message
        """
        self.context.bot.send_message(self.id, text="Time for your meds nerd")

    def bot_command_start(self, update: Updater, context: CallbackContext) -> None:
        """
        Mandatory instance method because the bot needs the context initialized in order to send messages
        :param update: An updater object used to receive data from the telegram chat
        :param context: A context object which allows us to send data to the chat
        """
        update.message.reply_text("Big money time (dab)")

        self.context = context
        self.id = update.effective_chat.id

        # Schedule a function to be executed at a given time interval until the bot is killed
        schedule.every((5*60)).seconds.do(self.test_function_message)
        ScheduleThread.ScheduleThread().start()


if __name__ == '__main__':
    bot = TelegramBot()
    bot.start_telegram_bot()

