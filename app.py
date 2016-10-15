import os
import sys
import json
import re
import requests
import apiai
import urlparse
import redis
import traceback
from flask import Flask, request
from dc_hub import get_hub_add
import SO_scrapper
import upcomingevents
app = Flask(__name__)
url = urlparse.urlparse(os.environ.get('REDISCLOUD_URL'))
redis_database = redis.Redis(host=url.hostname, port=url.port, password=url.password)
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
    add_get_started_button()
    add_persistent_menu()  # this function adds the persistent menu to the chat
    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing
    if data["object"] == "page":
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                if messaging_event["sender"]["id"] == '1880474155521998' :
                    break
                else :
                    if messaging_event.get("message"):  # someone sent us a message
                        sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                        recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                        try :
                            message_text = messaging_event["message"]["text"]  # the message's text
                        except KeyError :
                            break
                        parsing_message(sender_id, message_text)
                        #reading the payload from persistent menu
                    if messaging_event.get('postback') : #someone used one the persistent menu
                        payload_text = messaging_event["postback"]["payload"]  # the payload's text
                        if payload_text == 'DEV_ISSUE' :
                            user_details = get_user(messaging_event["sender"]["id"])
                            try :
                                msg = "Don't worry {} I will help you out.Please tell me what is you issue.".format(user_details['first_name'])
                            except KeyError:
                                msg = "Please tell me what is your issue."
                            send_message(messaging_event["sender"]["id"],msg)
                            redis_database.set(messaging_event["sender"]["id"],"DI")
                            log("Changing value of flag") # ---------**************************__-------------
                        elif payload_text == 'GET_STARTED_PAYLOAD' :
                            user_details = get_user(messaging_event["sender"]["id"])
                            try :
                                msg = "Hi {} !, Welcome to KOSS, How are you doing ?".format(user_details['first_name'])
                            except KeyError:
                                msg = "Hi !, Welcome to KOSS, How are you doing ?"
                            send_message(messaging_event["sender"]["id"],msg)
                        elif payload_text=="PAYLOAD_RECRUIT":
                            user_details = get_user(messaging_event["sender"]["id"])
                            try :
                                msg = "Good to see you want to come aboard {}. We generally recruit new memebers in spring semester.Keep checking our facebook page for latest update".format(user_details['first_name'])
                            except KeyError:
                                msg = "Good to see you want to come aboard. We generally recruit new memebers in spring semester.Keep checking our facebook page for latest update"                                                        
                            send_message(messaging_event["sender"]["id"],msg)
                        elif payload_text=="PAYLOAD_UPCOMING_EVENTS" :
                            user_details = get_user(messaging_event["sender"]["id"]) 
                            events = upcomingevents.main()
                            bubble_list = list()
                            try :
                                for event in events :  # since title and subtitle can be of maximum 80 chars
                                    if len(event['name']) > 80 :
                                        event['name'] = event['name'][:77] + "..."
                                    if len(event['desc']) > 80 :
                                        event['desc'] = event['desc'][:77] + "..."
                                    if "img_url" in event.keys() :  #checking if the image is present in the event
                                        bubble_list.append({"title":event['name'] , "subtitle": event['desc'] , "image_url":event['img_url']})
                                    else :
                                        bubble_list.append({"title":event['name'] , "subtitle": event['desc']})
                            except :
                                error_msg = "Got following error in getting upcoming events :\n{}".format(traceback.format_exc())
                                slack_notification(error_msg)
                            if bubble_list : 
                                #this all executes when there is atleast one bubble in bubble list
                                try:   
                                    msg = "Hey {} ! We are going to have following events : ".format(user_details['first_name'])
                                except KeyError:
                                    msg = "We are going to have following events : "
                                send_message(messaging_event["sender"]["id"],msg)
                                sending_generic_template(messaging_event["sender"]["id"],bubble_list)
                            else : 
                                try:   
                                    msg = "Hey {} ! There are no new events lined up right now".format(user_details['first_name'])
                                except KeyError:
                                    msg = "There are no new events lined up right now"
                                send_message(messaging_event["sender"]["id"],msg)
                    if messaging_event.get("delivery"):  # delivery confirmation
                        pass

                    if messaging_event.get("optin"):  # optin confirmation
                        pass

                    if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                        pass

    return "ok", 200

