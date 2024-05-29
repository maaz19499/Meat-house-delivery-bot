import logging
from flask import current_app, jsonify
import json
import requests
from recognizers_number import recognize_number, Culture
from recognizers_date_time import recognize_datetime
from datetime import date,datetime
# from app.services.openai_service import generate_response
import re

Details_empty_dict = {'client_name':'','client_mobile_no':'','checkin_date':'',
                'checkout_date':'','room_type':'','booking_source':'',
                'tariff':'','total_amount':'','advance_payment':'','balance':''}
details_dict = Details_empty_dict.copy()
flow_flag = None
edit_flag = None



class ValidationResult:
    def __init__(
        self, is_valid: bool = False, value: object = None, message: str = None
    ):
        self.is_valid = is_valid
        self.value = value
        self.message = message

def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")


def get_text_message_input(recipient, text):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to":current_app.config['RECIPIENT_WAID'],
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
    )

def edit_func(response,flow_flag,edit_flag,details_dict):
    print('inside edit func')
    output = 200
    if flow_flag == 'edit' and edit_flag == 'name':
        validate_result = _validate_name(response)
        if not validate_result.is_valid:
            output = validate_result.message
        else:
            details_dict['client_name'] = validate_result.value
            flow_flag = 'final_confirmation'
    elif flow_flag == 'edit' and edit_flag == 'contact_no':
        validate_result = _validate_contact_no(response)
        if not validate_result.is_valid:
            output = validate_result.message
        else:
            details_dict['client_mobile_no'] = validate_result.value
            flow_flag = 'final_confirmation'
    elif flow_flag == 'edit' and edit_flag == 'checkin_date':
        validate_result = _validate_date(details_dict,response)
        if not validate_result.is_valid:
            output = validate_result.message
        else:
            details_dict['checkin_date'] = validate_result.value
            details_dict['total_amount'] = calculate_days(details_dict) * details_dict['tariff']
            details_dict['balance'] = details_dict['total_amount'] - details_dict['advance_payment']
            flow_flag = 'final_confirmation'
    elif flow_flag == 'edit' and edit_flag == 'checkout_date':
        validate_result = _validate_date(details_dict,response)
        if not validate_result.is_valid:
            output = validate_result.message
        else:
            details_dict['checkout_date'] = validate_result.value
            details_dict['total_amount'] = calculate_days(details_dict) * details_dict['tariff']
            details_dict['balance'] = details_dict['total_amount'] - details_dict['advance_payment']
            flow_flag = 'final_confirmation'
    elif flow_flag == 'edit' and edit_flag == 'room_type':
        validate_result = _validate_room_type(response)
        if not validate_result.is_valid:
            output = validate_result.message
        else:
            details_dict['room_type'] = validate_result.value
            flow_flag = 'final_confirmation'
    elif flow_flag == 'edit' and edit_flag == 'booking_source':
        validate_result = _validate_booking_source(response)
        if not validate_result.is_valid:
            output = validate_result.message
        else:
            details_dict['booking_source'] = validate_result.value
            flow_flag = 'final_confirmation'
    elif flow_flag == 'edit' and edit_flag == 'tariff':
        validate_result = _validate_amount(response)
        if not validate_result.is_valid:
            output = validate_result.message
        else:
            details_dict['tariff'] = validate_result.value
            details_dict['total_amount'] = calculate_days(details_dict) * details_dict['tariff']
            details_dict['balance'] = details_dict['total_amount'] - details_dict['advance_payment']
            flow_flag = 'final_confirmation'
    elif flow_flag == 'edit' and edit_flag == 'advance_payment':
        validate_result = _validate_amount(response)
        if not validate_result.is_valid:
            output = validate_result.message
        else:
            details_dict['advance_payment'] = validate_result.value
            details_dict['total_amount'] = calculate_days(details_dict) * details_dict['tariff']
            details_dict['balance'] = details_dict['total_amount'] - details_dict['advance_payment']
            flow_flag = 'final_confirmation'            
    if output != 200:
        return output
    else:
        edit_flag = None
        return output,flow_flag,edit_flag,details_dict

