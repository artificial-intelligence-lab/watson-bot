import requests
import json
import os
from flask import Flask, request
from dotenv import load_dotenv
from message import Message, QuickReply, ReceivedMessage
from template import Template
from attachment import Button, Element, ReceiptElement, List
from watson_developer_cloud import ConversationV1

context = {}

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
    
workspace_id  = os.environ.get("WORKSPACE_ID")
    
conversation = ConversationV1(
    username = os.environ.get("CONVERSATION_USERNAME"),
    password = os.environ.get("CONVERSATION_PASSWORD"),
    version = "2017-04-21"

)

response_obj  = conversation.message(
                                        workspace_id = workspace_id,
                                        message_input = {'text': 'hello'}, 
                                        context= context )

context = response_obj['context']

message_type = response_obj['output']['type']
template_buttons=[]
if message_type != 'text':
    quick_reply_options = response_obj['output']['quick_reply_options']
title = response_obj["output"]["text"][0]
for option_name in quick_reply_options:
    template_buttons.append(Button(type='postback',title=option_name,payload=option_name))
        
button_template = Template( Template.button_type, title=title, buttons = template_buttons )

msg = Message('template', button_template)

app = Flask(__name__)

@app.route('/', methods=['GET'])
def verify():
    # our endpoint echos back the 'hub.challenge' value specified when we setup the webhook
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == 'foo':
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return 'Hello World', 200


def reply(user_id, msg):
    data = {
        "recipient": {"id": user_id},
        "message": msg
    }
    print data
    resp = requests.post("https://graph.facebook.com/v2.6/me/messages?access_token=" + FB_APP_TOKEN, json=data)
    print(resp.content)

def prepare_reply(response_obj):
    message_type = response_obj['output']['type']
    title = response_obj["output"]["text"][0]
    quick_replies=[]
    template_buttons=[]
    if message_type != 'text':
        quick_reply_options = response_obj['output']['quick_reply_options']
    if message_type =='quick_reply':
        
        for option_name in quick_reply_options:
            quick_replies.append(QuickReply('text',title=option_name,   payload = option_name))
        msg = Message('quick', title , quick_replies=quick_replies)

    if message_type =='text':
        msg = Message('text', response_obj["output"]["text"][0])

    if message_type =='template':
        
        for option_name in quick_reply_options:
            template_buttons.append(Button(type='postback',title=option_name,payload=option_name))
        
        button_template = Template( Template.button_type, title=title, buttons = template_buttons )

        msg = Message('template', button_template)
    
    if message_type == 'list':
        template_list=[]
        for option_name in quick_reply_options:
             template_list.append(List(title=option_name,subtitle= option_name,image_url='https://s-media-cache-ak0.pinimg.com/236x/f2/4e/3f/f24e3fc72a42e7a7c275a7f547bba8ab.jpg'))

        list_template = Template( Template.list_type, elements = template_list )

        msg = Message('template', list_template)


        
    return msg.to_json()


@app.route('/', methods=['POST'])
def handle_incoming_messages():
    data = request.json
    sender = data['entry'][0]['messaging'][0]['sender']['id']
    message = data['entry'][0]['messaging'][0]['message']['text']
    global context
    
    #prepare IBM Watson Conversation request
    response_obj  = conversation.message(
                                    workspace_id = workspace_id,
                                    message_input = {'text': message}, 
                                    context= context )

    #having this variable set will make IBM Watson Conversation continue the dialog
    context = response_obj['context']
    #check if IBM Watson Conversion has detected any intent
    #check if intent confidence is quite high
    if response_obj['intents'] and response_obj['intents'][0]['confidence']>0.6:
        #some of the intents might have been configured but the dialog has not a complete flow, meaning no text is replied
        if response_obj["output"]["text"]:
            msg = prepare_reply(response_obj)
            reply(sender,msg)

    return 'ok'