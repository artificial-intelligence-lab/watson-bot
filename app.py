import requests
import json
import os
from flask import Flask, request
from dotenv import load_dotenv
from watson_developer_cloud import ConversationV1


context = {}

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
    
workspace_id  = os.environ.get("WORKSPACE_ID")
    
conversation = ConversationV1(
    username = os.environ.get("CONVERSATION_USERNAME"),
    password = os.environ.get("CONVERSATION_PASSWORD"),
    version = "2017-04-21"

)

# Get port from environment variable or choose 9099 as local default
port = int(os.getenv("PORT", 9099))
# FB messenger credentials
FB_APP_TOKEN = os.environ.get("FB_APP_TOKEN")
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
        "message": {"text": msg}
    }
    resp = requests.post("https://graph.facebook.com/v2.6/me/messages?access_token=" + FB_APP_TOKEN, json=data)
    print(resp.content)


@app.route('/', methods=['POST'])
def handle_incoming_messages():
    data = request.json
    sender = data['entry'][0]['messaging'][0]['sender']['id']
    message = data['entry'][0]['messaging'][0]['message']['text']
    global context
    print message
    #prepare Watson Conversation request
    response_obj  = conversation.message(workspace_id=workspace_id,message_input={
        'text': message}, context= context )
    
    context = response_obj['context']

    response = response_obj["output"]["text"]
    reply(sender,response[0])

    return 'ok'
    

if __name__ == '__main__':
    # Run the app, listening on all IPs with our chosen port number
    app.run(host='0.0.0.0', port=port)