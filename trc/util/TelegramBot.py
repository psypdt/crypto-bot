from __future__ import print_function

import logging
import os
from pprint import pprint
import re

import schedule

from util import UtilityMethods, ScheduleThread
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from googleapiclient.discovery import build

# Suppress annoying google api import warnings
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)

# Enable logging for Telegram bot
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


# This class contains the functions and behaviours of the Telegram bot
class TelegramBot:

    def __init__(self):
        # Get the Telegram API Token
        d_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        f_path = os.path.join(d_path, 'token.txt')
        telegram_api_token = UtilityMethods.get_telegram_api_token(f_path)

        # Create updater (front end for Bot) to receive updates from telegram (messages, etc) & send them to dispatcher
        self.updater = Updater(token=telegram_api_token, use_context=True)

        # Create a dispatcher where we can register our handlers for commands & other behaviours
        self.dispatcher = self.updater.dispatcher

        self.context = None
        self.id = None

        # Add handlers which dictate how to respond to different commands
        self.dispatcher.add_handler(CommandHandler("start", self.bot_command_start))
        self.dispatcher.add_handler(CommandHandler("chores", self.bot_command_chores))
        self.dispatcher.add_handler(CommandHandler("select", self.bot_command_set_chore))
        self.dispatcher.add_handler(CommandHandler("done", self.bot_command_done))

        # Register callback behaviour with dispatcher
        self.dispatcher.add_handler(CallbackQueryHandler(self.bot_helper_button_select_callback, pass_update_queue=True,
                                                         pass_user_data=True))

        # Add permissions used to access sheet
        self.SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        self.SHEET_ID = "1WuBB96pMe5QlGI8npdDqmcMjfmv9R6IvEKOSOZgAZR0"
        self.DEFAULT_CELL_RANGE = "A2:C"

        # Validate credentials for Google Sheets API
        credentials = None

        # Check if pickle token file exists
        if os.path.exists('token.pickle'):
            f_path = os.path.join(d_path, 'token.pickle')
            credentials = UtilityMethods.get_google_api_token(f_path, self.SCOPES)

        # Create a service which lets us access the google API with our credentials
        self.google_sheets_service = build('sheets', 'v4', credentials=credentials)

    # This method will launch the bot. Bot persists until the program is killed
    def start_telegram_bot(self):
        self.updater.start_polling()
        self.updater.idle()

    def test_function_message(self):
        self.context.bot.send_message(self.id, text="Time for your meds nerd")

    # Instance method which implements behaviour when /start command is received
    def bot_command_start(self, update: Updater, context: CallbackContext):
        print(self.google_api_get_column())
        update.message.reply_text("Some response")

        self.context = context
        self.id = update.effective_chat.id

        schedule.every(40).seconds.do(self.test_function_message)
        ScheduleThread.ScheduleThread().start()

    # Get all for the individual that sent the command
    def bot_command_chores(self, update: Updater, context: CallbackContext):
        name = update.message.from_user.first_name
        associated_chores = self.google_api_get_associated_chores(name, self.DEFAULT_CELL_RANGE)

        # Check which chores have been completed
        table = self.google_api_get_table(cell_range="B2:B")
        chore_dict = dict()  # temp dict storing cell:chore pairs

        # Collect all chores and the associated cell name
        for chore in associated_chores:
            key = UtilityMethods.get_cell_name_by_value(table=table, cell_value=chore)
            chore_dict[key] = chore

        # Eject all chores which are marked as completed
        for cell, chore in chore_dict.items():
            done_label_cell = UtilityMethods.get_neighbour_cell(
                side='r', origin_cell=UtilityMethods.get_neighbour_cell(side='r', origin_cell=cell))
            cell_content = self.google_api_get_column(cell_range=done_label_cell)
            if cell_content:
                associated_chores.remove(chore)  # Eject completed chore

        # Construct and execute response
        response = ""
        if associated_chores:
            for chore in associated_chores:
                response += str(f'\n_{chore}_')
        else:
            response = "Looks like you've got no chores"

        update.message.reply_text(response, parse_mode="Markdownv2")

    # Inserts a selected chore into the google sheets
    def bot_command_set_chore(self, update: Updater, context: CallbackContext):
        # Get all chores from the spread sheet
        chore_column = self.google_api_get_table(cell_range="B2:B")
        formatted_chore_columns = UtilityMethods.table_to_cells(google_sheets_table=chore_column)

        # Get all chore:name pairs
        pair_table = self.google_api_get_table(cell_range="A2:B")
        formatted_pair_table = UtilityMethods.table_to_cells(google_sheets_table=pair_table)

        # Remove all chores which have been allocated
        chore_list = list()

        for cell_name, chore in formatted_chore_columns.items():
            neighbour = UtilityMethods.get_neighbour_cell(side='l', origin_cell=cell_name)
            # Append if no name exists in the neighbour cell
            if not formatted_pair_table.get(neighbour):
                chore_list.append(chore)

        # Get all chores and split them into 2 columns
        chore_chunks = UtilityMethods.chunk_list(chore_list, 2)
        custom_keyboard = list()  # Will display chores as buttons

        for row in chore_chunks:
            custom_keyboard.append([InlineKeyboardButton(chore, callback_data=str(chore)) for chore in row])

        custom_keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
        reply_markup = InlineKeyboardMarkup(custom_keyboard)  # Initiate new markup keyboard
        update.message.reply_text("Please select a chore", reply_markup=reply_markup)

    # Defines behaviour when the /done command is entered
    def bot_command_done(self, update: Updater, context: CallbackContext):
        user = update.message.from_user.first_name
        associated_chores = self.google_api_get_associated_chores(name=user, cell_range=self.DEFAULT_CELL_RANGE)

        # Chunk list into 2 columns
        chore_chunks = UtilityMethods.chunk_list(associated_chores, 2)
        custom_keyboard = list()

        for row in chore_chunks:
            custom_keyboard.append([InlineKeyboardButton(chore, callback_data=str('d:{}'.format(chore))) for chore in row])

        custom_keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
        reply_markup = InlineKeyboardMarkup(custom_keyboard)
        update.message.reply_text("Please select the chore you completed", reply_markup=reply_markup)

    # A callback which dictates how the bot acts when a button is pressed
    def bot_helper_button_select_callback(self, update: Updater, context: CallbackContext):
        query = update.callback_query

        # Check if user opted to cancel the action
        if str(query.data).lower() == 'cancel':
            query.answer()
            query.edit_message_text(text="*Chore selection has been canceled*", parse_mode="Markdownv2")
            return

        regex_filter = re.search('(d:)(.*)', query.data, re.IGNORECASE) # Check if d/ flag found
        flag = None
        if regex_filter:
            flag = regex_filter.group(1)

        if not flag == 'd:':
            self.bot_helper_chore_selection_behaviour(query=query)
        else:
            self.bot_helper_chore_done_behaviour(query=query, completed_chore=regex_filter.group(2))

    # Defines how the bot behaves if the callback originated from users assigning tasks
    def bot_helper_chore_selection_behaviour(self, query):
        # Write into the google sheets
        assigned_chore = query.data
        user = query.from_user.first_name

        # Convert the table so we can get the cell names
        table = self.google_api_get_table("A2:B")
        # Cell where name will be written
        chore_sell = UtilityMethods.get_cell_name_by_value(table, assigned_chore)
        cell_contents = UtilityMethods.build_spreadsheet_message_body([[user]])

        # Get the cell to the left of the chore cell
        destination_cell = UtilityMethods.get_neighbour_cell(origin_cell=chore_sell, side='l')
        formatted_table = UtilityMethods.table_to_cells(table)

        query.answer()

        # Check that cell is available
        if formatted_table.get(destination_cell) == '':
            self.google_api_write_cell(cell_range=destination_cell, cell_values=cell_contents)
            query.edit_message_text(text="*{}* is now on *{}* duty".format(query.from_user.first_name, query.data),
                                    parse_mode="Markdownv2")
        else:
            query.edit_message_text(text="Looks like *{}* is already taken by *{}*"
                                    .format(query.data, formatted_table.get(destination_cell)),
                                    parse_mode="Markdownv2")

    # Defines how the bot behaves when the user selects a chore after using the /done command
    def bot_helper_chore_done_behaviour(self, query, completed_chore):
        user = query.from_user.first_name

        table = self.google_api_get_table(cell_range="B2:D")
        chore_cell = UtilityMethods.get_cell_name_by_value(table=table, cell_value=completed_chore)

        destination_cell = \
            UtilityMethods.get_neighbour_cell(side='r',origin_cell=
            UtilityMethods.get_neighbour_cell(side='r', origin_cell=chore_cell))

        query.answer()

        cell_values = UtilityMethods.build_spreadsheet_message_body([["done"]])
        self.google_api_write_cell(cell_range=destination_cell, cell_values=cell_values)
        query.edit_message_text(text="*{}* was marked as *done* by {}".format(completed_chore, user),
                                parse_mode="Markdownv2")


    ### All google API methods are placed here ###


    # Get a range of cells from the google sheet
    def google_api_get_table(self, cell_range):
        try:
            table = self.google_sheets_service.spreadsheets().values().get(spreadsheetId=self.SHEET_ID,
                                                                           range=cell_range).execute()
        except Exception as ex:
            table = None
            pprint(ex)
        return table

    # Get all chores associated to a person
    def google_api_get_associated_chores(self, name, cell_range: str):
        try:
            formatted_name = str(name).lower()
            associated_chores = list()  # Chores associated with a person

            table = self.google_sheets_service.spreadsheets().values().get(spreadsheetId=self.SHEET_ID,
                                                                           range=cell_range).execute()
            # Get the rows as lists of elements
            table_rows = table.get("values", [])

            # Check if name exists in spread sheet in column A
            if formatted_name not in list(map(str.lower, self.google_api_get_column("A2:A"))):
                return None

            for row in table_rows:
                if str(row[0]).lower() == formatted_name:  # row[0] contains the participants name
                    associated_chores.append(row[1])  # Append chore located in row[1]

            return associated_chores

        except Exception as ex:
            print(ex)

    # Get all elements stored in the columns. Gets all chores by default
    def google_api_get_column(self, cell_range: str = "B2:B") -> list:
        try:
            # Get all entries from cell B2 down
            table = self.google_sheets_service.spreadsheets().values().get(spreadsheetId=self.SHEET_ID,
                                                                           range=cell_range).execute()
            # Get all values obtained from the spread-sheet
            rows = table.get("values")

            # Turn the list of cells into a list of entries (list of chores)
            flatten = lambda l: [item for sublist in l for item in sublist]
            return flatten(rows)

        except Exception as ex:
            print(ex)

    # Write data into a specified cell range
    def google_api_write_cell(self, cell_range, value_input_option: str = "RAW", cell_values: dict = None):
        try:
            response = self.google_sheets_service.spreadsheets().values().update(
                spreadsheetId=self.SHEET_ID,
                range=cell_range,
                valueInputOption=value_input_option,
                body=cell_values).execute()
            pprint(response)
        except Exception as ex:
            print(ex)
