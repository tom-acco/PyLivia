# PyLivia
A Python chat application implementing the [Olivia](https://en.wikipedia.org/wiki/Olivia_MFSK) protocol.

# Setup
## Install
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Device Listing
```bash
python -m sounddevice
```

## Environment File
.env
```bash
## RIGCTL
RIG_FILE = "/dev/tty.usbmodem58910155343"
RIG_MODEL = 3087

## AUDIO DEVICES
## Id (Int) of device from `python -m sounddevice`
## Comment out to use default
#INPUT_DEVICE = 0
#OUTPUT_DEVICE = 0

## SAMPLE RATE
SAMPLE_RATE = 8000

## ATTENUATION
ATTENUATION = 30

## CENTRE FREQ
CENTRE_FREQ = 1500

## SYMBOLS
SYMBOLS = 32

## BANDWIDTH
BANDWIDTH = 1000
```

# Credits
[sntfrc/olivia-python](https://github.com/sntfrc/olivia-python)