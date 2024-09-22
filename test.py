from time import sleep
from modems.Olivia import OliviaModem

def callback(state = None, message = None):
    if state:
        print(f"State: {state}")

    if message:
        print(f"Received Message: {message}")

if __name__ == "__main__":
    ol = OliviaModem(callback = callback)

    ol.send("test")

    sleep(20)