import logging
import os
import json
from quart import Blueprint, request, jsonify, current_app
from .decorators.security import signature_required
from .utils.whatsapp_utils import (
    process_whatsapp_message,
    is_valid_whatsapp_message,
)
import asyncio
from threading import Lock

webhook_blueprint = Blueprint("webhook", __name__)

class ChatSession:
    def __init__(self, recipient_number):
        self.recipient_number = recipient_number
        self.lock = Lock()
        self.message_queue = asyncio.Queue()
        self.flow_flag = None
        self.customer_data = {'customer_id':'','customer_name':'','customer_mobile_no':'','customer_house_image_id':"",
                'customer_house_latitude':'','customer_house_longitude':''}
        self.search_data = {'customer_id':'','customer_name':'','customer_mobile_no':'','customer_house_image_id':"",
                'customer_house_latitude':'','customer_house_longitude':''}

    def save_session(self, filename):
        session_data = {
            'recipient_number': self.recipient_number,
            'flow_flag': self.flow_flag,
            'customer_data': self.customer_data,
            'search_data': self.search_data
            # Add other relevant fields here
        }
        with open(filename, 'w') as file:
            json.dump(session_data, file, indent=2)

    @classmethod
    def load_session(cls, filename):
        with open(filename, 'r') as file:
            session_data = json.load(file)
            recipient_number = session_data.get('recipient_number')
            flow_flag = session_data.get('flow_flag')
            customer_data = session_data.get('customer_data')
            search_data = session_data.get('search_data')
            # Create a new ChatSession instance
            session = cls(recipient_number)
            session.flow_flag= flow_flag
            session.customer_data = customer_data
            session.search_data = search_data
            return session


async def handle_message():
    """
    Handle incoming webhook events from the WhatsApp API.

    This function processes incoming WhatsApp messages and other events,
    such as delivery statuses. If the event is a valid message, it gets
    processed. If the incoming payload is not a recognized WhatsApp event,
    an error is returned.

    Every message send will trigger 4 HTTP requests to your webhook: message, sent, delivered, read.

    Returns:
        response: A tuple containing a JSON response and an HTTP status code.
    """
    # print("Handling incoming")
    body = await request.get_json()
    logging.info(f"request body: {body}")

    # Check if it's a WhatsApp status update
    if (
        body.get("entry", [{}])[0]
        .get("changes", [{}])[0]
        .get("value", {})
        .get("statuses")
    ):
        logging.info("Received a WhatsApp status update.")
        return jsonify({"status": "ok"}), 200
    # Extract user_id
    message = body["entry"][0]["changes"][0]["value"]["messages"][0]
    recipient_number = message["from"]
    print(1)
    if os.path.exists(f'./app/session_management/{recipient_number}_session.json') == True:
        session = ChatSession.load_session(f'./app/session_management/{recipient_number}_session.json')
    else:
        session = ChatSession(recipient_number)
    print('session: ', session)
    # Acquire the lock before processing the message
    with session.lock:
        await session.message_queue.put(message)
        # try:
        if is_valid_whatsapp_message(body):
            session  = await process_whatsapp_message(body,recipient_number,session)
            print(2)
            # Save session to a file
            session.save_session(f'./app/session_management/{recipient_number}_session.json')
            return jsonify({"status": "ok"}), 200
        else:
            # if the request is not a WhatsApp API event, return an error
            return (
                jsonify({"status": "error", "message": "Not a WhatsApp API event"}),
                404,
            )
        # except json.JSONDecodeError:
        #     logging.error("Failed to decode JSON")
        #     return jsonify({"status": "error", "message": "Invalid JSON provided"}), 400


# Required webhook verifictaion for WhatsApp
def verify():
    # Parse params from the webhook verification request
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    # Check if a token and mode were sent
    if mode and token:
        # Check the mode and token sent are correct
        if mode == "subscribe" and token == current_app.config["VERIFY_TOKEN"]:
            # Respond with 200 OK and challenge token from the request
            logging.info("WEBHOOK_VERIFIED")
            return challenge, 200
        else:
            # Responds with '403 Forbidden' if verify tokens do not match
            logging.info("VERIFICATION_FAILED")
            return jsonify({"status": "error", "message": "Verification failed"}), 403
    else:
        # Responds with '400 Bad Request' if verify tokens do not match
        logging.info("MISSING_PARAMETER")
        return jsonify({"status": "error", "message": "Missing parameters"}), 400

@webhook_blueprint.route("/webhook", methods=["GET"])
async def webhook_get():
    return verify()

@webhook_blueprint.route("/webhook", methods=["POST"])
@signature_required
async def webhook_post():
    return await handle_message()
