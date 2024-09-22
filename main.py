from textual.app import App
from textual.containers import Grid
from textual.reactive import reactive
from textual.widgets import Input, Label, OptionList

from modems.Olivia import OliviaModem

## AUDIO DEVICES
## None for default
## Id (Int) of device from Olivia.listDevices()
INPUT_DEVICE = None
OUTPUT_DEVICE = None

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

class ModemStatus(Label):
    state = reactive("")
    def render(self):
        return self.state

class AppDisplay(App):
    line_count = 0

    def compose(self):
        yield Grid(
            OptionList(),
            Input(id = "message", placeholder = "Message")
        )
        yield ModemStatus()

    def on_mount(self):
        self.olivia = OliviaModem(
            input_device = INPUT_DEVICE,
            output_device = OUTPUT_DEVICE,
            sample_rate = SAMPLE_RATE,
            attenuation = ATTENUATION,
            centre_freq = CENTRE_FREQ,
            symbols = SYMBOLS,
            bandwidth = BANDWIDTH,
            callback = self.oliviaCallback
        )
        self.olivia.start()

        def handle_submit():
            message = str(message_input.value)
            message_input.value = ""

            self.olivia.send(message)
            self.add_message(str(f"TX: {message}"))

        dest_input = self.query(Input).first()
        dest_input.focus()

        message_input = self.query(Input).last()
        message_input.action_submit = handle_submit

    def add_message(self, message):
        self.line_count += 5
        self.query_one(OptionList).add_option(message)
        self.query_one(OptionList).scroll_to(y = self.line_count)

    def oliviaCallback(self, state = None, message = None):
        if state:
            self.query_one(ModemStatus).state = state

        if message:
            self.add_message(f"RX: {message}")

if __name__ == "__main__":
    app = AppDisplay(css_path="style.tcss")
    app.run()