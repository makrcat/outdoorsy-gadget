import displayio
from my_utilities import *
from Page import Page
from adafruit_display_text import label
from fonts import PRAGATI_22, NINE_REG,SUBTEN
import gc
from theme import SMALL_BOX_BITMAP, DESC_BOX_BITMAP, BOX_PALETTE


class HumidityBox(displayio.Group):
    def __init__(self, x, y):
        super().__init__(x=x, y=y)
        self.bg_grid = displayio.TileGrid(SMALL_BOX_BITMAP, pixel_shader=BOX_PALETTE)
        self.append(self.bg_grid)
        
        self.append(label.Label(NINE_REG, text="Humid:", color=0x52E5FF, anchor_point=(0.0, 0.0), anchored_position=(4, 0), scale=1))
        
        self.hum_label = label.Label(NINE_REG, text="--%", color=0x52E5FF, anchor_point=(0.0, 0.0), anchored_position=(4, 16), scale=1)
        self.append(self.hum_label)

    def update(self, store):
        self.hum_label.text = f"{store.getVal('humidity'):.1f}%"


class DewBox(displayio.Group):
    def __init__(self, x, y):
        super().__init__(x=x, y=y)
        self.bg_grid = displayio.TileGrid(SMALL_BOX_BITMAP, pixel_shader=BOX_PALETTE)
        self.append(self.bg_grid)
        
        self.append(label.Label(NINE_REG, text="Dew pt:", color=0xA8FFA3, anchor_point=(0.0, 0.0), anchored_position=(4, 0), scale=1))
        
        self.dew_label = label.Label(NINE_REG, text="--C", color=0xA8FFA3, anchor_point=(0.0, 0.0), anchored_position=(4, 16), scale=1)
        self.append(self.dew_label)

    def update(self, store):
        self.dew_label.text = f"{store.getConvertedVal('dewpoint'):.1f}" + store.get_setting("temperature_unit")


class FLBox(displayio.Group):
    def __init__(self, x, y):
        super().__init__(x=x, y=y)
        self.bg_grid = displayio.TileGrid(SMALL_BOX_BITMAP, pixel_shader=BOX_PALETTE)
        self.append(self.bg_grid)
                
                
        self.append(label.Label(NINE_REG, text="Feels:", color=0xFF7DE5, anchor_point=(0.0, 0.0), anchored_position=(4, 0), scale=1))
        
        self.FL_label = label.Label(NINE_REG, text="--C", color=0xFF7DE5, anchor_point=(0.0, 0.0), anchored_position=(4, 16), scale=1)
        self.append(self.FL_label)

    def update(self, store):
        self.FL_label.text = f"{store.getConvertedVal('feels_like'):.1f}" + store.get_setting("temperature_unit")


class TempArea(displayio.Group):
    def __init__(self, x, y):
        super().__init__(x=x, y=y)
        
        self.temp_label = label.Label(PRAGATI_22, text="--", color=0xFFFFFF, anchor_point=(0.0, 0.0), anchored_position=(0, 6), scale=2)
        self.append(self.temp_label)

    def update(self, store):
        self.temp_label.text = f"{store.getConvertedVal('temperature'):.1f}" + store.get_setting("temperature_unit")


class TamagotchiArea(displayio.Group):
    def __init__(self, x, y):
        super().__init__(x=x, y=y)
        
        self.emoticon_label = label.Label(PRAGATI_22, text="(>_<)", color=0xFFFFFF, anchor_point=(0.0, 0.0), anchored_position=(0, 4), scale=2)
        self.append(self.emoticon_label)

    def update(self, store):
        self.emoticon_label.text = "(>_<)" 


def weather_cat(temp):
    if temp > 35: return 5
    elif temp > 27: return 4
    elif temp > 18: return 3
    elif temp > 5: return 2
    elif temp > -9: return 1
    else: return 0

pinfo = [
    ("Freezing", "Dangerously cold, wear many layers of clothes."),
    ("Cold", "Cold weather, watch for wind! Drink some warm water."),
    ("Cool", "Crisp and refreshing weather, and a jacket will do."),
    ("Nice", "It's comfortable weather, good for strolling outdoors."),
    ("Hot!", "It's very hot, make sure to drink lots of water!"), 
    ("Scorching", "Risk of heat stroke, try to stay in the shade or inside.")
]


class DescriptionBox(displayio.Group):
    def __init__(self, x, y):
        super().__init__(x=x, y=y)
        self.bg_grid = displayio.TileGrid(DESC_BOX_BITMAP, pixel_shader=BOX_PALETTE)
        self.append(self.bg_grid)
     
        self.header_label = label.Label(
            NINE_REG, text="----", color=0xEFBA0F, line_spacing=0.8,
            anchor_point=(0.0, 0.0), anchored_position=(5, 3), scale=1
        )
        
        self.description_label = label.Label(
            SUBTEN, text="Loading", line_spacing=1.0,
            color=0xFFFFFF, anchor_point=(0.0, 0.0), anchored_position=(5, 25), scale=1
        )
        
        self.append(self.header_label)
        self.append(self.description_label)


        self.last_cat = None
        
    def update(self, store):
        temp = store.getVal("temperature")
        cat = weather_cat(temp)
        
        if cat != self.last_cat:
            gc.collect() 
            
            self.header_label.text = pinfo[cat][0]
            self.description_label.text = wrap_text(pinfo[cat][1], 82, SUBTEN)
            self.last_cat = cat


class TemperaturePage(Page):
    def __init__(self, store):
        super().__init__(header_text="Temperature")
        self.store = store

        self.temp_box = TempArea(x=14, y=31)
        self.group.append(self.temp_box)
        self.tamagotchi_box = TamagotchiArea(x=150, y=31)
        self.group.append(self.tamagotchi_box)
        
        self.humidity_box = HumidityBox(x=14, y=84)
        self.group.append(self.humidity_box)
        self.dew_box = DewBox(x=87, y=84)
        self.group.append(self.dew_box)
        self.FL_box = FLBox(x=160, y=84)
        self.group.append(self.FL_box)
        
        self.description_box = DescriptionBox(x=142, y=132)
        self.group.append(self.description_box)
        
        self.graph_range = 10
        self.graph = DataGraph(xpos=14, ypos=132, width=122, height=90, group=self.group)
        
    def on_show(self):
        self.store.set_active_metric("temperature")

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
        self.humidity_box.update(self.store)
        self.temp_box.update(self.store)
        self.dew_box.update(self.store)
        self.FL_box.update(self.store)
        self.description_box.update(self.store)

            
    def data_schedule_update(self):
        readings = self.store.getVariableData()
        self.graph.draw_the_shit(
            readings.get_data_log(),
            self.store.get_setting("interval"),
            self.graph_range
        )