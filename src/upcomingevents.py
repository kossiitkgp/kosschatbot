from pastebin import PastebinAPI
from bs4 import BeautifulSoup as bs
import os
import requests


def main():
    pb = PastebinAPI()
    api_dev_key = os.environ['PASTEBIN_DEV_KEY']
    username = os.environ['PASTEBIN_USERNAME']
    password = os.environ['PASTEBIN_PASSWORD']
    # generating session key which will be needed after wards
    api_user_key = pb.generate_user_key(api_dev_key, username, password)

    all_pastes = pb.pastes_by_user(
        api_dev_key, api_user_key, results_limit=None)
    pastes_xml = "<all_pastes>" + all_pastes + "</all_pastes>"
    soup = bs(pastes_xml, 'xml')
    for paste_name in soup.findAll('paste_title'):
        if paste_name.string == "upcoming_events":
            paste_parent = paste_name.parent
            for key in paste_parent.find('paste_key'):
                # getting the key of the upcoming_events paste
                upcoming_events_key = key.string
            break
    events_json = requests.get(
        "http://pastebin.com/raw/{}".format(upcoming_events_key)).json()  # getting paste data
    return events_json
