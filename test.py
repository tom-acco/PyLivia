from modems.Olivia import OliviaModem

if __name__ == "__main__":
    ol = OliviaModem()
    ol.send("test")

    while True:
        pass