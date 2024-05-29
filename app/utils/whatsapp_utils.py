import logging
from quart import current_app, jsonify
import aiohttp
import json
import requests
from recognizers_number import recognize_number, Culture
from recognizers_date_time import recognize_datetime
from datetime import date,datetime,timedelta
# from app.services.openai_service import generate_response
import re
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import calendar
from google.cloud.firestore_v1.base_query import FieldFilter
import pytz


# Initialize Firebase Admin SDK
cred = credentials.Certificate('./app/utils/firebase_cred/meat-house-delivery-bot-firebase-adminsdk-wn9ad-b6c2eef24b.json')
firebase_admin.initialize_app(cred)
# Initialize Firestore instance
db = firestore.client()

Details_empty_dict = {'customer_id':'','customer_name':'','customer_mobile_no':'','customer_house_image_id'
                'customer_house_latitude':'','customer_house_longitude':''}
details_dict = Details_empty_dict.copy()
flow_flag = None
customer_data = None



class ValidationResult:
    def __init__(
        self, is_valid: bool = False, value: object = None, message: str = None
    ):
        self.is_valid = is_valid
        self.value = value
        self.message = message

def log_http_response(response):
    logging.info(f"Status: {response.status}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")


def get_text_message_input(recipient_number, text):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to":recipient_number,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
    )

def get_location_message_input(recipient_number, lattitude, longitude):
    return json.dumps(
        {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_number,
        "type": "location",
        "location": {
            "latitude": lattitude,
            "longitude": longitude,
            "name": "Customer House Location"
  }
}
    )

def get_image_message_input(recipient_number, image_id):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to":recipient_number,
            "type": "image",
            "image": {
                "id" : image_id,
                "caption": "Customer House Image"
  }
}
    )

def firebase_upload(details_dict):
    # Create a new booking document
    new_booking = {
        'Customer_ID': details_dict['customer_id'],
        'Customer_Name': details_dict['customer_name'],
        'Customer_Contact_Number': int(details_dict['customer_mobile_no']),
        'Image_ID': details_dict['customer_house_image_id'],
        "latitude": details_dict["customer_house_latitude"],
        "longitude": details_dict["customer_house_longitude"],
    }
    
    # Add the new booking to the 'bookings' collection
    db.collection('Customer_Info').add(new_booking)


