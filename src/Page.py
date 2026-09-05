import displayio, terminalio
from adafruit_display_text import label
from fonts import NINE

class Page():
    def __init__(self, header_text=""):
        self.header_text = header_text
        self.group = displayio.Group(x=0, y=0)
        self.in_select_mode = False

        self.header_label = label.Label(NINE, text=header_text, color=0xFFFFFF, x=5, y=8)
        self.group.append(self.header_label)
    
    def on_show(self):
        pass

    def set_header(self, text):
        self.header_label.text = text

    def on_short_select(self):
        pass

    def on_long_select(self):
        pass
    
    def on_short_next(self):
        pass
    
    def update_page(self):
        pass

    def data_schedule_update(self):
        pass
