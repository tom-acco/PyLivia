from time import sleep
from modems.Olivia import OliviaModem

def callback(state = None, message = None):
    if state:
        print(f"State: {state}")

    if message:
        print(f"Received Message: {message}")

if __name__ == "__main__":
    ## Init the modem
    ol = OliviaModem(callback = callback)

    ## List the possible devices
    ol.listDevices()

    ## Print the config
    ol.getConfig()

    ## Start the modem
    ol.start()

    ## Send a test message
    ol.send("test")

    sleep(30)