async def generate_response(response,session,mess_type):
    global flow_flag, details_dict
    flow_flag = session.flow_flag
    details_dict = session.customer_data
    print(type(session))
    if mess_type != 'location' and response.lower() == 'restart':
        flow_flag = None
        output = """
Please enter
    1 for Add Customer Details
    2 for Search Customer Details"""
    elif flow_flag == 'status_confirmation':
        print(current_app.config['Manager_WAID'])
        if response == '1':
            delivery_status = f"""Deliver details:
Delivery Boy mobile number: {session.recipient_number} 
Delivery status: Delivered
Customer ID: {session.customer_data['customer_id']}
Customer Name: {session.customer_data['customer_name']}"""
            output = f""" Thank you for the status. The Owner will be notified"""
            data = get_text_message_input(current_app.config['Manager_WAID'], delivery_status)
            await send_message(data)
            flow_flag = None
        elif response == '2':
            delivery_status = f"""Deliver details:
Delivery Boy mobile number: {session.recipient_number} 
Delivery status: Not Delivered
Customer ID: {session.customer_data['customer_id']}
Customer Name: {session.customer_data['customer_name']}"""
            output = f""" Thank you for the status. The Owner will be notified"""
            data = get_text_message_input(current_app.config['Manager_WAID'], delivery_status)
            await send_message(data)
            flow_flag = None
        elif response == '3':
            delivery_status = f"""Deliver details:
Delivery Boy mobile number: {session.recipient_number} 
Delivery status: Customer Not Available
Customer ID: {session.customer_data['customer_id']}
Customer Name: {session.customer_data['customer_name']}"""
            output = f""" Thank you for the status. The Owner will be notified"""
            data = get_text_message_input(current_app.config['Manager_WAID'], delivery_status)
            await send_message(data)
            flow_flag = None
        elif response == '4':
            delivery_status = f"""Deliver details:
Delivery Boy mobile number: {session.recipient_number} 
Delivery status: Hold
Customer ID: {session.customer_data['customer_id']}
Customer Name: {session.customer_data['customer_name']}"""
            output = f""" Thank you for the status. The Owner will be notified"""
            data = get_text_message_input(current_app.config['Manager_WAID'], delivery_status)
            await send_message(data)
            flow_flag = None
        else:
            output = 'Please select from above choices'
        
    elif flow_flag == 'delivery_confirmation' and response == '1':
        flow_flag = 'status_confirmation' 
        output = f"""
Please enter the Status of the Delivery:
1 for Delivered
2 for Cancelled
3 for Customer Not Available
4 for Hold"""
    elif flow_flag == 'delivery_confirmation' and response == '2':
        flow_flag = None
        output = f"""Thank you for searching.
Please enter
    1 for Add Customer Details
    2 for Search Customer Details"""
    elif flow_flag == 'customer_search':
        customer_id = int(response)
        customer_db = db.collection('Customer_Info').where('Customer_ID', '==', customer_id).limit(1).get()
        if len(customer_db) == 0:
            output = f"""Customer ID: {customer_id} not found."""
        else:
            for customer in customer_db:
                customer_data = customer.to_dict()
            print(customer_data)
            session.search_data = customer_data
            output = f"""
Customer ID: {customer_data['Customer_ID']}
Customer Name: {customer_data['Customer_Name']}
Contact Number: {customer_data['Customer_Contact_Number']}

Please enter:
1 for Continue Delivery
2 for Back to search
"""
            flow_flag = 'delivery_confirmation'
    elif flow_flag == None and response == '2':
        flow_flag = 'customer_search'
        output = 'Please enter the Customer ID'
    elif flow_flag == 'add_customer_details' and response == '2':
        flow_flag = None
        output = f"""Customer Data has been erased successfully.
Please enter
    1 for Add Customer Details
    2 for Search Customer Details"""
    elif flow_flag == 'add_customer_details' and response == '1':
        firebase_upload(details_dict)
        flow_flag = None
        output = f"""Customer Data has been saved successfully.
Please enter
    1 for Add Customer Details
    2 for Search Customer Details"""
    elif flow_flag == 'customer_house_location': 
        details_dict['customer_house_latitude'] = response['latitude']
        details_dict['customer_house_longitude'] = response['longitude']
        customer_data = details_dict
        flow_flag = 'add_customer_details'
        output = """Please enter
1 to CONFIRM
2 to CANCEL"""
    elif flow_flag == 'customer_house_image_id':
        details_dict['customer_house_image_id'] = response
        flow_flag = 'customer_house_location'
        output = 'Please select the Customer House Location'
    elif flow_flag == 'customer_mobile_no':
        validate_result = _validate_contact_no(response)
        if not validate_result.is_valid:
            output = validate_result.message
        else:
            details_dict['customer_mobile_no'] = validate_result.value
            flow_flag = 'customer_house_image_id'
            output = 'Please select the Customer House Image'
    elif flow_flag == 'customer_name':
        validate_result = _validate_name(response)
        if not validate_result.is_valid:
            output = validate_result.message
        else:
            details_dict['customer_name'] = validate_result.value
            flow_flag = 'customer_mobile_no'
            output = 'Please enter the Customer Contact Number'
    elif flow_flag == 'customer_id':
        validate_result = _validate_customer_id(response)
        if not validate_result.is_valid:
            output = validate_result.message
        else:
            details_dict['customer_id'] = validate_result.value
            flow_flag = 'customer_name'
            output = 'Please enter the Customer Name'
    elif flow_flag == None and response == '1':
        output = 'Please enter the Customer ID'
        flow_flag = 'customer_id'
    elif flow_flag == None:
        output = """
Please enter
    1 for Add Customer Details
    2 for Search Customer Details"""
    
    session.flow_flag = flow_flag
    session.customer_data = details_dict
    # Return text in uppercase
    return output,session


async def send_message(data):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
    }
    url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/messages"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data, headers=headers) as response:
                response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
    except requests.Timeout:
        logging.error("Timeout occurred while sending message")
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except (requests.RequestException) as e:  # This will catch any general request exception
        logging.error(f"Request failed due to: {e}")
        return jsonify({"status": "error", "message": "Failed to send message"}), 500
    else:
        # Process the response as normal
        log_http_response(response)
        return response


def process_text_for_whatsapp(text):
    # Remove brackets
    pattern = r"\【.*?\】"
    # Substitute the pattern with an empty string
    text = re.sub(pattern, "", text).strip()

    # Pattern to find double asterisks including the word(s) in between
    pattern = r"\*\*(.*?)\*\*"

    # Replacement pattern with single asterisks
    replacement = r"*\1*"

    # Substitute occurrences of the pattern with the replacement
    whatsapp_style_text = re.sub(pattern, replacement, text)

    return whatsapp_style_text


