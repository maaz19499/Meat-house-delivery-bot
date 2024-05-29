import sys
import os
from dotenv import load_dotenv
import logging


FIREBASE_CRED_PATH = 'app/utils/firebase_cred/airbnbbot-usmaanclient-firebase-adminsdk-obzqc-78e56060b5.json'

ACCESS_TOKEN="EABpkf677ZBeoBO036aTJbq0FA65P8Q6bN6QgwEEAOf0aPdaUKHeiA2qVA2fnIQ8icyONvpQfs2JVUY92lptdvip74NV3BvFO8fxu9m8VrTZBNhJGa5PTqyo4lGuLkKGYjeaTNOfoHA7xcyhhj1cKkvNixzMAqCmy85X3mqZCsbZCPcgCTCFgnCYwYlfJBVBYBnXGzWjVP2RMfWEuDUoZD"

APP_ID="7428848953850346"
APP_SECRET="538fd8b469754edf682fff536303a9b1"
RECIPIENT_WAID="+919945657981"
VERSION="v19.0"
PHONE_NUMBER_ID="290500427483399"
VERIFY_TOKEN="project_novus"
Manager_WAID = "917338006388"


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
