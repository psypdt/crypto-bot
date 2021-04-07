import pickle
import re
from typing import List


def get_telegram_api_token(file_name):
    tmp_token = None
    with open(str(file_name), 'r') as f:
        tmp_token = f.readline()
    return tmp_token


# Helper function which divides array into chunks, giving us a list of lists
def chunk_list(lst, chunk_size):
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i+chunk_size]


# Useless, doesn't return
def parse_times(frequencies):
    list_frequencies = frequencies.split(",")
    list_frequencies = list(map(str.lower, list_frequencies))