async def process_whatsapp_message(body,recipient_number,session):
    print(session.flow_flag)
    # try:
    mess_type = body["entry"][0]["changes"][0]["value"]["messages"][0]['type']
    if session.flow_flag == 'customer_house_image_id':
        if mess_type == 'image':
            message = body["entry"][0]["changes"][0]["value"]["messages"][0]
            message_body = message['image']['id']
            response,session = await generate_response(message_body,session,mess_type)
        else:
            response = """Please Upload the image of the Customer's house properly."""
    elif session.flow_flag == 'customer_house_location':
        if mess_type == 'location':
            message = body["entry"][0]["changes"][0]["value"]["messages"][0]
            message_body = message['location']
            response,session = await generate_response(message_body,session,mess_type)
        else:
            response = """Please Upload the location of the Customer's house properly."""
    else:
        message = body["entry"][0]["changes"][0]["value"]["messages"][0]
        message_body = message["text"]["body"]
        response,session = await generate_response(message_body,session,mess_type)
    print('message_body:',message_body)
    print('recipient_number:',recipient_number)
    # TODO: implement custom function here
    

    # OpenAI Integration
    # response = generate_response(message_body, wa_id, name)
    # response = process_text_for_whatsapp(response)
    if session.flow_flag == 'add_customer_details':
        # sending text data
        output1 = f"""Customer details:
ID: {session.customer_data['customer_id']}
Name: {session.customer_data['customer_name']}
Contact Number: {session.customer_data['customer_mobile_no']}"""
        text_data = get_text_message_input(recipient_number, output1)
        await send_message(text_data)
        # sending location data
        lattitude = session.customer_data['customer_house_latitude']
        longitude = session.customer_data['customer_house_longitude']
        location_data = get_location_message_input(recipient_number, lattitude, longitude)
        await send_message(location_data)
        # sending image data
        image_id = session.customer_data['customer_house_image_id']
        image_data = get_image_message_input(recipient_number, image_id)
        await send_message(image_data)
        # sending text data
        data = get_text_message_input(recipient_number, response)
        await send_message(data)
    elif session.flow_flag == 'status_confirmation':
        # sending text data
        output1 = f"""Customer details:
ID: {session.search_data['Customer_ID']}
Name: {session.search_data['Customer_Name']}
Contact Number: {session.search_data['Customer_Contact_Number']}"""
        text_data = get_text_message_input(recipient_number, output1)
        await send_message(text_data)
        # sending location data
        lattitude = session.search_data['latitude']
        longitude = session.search_data['longitude']
        location_data = get_location_message_input(recipient_number, lattitude, longitude)
        await send_message(location_data)
        # sending image data
        image_id = session.search_data['Image_ID']
        image_data = get_image_message_input(recipient_number, image_id)
        await send_message(image_data)
        # sending text data
        data = get_text_message_input(recipient_number, response)
        await send_message(data)
    else:
        data = get_text_message_input(recipient_number, response)
        await send_message(data)
    print('session: ',session.flow_flag)
    return session
    # except Exception as e:
    #     print(3)
    #     print(e)
    #     return jsonify({"status": "error", "message": "Failed to send message"}), 500


def is_valid_whatsapp_message(body):
    """
    Check if the incoming webhook event has a valid WhatsApp message structure.
    """
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )

def _validate_name(user_input: str) -> ValidationResult:
    if not user_input:
        return ValidationResult(
            is_valid=False,
            message="Please enter a name that contains at least one character.",
        )

    return ValidationResult(is_valid=True, value=user_input)

def _validate_room_type(user_input: str) -> ValidationResult:
    if user_input not in ['1','2']:
        return ValidationResult(
            is_valid=False,
            message="Please select proper Room booking type from the options provided.",
        )
    else:
        if user_input == '1':
            user_input = 'Single Room'
        elif user_input == '2':
            user_input = 'Double Room'
        return ValidationResult(is_valid=True, value=user_input)

def _validate_booking_source(user_input: str) -> ValidationResult:
    if user_input.lower() not in ['booking.com','airbnb','others']:
        return ValidationResult(
            is_valid=False,
            message="Please select proper booking Source from the options provided.",
        )
    else:
        return ValidationResult(is_valid=True, value=user_input)