def generate_response(response):
    global flow_flag, edit_flag, details_dict

    if flow_flag == 'edit' and edit_flag == None:
        if response == '1':
            output = "Please enter the name."
            edit_flag = 'name'
        elif response == '2':
            output = "Please enter the contact number."
            edit_flag = 'contact_no'
        elif response == '3':
            output = "Please enter the checkin date."
            edit_flag = 'checkin_date'
        elif response == '4':
            output = "Please enter the checkout date."
            edit_flag = 'checkout_date'
        elif response == '5':
            output = """Please enter the Room type:
    Enter 1 for Single Room
    Enter 2 for Double Room"""
            edit_flag = 'room_type'
        elif response == '6':
            output = '''Please enter the source of booking:
    Enter 1 for Booking.com
    Enter 2 for Airbnb
    Enter 3 for Others'''
            edit_flag = 'booking_source'
        elif response == '7':
            output = "Please enter the Per-day Charge."
            edit_flag = 'tariff'
        elif response == '8':
            output = "Please enter the Advance Payment."
            edit_flag = 'advance_payment'
        else:
            output = "Please select from above choice only."

    elif flow_flag == 'final_confirmation' and edit_flag == None:
        print('edit_flag:', edit_flag)
        if response == '1':
           output = """Usman bhai aapka Data save hochuka hai
           Enter start to get started"""
           flow_flag = None
           edit_flag = None
        elif response == '2':
            output = """Usman bhai aapka Data mita diya gaya hai
            Enter start to get started"""
            flow_flag = None
            edit_flag = None
        elif response == '3':
            output = """Usman bhai 
    Enter 1 to Edit Name
    Enter 2 to Edit Contact Number
    Enter 3 to Edit Checkin Date
    Enter 4 to Edit Checkout Date
    Enter 5 to Edit Room Type
    Enter 6 to Edit Booking Source
    Enter 7 to Edit Tariff
    Enter 8 to Edit Advance Payment"""
            flow_flag = "edit"
            print('edit_flag:', edit_flag)
            print('flow_flag:', flow_flag)
        else:
            output = "Please select from above choice only."       
    elif flow_flag =='advance_payment':
        validate_result = _validate_amount(response)
        if not validate_result.is_valid:
            output = validate_result.message
        else:
            details_dict['advance_payment'] = validate_result.value
            details_dict['total_amount'] = calculate_days(details_dict) * details_dict['tariff']
            details_dict['balance'] = details_dict['total_amount'] - details_dict['advance_payment']
            output = f"""
    Details:
    Client's Name:   {details_dict['client_name']}
    Contact Number:  {details_dict['client_mobile_no']}     
    Check in date:   {details_dict['checkin_date']}
    Check out date:  {details_dict['checkout_date']}
    Room Type:       {details_dict['room_type']}
    Booking Source:  {details_dict['booking_source']}
    Per-day Charge:  {details_dict['tariff']}
    Advance payment: {details_dict['advance_payment']}
    Total Amount:    {details_dict['total_amount']}
    Balance:         {details_dict['balance']}

    Enter 1 for CONFIRMATION
    Enter 2 for CANCEL
    Enter 3 for EDIT""" 
            flow_flag = 'final_confirmation'
    elif flow_flag == 'tariff':
        validate_result = _validate_amount(response)
        if not validate_result.is_valid:
            output = validate_result.message
        else:
            details_dict['tariff'] = validate_result.value
            output = 'Please enter the amount client has paid as Advance payment:'
            flow_flag = 'advance_payment'
    elif flow_flag == 'booking_source':
        validate_result = _validate_booking_source(response)
        if not validate_result.is_valid:
            output = validate_result.message
        else:
            details_dict['booking_source'] = validate_result.value
            output = 'Please enter the Per day charge for the selected Room type:'
            flow_flag = 'tariff'
    elif flow_flag == 'room_type':
        validate_result = _validate_room_type(response)
        if not validate_result.is_valid:
            output = validate_result.message
        else:
            details_dict['room_type'] = validate_result.value
            output = '''Please enter the source of booking:
    Enter 1 for Booking.com
    Enter 2 for Airbnb
    Enter 3 for Others'''
            flow_flag = 'booking_source'
    elif flow_flag == 'checkout_date':
        validate_result = _validate_date(details_dict,response)
        if not validate_result.is_valid:
            output = validate_result.message
        else:
            details_dict['checkout_date'] = validate_result.value
            output = """Please enter the Room type:
    Enter 1 for Single Room
    Enter 2 for Double Room"""
            flow_flag = 'room_type'
    elif flow_flag == 'checkin_date':
        validate_result = _validate_date(details_dict,response)
        if not validate_result.is_valid:
            output = validate_result.message
        else:
            details_dict['checkin_date'] = validate_result.value
            output = 'Please enter the Checkout Date:'
            flow_flag = 'checkout_date'
    elif flow_flag == 'client_mobile_no':
        validate_result = _validate_contact_no(response)
        if not validate_result.is_valid:
            output = validate_result.message
        else:
            details_dict['client_mobile_no'] = validate_result.value
            output = 'Please enter the Checkin Date:'
            flow_flag = 'checkin_date'
    elif flow_flag == 'client_name':
        validate_result = _validate_name(response)
        if not validate_result.is_valid:
            output = validate_result.message
        else:
            details_dict['client_name'] = validate_result.value
            output = 'Please enter the Clients Mobile Number:'
            flow_flag = 'client_mobile_no'
    elif flow_flag == None and response.lower() == "start":
        output = 'Please enter the Clients Name:'
        flow_flag = 'client_name'

    elif flow_flag == None:
        output = 'Please enter start to get started'
    
    elif flow_flag == 'edit' and edit_flag in ['name','contact_no','checkin_date','checkout_date','room_type','booking_type','tariff','advance_payment']:
        print('inside edit flag')
        output,flow_flag,edit_flag,details_dict = edit_func(response, flow_flag,edit_flag,details_dict)
        print(type(output))
        print(output)
        if output == 200:
            output = f"""
    Details:
    Client's Name:   {details_dict['client_name']}
    Contact Number:  {details_dict['client_mobile_no']}     
    Check in date:   {details_dict['checkin_date']}
    Check out date:  {details_dict['checkout_date']}
    Room Type:       {details_dict['room_type']}
    Booking Source:  {details_dict['booking_source']}
    Per-day Charge:  {details_dict['tariff']}
    Advance payment: {details_dict['advance_payment']}
    Total Amount:    {details_dict['total_amount']}
    Balance:         {details_dict['balance']}

    Enter 1 for CONFIRMATION
    Enter 2 for CANCEL
    Enter 3 for EDIT"""
            
        else:
            output = output
    
    # Return text in uppercase
    return output