def add_get_started_button():
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps(
        {
  "setting_type":"call_to_actions",
  "thread_state":"new_thread",
  "call_to_actions":[
    {
      "payload":"GET_STARTED_PAYLOAD"
    }
  ]
}
    )
    r = requests.post("https://graph.facebook.com/v2.6/me/thread_settings", params=params, headers=headers, data=data)
    if r.status_code != 200:
        error_msg = "Got following error while adding get started button:\nStatus Code : {}\nText : {}".format(r.status_code,r.text)
        slack_notification(error_msg)
        log(r.status_code)
        log(r.text)
def add_persistent_menu():
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
                      "setting_type" : "call_to_actions",
                      "thread_state" : "existing_thread",
                      "call_to_actions":[
                        {
                          "type":"postback",
                          "title":"Upcoming Events",
                          "payload":"PAYLOAD_UPCOMING_EVENTS"                        
                        },
                        {
                          "type":"postback",
                          "title":"Recruitment",
                          "payload":"PAYLOAD_RECRUIT"
                        },
                        {
                          "type":"postback",
                          "title":"Facing some development issue",
                          "payload":"DEV_ISSUE"
                        },
                        {
                          "type":"web_url",
                          "title":"View Website",
                          "url":"http://kossiitkgp.in/"
                        }
                      ]
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/thread_settings", params=params, headers=headers, data=data)
    if r.status_code != 200:
        error_msg = "Got following error while adding persistent menu:\nStatus Code : {}\nText : {}".format(r.status_code,r.text)
        slack_notification(error_msg)
        log(r.status_code)
        log(r.text)


''' This function marks a msg as read , starts `typing` or stops it. sender_action can be following
mark_seen : Mark last message as read
typing_on : Turn typing indicators on
typing_off : Turn typing indicators off
'''
def sending_sender_action(recipient_id,sender_action) :
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data=json.dumps(
        {
      "recipient":{
        "id" : recipient_id
      },
      "sender_action":sender_action
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        error_msg = "Got following error while sending sender action:\nStatus Code : {}\nText : {}".format(r.status_code,r.text)
        slack_notification(error_msg)
        log("in sending_sender_action : {}".format(r.status_code))
        log(r.text)


def sending_generic_template(recipient_id,result_list):
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data=json.dumps(
        {
  "recipient":{
    "id":recipient_id
  },
  "message":{
    "attachment":{
      "type":"template",
      "payload":{
        "template_type":"generic",
        "elements":result_list
      }
    }
  }
})
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        error_msg = "Got following error while sending generic template:\nStatus Code : {}\nText : {}".format(r.status_code,r.text)
        slack_notification(error_msg)
        log("in sending_generic_template : {}".format(r.status_code))
        log(r.text)


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
    Flag=redis_database.get(sender_id)
    log("The value of flag is :{}".format(Flag))
    if Flag == 'DI' : #this means the user is faceing development issue and has replied with his/her query
        redis_database.delete(sender_id)
        sending_sender_action(sender_id,'typing_on')
        SO_results = SO_scrapper.main(message)
        log("Search results for {}".format(message))
        log(SO_results)
        if len(SO_results) == 0 :
            sending_sender_action(sender_id,'typing_off')
            try :
                msg="Sorry {} , I couldn't find anything about it.".format(user_details['first_name'])
            except KeyError :
                msg="Sorry, I couldn't find anything about it."
            send_message(sender_id,msg)
        else :
            sending_sender_action(sender_id,'typing_off')
            sending_generic_template(sender_id,SO_results)

    elif gsoc_re_1 or gsoc_re_2 :   #if user wants to know about gsoc 
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
        msg = apiai_call(message)
        send_message(sender_id, msg)


def apiai_call(message):
    ai = apiai.ApiAI(os.environ["APIAI_CLIENT_ACCESS_TOKEN"])
    request = ai.text_request()
    request.query = message 
    response = request.getresponse()
    response_json = json.loads(response.read().decode('utf-8'))
    return response_json['result']['fulfillment']['speech']


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
        error_msg = "Got following error while sending message:\nStatus Code : {}\nText : {}".format(r.status_code,r.text)
        slack_notification(error_msg)
        log("in send_message : {}".format(r.status_code))
        log(r.text)


def slack_notification(message):
    headers = {
        "Content-Type": "application/json"
    }
    data =json.dumps({
        "text":message
    })   
    r=requests.post(os.environ["SLACK_WEBHOOK_URL"] , headers=headers , data=data)
    log(os.environ["SLACK_WEBHOOK_URL"])
    if r.status_code != 200:
        log("in slack_notification : {}".format(r.status_code))
        log(r.text)    
def log(message):  # simple wrapper for logging to stdout on heroku
    print str(message)
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True)