def _validate_contact_no(user_input: int) -> ValidationResult:
    if user_input.isdigit() == False:
        return ValidationResult(
            is_valid=False,
            message="Please provide a valid 10 digit number without Country Code.",
        )
    elif len(str(user_input)) != 10:
        return ValidationResult(
            is_valid=False,
            message="Please provide a valid 10 digit number without Country Code.",
        )

    return ValidationResult(is_valid=True, value=user_input)

def _validate_amount(user_input: int) -> ValidationResult:
    # Attempt to convert the Recognizer result to an integer. This works for "a dozen", "twelve", "12", and so on.
    # The recognizer returns a list of potential recognition results, if any.
    # results = recognize_number(user_input, Culture.English)
    # for result in results:
    #     if "value" in result.resolution:
    #         amount = int(result.resolution["value"])
    #         if 1 <= amount <= 5000000000:
    
    if user_input.isdigit() == False:
        return ValidationResult(
        is_valid=False, message="Please enter the amount properly."
        )
    elif int(user_input)< 0:
        return ValidationResult(
        is_valid=False, message="Please enter the amount properly."
        )
    return ValidationResult(is_valid=True, value = int(user_input))


def _validate_customer_id(user_input: int) -> ValidationResult:
    # Attempt to convert the Recognizer result to an integer. This works for "a dozen", "twelve", "12", and so on.
    # The recognizer returns a list of potential recognition results, if any.
    # results = recognize_number(user_input, Culture.English)
    # for result in results:
    #     if "value" in result.resolution:
    #         amount = int(result.resolution["value"])
    #         if 1 <= amount <= 5000000000:
    
    if user_input.isdigit() == False:
        return ValidationResult(
        is_valid=False, message="Please enter the Customer ID properly."
        )
    elif int(user_input)< 0:
        return ValidationResult(
        is_valid=False, message="Please enter the amount properly."
        )
    return ValidationResult(is_valid=True, value = int(user_input))

def _validate_age(user_input: str) -> ValidationResult:
    # Attempt to convert the Recognizer result to an integer. This works for "a dozen", "twelve", "12", and so on.
    # The recognizer returns a list of potential recognition results, if any.
    results = recognize_number(user_input, Culture.English)
    for result in results:
        if "value" in result.resolution:
            age = int(result.resolution["value"])
            if 18 <= age <= 120:
                return ValidationResult(is_valid=True, value=age)

    return ValidationResult(
        is_valid=False, message="Please enter an age between 18 and 120."
    )



def _validate_date(user_input: str) -> ValidationResult:
    try:
        # Try to recognize the input as a date-time. This works for responses such as "11/14/2018", "9pm",
        # "tomorrow", "Sunday at 5pm", and so on. The recognizer returns a list of potential recognition results,
        # if any.
        results = recognize_datetime(user_input, Culture.English)
        for result in results:
            for resolution in result.resolution["values"]:
                if "value" in resolution:
                    now = datetime.now()

                    value = resolution["value"]
                    if resolution["type"] == "date":
                        candidate = datetime.strptime(value, "%Y-%m-%d")
                    elif resolution["type"] == "time":
                        candidate = datetime.strptime(value, "%H:%M:%S")
                        candidate = candidate.replace(
                            year=now.year, month=now.month, day=now.day
                        )
                    else:
                        candidate = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")

                    # user response must be more than an hour out
                    diff = candidate - now
                    if diff.total_seconds() >= 3600:
                        return ValidationResult(
                            is_valid=True,
                            value=candidate.strftime("%d/%m/%y"),
                        )

        return ValidationResult(
            is_valid=False,
            message="I'm sorry, please enter a date at least an hour out.",
        )
    except ValueError:
        return ValidationResult(
            is_valid=False,
            message="I'm sorry, I could not interpret that as an appropriate "
            "date. Please enter a date at least an hour out.",
        )
    
    
def calculate_days(details_dict):
        start_date = datetime.strptime(details_dict['checkin_date'],'%m/%d/%y')
        end_date = datetime.strptime(details_dict['checkout_date'],'%m/%d/%y')
        delta = end_date - start_date
        return delta.days

def filter_by_dates(entries,date):
    filtered_entries = []
    for entry in entries:
        entry = entry.to_dict()
        checkin_date = entry['checkin_date'].date()
        checkin_date = checkin_date.strftime("%d/%m/%y")
        checkin_date = datetime.strptime(checkin_date, "%d/%m/%y")
        checkout_date = entry['checkout_date'].date()
        checkout_date = checkout_date.strftime( "%d/%m/%y")
        checkout_date = datetime.strptime(checkout_date, "%d/%m/%y")
        if checkin_date <= date <= checkout_date :
            filtered_entries.append(entry)
    return filtered_entries