def send_message(data):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
    }
    print('headers:', headers)
    url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/messages"
    print('url:', url)
    try:
        # async with session.post(url, data=data, headers=headers) as response:
        response = requests.post(
            url, data=data, headers=headers, timeout=10
        )  # 10 seconds timeout as an example
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


def process_whatsapp_message(body):
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]

    message = body["entry"][0]["changes"][0]["value"]["messages"][0]
    message_body = message["text"]["body"]
    print(message_body)

    # TODO: implement custom function here
    response = generate_response(message_body)

    # OpenAI Integration
    # response = generate_response(message_body, wa_id, name)
    # response = process_text_for_whatsapp(response)

    data = get_text_message_input(current_app.config["RECIPIENT_WAID"], response)
    send_message(data)


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
    if user_input not in ['1','2','3']:
        return ValidationResult(
            is_valid=False,
            message="Please select proper boooking Source from the options provided.",
        )
    else:
        if user_input == '1':
            user_input = 'Booking.com'
        elif user_input == '2':
            user_input = 'Airbnb'
        elif user_input == '3':
            user_input = 'Others'
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

def _validate_date(details_dict, user_input: str) -> ValidationResult:
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
                    candidate = candidate.replace(year = now.year) 
                    print(now.year)
                    diff = candidate - now
                    if len(details_dict['checkin_date'])> 0:
                        print('checkout_date:', candidate)
                        print('checkin_date_type:', type(candidate))
                        start_date = datetime.strptime(details_dict['checkin_date'],'%m/%d/%y')
                        end_date = candidate
                        delta = end_date - start_date
                        print(delta.days)
                        if delta.days > 0:
                            return ValidationResult(
                            is_valid=True,
                            value=candidate.strftime("%m/%d/%y"),
                        )
                        else:
                            return ValidationResult(
                            is_valid=False,
                            message="Please enter checkout date greater than Checkin date",
                        )
                    else:
                        if diff.total_seconds() >= 3600:
                            return ValidationResult(
                                is_valid=True,
                                value=candidate.strftime("%m/%d/%y"),
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
    
