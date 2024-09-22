import os
from dotenv import load_dotenv

from time import sleep
from modems.Olivia import OliviaModem

## Load environment file
load_dotenv()

def callback(state = None, message = None):
    if state:
        print(f"State: {state}")

    if message:
        print(f"Received Message: {message}")

if __name__ == "__main__":
    ## Init the modem
    ol = OliviaModem(
        input_device = os.getenv("INPUT_DEVICE", None),
        output_device = os.getenv("OUTPUT_DEVICE", None),
        sample_rate = os.getenv("SAMPLE_RATE", 8000),
        attenuation = os.getenv("ATTENUATION", 30),
        centre_freq = os.getenv("CENTRE_FREQ", 1500),
        symbols = os.getenv("SYMBOLS", 32),
        bandwidth = os.getenv("BANDWIDTH", 1000),
        callback = callback
    )

    ## Print the config
    ol.getConfig()

    ## Start the modem
    ol.start()

    ## Send a test message
    ol.send("test")

    sleep(30)