# Function to query bookings by check-in date
def query_bookings_by_checkin_date(checkin_date_str):
    # Convert checkin_date from string to datetime object
    checkin_date = datetime.strptime(checkin_date_str, '%d/%m/%y')
    print('checkin_date: ', checkin_date)
    # Query bookings with the exact check-in date
    bookings = bookings = db.collection('bookings').where(filter=FieldFilter('checkin_date', '<=',checkin_date)).get()
    bookings = filter_by_dates(bookings,checkin_date)
#     output = f"""Date: {checkin_date_str}
# Client Name        : Stay Duration
# ------------------------------------"""
    output = f"""
Date   : {checkin_date_str}
Booked : {len(bookings)}
Vacant : {5-len(bookings)}
-------------------------------------"""
    # Print out the bookings
    for booking in bookings:
        booking_id = booking.get('booking_id')
        client_name = booking.get('name')
        stay_duration = (booking.get('checkout_date') - checkin_date.astimezone(booking.get('checkout_date').tzinfo)).days
        output = output + f"""
Booking ID: {booking_id}
Client Name : {client_name}
Stay Duration : {stay_duration}
------------------------------"""         
#         output = output + """
# """ +f"""{client_name}          : {stay_duration}days"""
#     output = output + f"""
# ------------------------------
# Booked  = {len(bookings)}
# Vacant  = {5-len(bookings)}"""
    output = output+"""

Please enter
1 for Add Bookings
2 for Update Bookings
3 for Summary"""
    return output

def query_bookings_by_month(month_str):
    # Convert dates from string to datetime objects
    # Parse the input date string
    date_obj = datetime.strptime(month_str, '%d/%m/%y')
    # Format it as '%m/%y'
    month_year = date_obj.strftime('%m/%y')
    print('month_year: ',month_year)
    days_lst = month_to_days(month_year)
    print('days_lst: ',days_lst)
    output = """"""
    for i in days_lst:
        out_day = query_bookings_by_checkin_date(i)
        output  = output + out_day + """
"""
    return output


def month_to_days(year_month):
    # Parse the input year_month (e.g., "05/24")
    month, year = map(int, year_month.split('/'))

    # Get the number of days in the specified month
    num_days = calendar.monthrange(year, month)[1]

    # Generate date strings for each day in the month
    date_list = [f"{day:02d}/{month:02d}/{year % 100:02d}" for day in range(1, num_days + 1)]

    return date_list

def get_last_booking_id():
    # Reference to the bookings collection
    bookings_ref = db.collection('bookings')

    # Query to get the last booking by ID
    last_booking_query = bookings_ref.order_by('booking_id', direction=firestore.Query.DESCENDING).limit(1)
    # Execute the query and get the last booking document
    last_booking = last_booking_query.stream()    
    for booking in last_booking:
        last_booking_dict = booking.to_dict()
        print('last_booking: ',last_booking_dict)
        if last_booking_dict is None:
            return 0
        else:
            last_booking_id = last_booking_dict.get('booking_id')
            print(f"The last booking ID is: {last_booking_id}")
            return last_booking_id
        
# Function to update a booking
def update_booking(booking_id):
    try:
        # Retrieve the booking document by ID
        booking_detail = db.collection('bookings').where('booking_id', '==' ,booking_id).limit(1).get()
        for x in booking_detail:
            booking_document_id = x.id
            print(x.to_dict())
            break
        # Retrieve the booking document by ID
        booking_ref = db.collection('bookings').document(booking_document_id)
        updated_data = {
        'booking_id': booking_id,
        'name': details_dict['client_name'],
        'number': int(details_dict['client_mobile_no']),
        'checkin_date': datetime.strptime(details_dict['checkin_date'], "%d/%m/%y"),
        'checkout_date': datetime.strptime(details_dict['checkout_date'], "%d/%m/%y"),
        'stay_duration': int(details_dict['stay_duration']),
        'per_day_charge': int(details_dict['tariff']),
        'booking_source': details_dict['booking_source'],
        'advance_paid': int(details_dict['advance_payment']),
        'total_amount': int(details_dict['total_amount']),
    }
        print(updated_data)
        # Update the fields in the booking document
        booking_ref.update(updated_data)
        return True
    except Exception as e:
        print('Error: ',e)
        return False