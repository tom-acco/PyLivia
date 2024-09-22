import os
from dotenv import load_dotenv

from textual.app import App
from textual.containers import Grid
from textual.reactive import reactive
from textual.widgets import Input, Label, OptionList

from modems.Olivia import OliviaModem

## Load environment file
load_dotenv()

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
            input_device = os.getenv("INPUT_DEVICE", None),
            output_device = os.getenv("INPUT_DEVICE", None),
            sample_rate = os.getenv("SAMPLE_RATE", 8000),
            attenuation = os.getenv("ATTENUATION", 30),
            centre_freq = os.getenv("CENTRE_FREQ", 1500),
            symbols = os.getenv("SYMBOLS", 32),
            bandwidth = os.getenv("BANDWIDTH", 1000),
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