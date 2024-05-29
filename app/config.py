import sys
import os
from dotenv import load_dotenv
import logging


FIREBASE_CRED_PATH = 'app/utils/firebase_cred/airbnbbot-usmaanclient-firebase-adminsdk-obzqc-78e56060b5.json'




def load_configurations(app):
    app.config["ACCESS_TOKEN"] = ACCESS_TOKEN
    app.config["YOUR_PHONE_NUMBER"] = 'YOUR_PHONE_NUMBER'
    app.config["APP_ID"] = APP_ID
    app.config["APP_SECRET"] = APP_SECRET
    app.config["RECIPIENT_WAID"] = RECIPIENT_WAID
    app.config["VERSION"] = VERSION
    app.config["PHONE_NUMBER_ID"] = PHONE_NUMBER_ID
    app.config["VERIFY_TOKEN"] = VERIFY_TOKEN
    app.config["Manager_WAID"] = Manager_WAID



def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
