import os
import sys
import json
import re
import requests
from flask import Flask, request
from dc_hub import get_hub_add
app = Flask(__name__)


@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events

    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message_text = messaging_event["message"]["text"]  # the message's text
                    parsing_message(sender_id, message_text)
                    #send_message(sender_id, "Just a change ")

                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    pass

    return "ok", 200
def get_user(sender_id) :
    '''
    The user_details dictionary will have following keys 
    first_name : First name of user
    last_name :Last name of user 
    profile_pic : Profile picture of user 
    locale : Locale of the user on Facebook
    '''
    base_url = "https://graph.facebook.com/v2.6/{}?fields=first_name,last_name,profile_pic,locale,timezone,gender&access_token={}".format(sender_id,os.environ["PAGE_ACCESS_TOKEN"])
    user_details = requests.get(base_url).json()
    return user_details
def parsing_message(sender_id , message):
    user_details = get_user(sender_id)  #getting user details
    #gsco re's
    gsoc_re_1=re.search(r'gsoc', message , re.IGNORECASE)
    gsoc_re_2=re.search(r'google summer of code', message , re.IGNORECASE)
    #dc re's
    dc_re_1=re.search(r'dc', message , re.IGNORECASE)
    dc_re_2=re.search(r'hub', message , re.IGNORECASE)
    dc_re_3=re.search(r'add', message , re.IGNORECASE)
    if gsoc_re_1 or gsoc_re_2 :   #if user wants to know about gsoc 
        try :
            msg = "Hey {} ! I don't know much but you can find more about GSoC(Google Summer of Code) at https://wiki.metakgp.org/w/Google_Summer_of_Code ".format(user_details['first_name'])
        except KeyError:
            msg = "I don't know much but you can find more about GSoC(Google Summer of Code) at https://wiki.metakgp.org/w/Google_Summer_of_Code "
        send_message(sender_id, msg)
    elif dc_re_1 and dc_re_2 and dc_re_3 :
        hub_address = get_hub_add()
        try :
            msg = "Hi {} ! The current hub address is {}".format(user_details['first_name'],hub_address)
        except KeyError: 
            msg = "The current hub address is {}".format(hub_address)
        send_message(sender_id, msg)
    else :
        try :
            msg = "{} can you say something else".format(user_details['first_name'])
        except KeyError :
            msg = "Can you say something else"
        send_message(sender_id, msg)
 

def send_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def log(message):  # simple wrapper for logging to stdout on heroku
    print str(message)
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True)
