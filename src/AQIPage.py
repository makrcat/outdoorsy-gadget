import displayio, terminalio
from my_utilities import *
from Page import Page
from adafruit_display_shapes.line import Line
from adafruit_display_text import label
from adafruit_display_shapes.rect import Rect
from fonts import PRAGATI_54, NINE_REG, NINE, SUBTEN


class eCO2(displayio.Group):
    def __init__(self, x, y):
        super().__init__(x=x, y=y)

        self.append(Rect(0, 0, 68, 42, fill=0x444444))
        self.append(Rect(0, 0, 68, 42, outline=0xFFFFFF))
        self.append(label.Label(NINE_REG, text="eCO2", color=0x52E5FF, anchor_point=(0.0, 0.0), 
                                     anchored_position=(4, 0), scale=1))
        
        self.eCO2_label = label.Label(NINE_REG, text="--", color=0x52E5FF, anchor_point=(0.0, 0.0), 
                                     anchored_position=(4, 16), scale=1)
        self.append(self.eCO2_label)

    def update(self, store):
        self.eCO2_label.text = f"{store.getVal("eCO2"):.0f}%"


class AQIArea(displayio.Group):
    def __init__(self, x, y):
        super().__init__(x=x, y=y)

        self.append(Rect(0, 0, 10, 10, fill=0x444444))
        self.aqi_label = label.Label(PRAGATI_54, text="-- dw", color=0xFFFFFF, anchor_point=(0.0, 0.0), 
                                     anchored_position=(0, 4), scale=1)
        self.append(self.aqi_label)
        

    def update(self, store):
        self.aqi_label.text = f"{store.getVal("aqi"):.1f}"

class DescriptionBox(displayio.Group):
    def __init__(self, x, y):
        super().__init__(x=x, y=y)
        self.append(Rect(0, 0, 86, 90, fill=0x444444))
        self.append(Rect(0, 0, 86, 90, outline=0xFFFFFF))

        self.header_label = label.Label(
            NINE, 
            text=wrap_text("Good AQ", 80, NINE), 
            color=0xEFBA0F, 
            line_spacing=0.8,
            anchor_point=(0.0, 0.0), 
            anchored_position=(5, 3), 
            scale=1
        )
        
        self.description_label = label.Label(
            SUBTEN, 
            text=wrap_text("Air quality is decent.", 80, SUBTEN), 
            line_spacing=1.0,
            color=0xFFFFFF, 
            anchor_point=(0.0, 0.0), 
            anchored_position=(5, 35), 
            scale=1
        )
        
        self.append(self.header_label)
        self.append(self.description_label)
        
    def update(self, store):
        pass
    
        




class AQIPage(Page):
    def __init__(self, store):
        super().__init__(header_text="Air Quality")
        self.store = store

        self.AQI_box = AQIArea(x=14, y=31)
        self.group.append(self.AQI_box)
        
        self.eCO2_box = eCO2(x=14, y=84)
        self.group.append(self.eCO2_box)
                
        self.description_box = DescriptionBox(x=142, y=132)
        self.group.append(self.description_box)
        
        
        self.graph_range = 10
        self.graph = DataGraph(xpos=14, ypos=132, width=122, height=90, group=self.group)
        
    def on_show(self):
        self.store.set_active_metric("aqi")

    def on_short_select(self):
        global DATA_RANGE
        current_index = DATA_RANGE.index(self.graph_range)
        next_index = (current_index + 1) % len(DATA_RANGE)
        self.graph_range = DATA_RANGE[next_index]
        
        

    def on_long_select(self):
        pass

    def on_short_next(self):
        pass 

    def update_page(self):
        self.eCO2_box.update(self.store)
        self.AQI_box.update(self.store)
            
    def data_schedule_update(self):
        readings = self.store.getVariableData()
        self.graph.draw_the_shit(readings.get_data_log(), readings.get_time_log(), self.graph_range)
