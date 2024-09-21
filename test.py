from time import sleep
from modems.Olivia import OliviaModem

def callback(state):
    print(state)

if __name__ == "__main__":
    ol = OliviaModem(callback=callback)
    ol.send("test")

    sleep(10)