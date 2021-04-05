import pickle
import re
from typing import List

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow


def get_telegram_api_token(file_name):
    tmp_token = None
    with open(str(file_name), 'r') as f:
        tmp_token = f.readline()
    return tmp_token


# Get the API auth token for the google sheets API
def get_google_api_token(file_path, scopes):
    credentials = None

    # Open the pickle file
    with open(file_path, 'rb') as token:
        credentials = pickle.load(token)

    # Check if credentials are valid
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            # Allow the user to log in manually if token auth fails
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', scopes)
            credentials = flow.run_local_server(port=0)

            # Save credentials for future executions
            with open(file_path, 'wb') as token:
                pickle.dump(credentials, token)

    return credentials


# Helper function which divides array into chunks, giving us a list of lists
def chunk_list(lst, chunk_size):
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i+chunk_size]


def parse_times(frequencies):
    list_frequencies = frequencies.split(",")
    list_frequencies = list(map(str.lower, list_frequencies))


# This method converts a google sheets table into a dictionary containing cell values & names
def table_to_cells(google_sheets_table) -> dict:
    # Get the name of the first cell as it appears in the spread sheet
    regex_filter = re.search('Sheet1!(.*)\d{0,}:.*', google_sheets_table.get('range'), re.IGNORECASE)

    if not regex_filter:
        return None

    first_cell = regex_filter.group(1).strip()  # Get the name of the first cell

    # Get the starting index of the first cell
    regex_filter = re.search('([A-Z])(\d{0,})', first_cell, re.IGNORECASE)

    if not regex_filter:
        return None

    first_cell_letter = str(regex_filter.group(1))
    first_cell_index = int(regex_filter.group(2))

    value_table = google_sheets_table.get('values')

    cell_table = dict()
    # Iterate over cells and assign the names
    row_index = first_cell_index
    for row in value_table:
        column_name = first_cell_letter  # Set the column back to the initial one
        for item in row:
            cell_name = ''.join([str(column_name), str(row_index)])
            cell_table[cell_name] = item  # Add cell name
            column_name = chr(ord(column_name)+1)

        row_index += 1

    return cell_table


# Creates the body that will be sent to google sheets, mainly when inserting cells
def build_spreadsheet_message_body(list_rows: List[List]) -> dict:
    """
    This method will create a body that can be sent off to the google sheets API
    :param list_rows: Expects a list of rows, [[Value for row n column x], [Value for row n column x+1]]
    :return: A dictionary object that can be sent to the api
    """

    body = {'values': list_rows}
    return body


# Get the first cell name given its content value
def get_cell_name_by_value(table, cell_value) -> str:
    formatted_table = table_to_cells(google_sheets_table=table)

    # Get the cell name
    for cell_name, val in formatted_table.items():
        if str(val).lower() == str(cell_value).lower():
            return cell_name


# Get the cell name of the cell to the right or left of the origin_cell
def get_neighbour_cell(side: str, origin_cell: str) -> str:
    regex_filter = re.search('([A-Z])(\d{0,})', origin_cell, re.IGNORECASE)

    if str(side).lower() == 'l':
        result_cell = ''.join([chr(ord(regex_filter.group(1)) - 1), chr(ord(regex_filter.group(2)))])
        return result_cell
    elif str(side).lower() == 'r':
        result_cell = ''.join([chr(ord(regex_filter.group(1)) + 1), chr(ord(regex_filter.group(2)))])
        return result_cell

