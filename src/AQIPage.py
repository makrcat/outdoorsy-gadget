import displayio
from my_utilities import *
from Page import Page
from adafruit_display_text import label
from fonts import NINE_REG, SUBTEN, PRAGATI_22
from theme import SMALL_BOX_BITMAP, DESC_BOX_BITMAP, BOX_PALETTE
import gc

class eCO2(displayio.Group):
    def __init__(self, x, y):
        super().__init__(x=x, y=y)

        self.bg_grid = displayio.TileGrid(SMALL_BOX_BITMAP, pixel_shader=BOX_PALETTE)
        self.append(self.bg_grid)
                
        self.append(label.Label(NINE_REG, text="eCO2", color=0x52E5FF, anchor_point=(0.0, 0.0), 
                                     anchored_position=(4, 0), scale=1))
        
        self.eCO2_label = label.Label(NINE_REG, text="--", color=0x52E5FF, anchor_point=(0.0, 0.0), 
                                     anchored_position=(4, 16), scale=1)
        self.append(self.eCO2_label)

    def update(self, store):
        self.eCO2_label.text = f"{store.getVal('eCO2'):.0f}"


class AQIArea(displayio.Group):
    def __init__(self, x, y):
        super().__init__(x=x, y=y)
        self.aqi_label = label.Label(PRAGATI_22, text="--", color=0xFFFFFF, anchor_point=(0.0, 0.0), 
                                     anchored_position=(0, 6), scale=2)
        self.append(self.aqi_label)
        

    def update(self, store):
        self.aqi_label.text = f"{store.getVal('aqi'):.1f}"


def aqi_cat(aqi):
    if aqi > 300: return 4
    elif aqi > 200: return 3
    elif aqi > 150: return 2
    elif aqi > 100: return 1
    else: return 0

pinfo = [
    ("Good", "Air quality is pretty good!"),
    ("Moderate", "Air quality is okay; some people might be sensitive."),
    ("Unhealthy+", "Members of sensitive groups may experience health effects."),
    ("Very bad", "Wear a mask! Everyone is likely to experience effects."),
    ("Terrible", "Pretty catastrophic air quality, don't go outside.")
]


class DescriptionBox(displayio.Group):
    def __init__(self, x, y):
        super().__init__(x=x, y=y)
        
        self.bg_grid = displayio.TileGrid(DESC_BOX_BITMAP, pixel_shader=BOX_PALETTE)
        self.append(self.bg_grid)

        self.header_label = label.Label(
            NINE_REG, 
            text="----",
            color=0xEFBA0F, 
            line_spacing=0.8,
            anchor_point=(0.0, 0.0), 
            anchored_position=(5, 3), 
            scale=1
        )
        
        self.description_label = label.Label(
            SUBTEN, 
            text="Loading",
            line_spacing=1.0,
            color=0xFFFFFF, 
            anchor_point=(0.0, 0.0), 
            anchored_position=(5, 25), 
            scale=1
        )
        
        self.append(self.header_label)
        self.append(self.description_label)
        
        self.last_cat = None
        
    def update(self, store):
        aqi_val = store.getVal("aqi")
        cat = aqi_cat(aqi_val)
        
        if cat != self.last_cat:
            gc.collect()
            
            self.header_label.text = pinfo[cat][0]
            self.description_label.text = wrap_text(pinfo[cat][1], 82, SUBTEN)
            self.last_cat = cat
    

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
        self.description_box.update(self.store)
        
        gc.collect()
            
    def data_schedule_update(self):
        readings = self.store.getVariableData()
        self.graph.draw_the_shit(
            readings.get_data_log(),
            self.store.get_setting("interval"),
            self.graph_range
        )