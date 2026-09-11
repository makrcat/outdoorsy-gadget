import displayio
from my_utilities import *
from Page import Page
from theme import SMALL_BOX_BITMAP, DESC_BOX_BITMAP, BOX_PALETTE
from adafruit_display_text import label
from fonts import NINE, SUBTEN, PRAGATI_54, NINE_BOLD
import gc

class PressureArea(displayio.Group):
    def __init__(self, x, y):
        super().__init__(x=x, y=y)
        
        self.bg_grid = displayio.TileGrid(SMALL_BOX_BITMAP, pixel_shader=BOX_PALETTE)
        self.append(self.bg_grid)
        
        self.append(label.Label(NINE, text="Pressur", color=0xFF9952, anchor_point=(0.0, 0.0), 
                                        anchored_position=(4, 0), scale=1))
        
        self.pressure_label = label.Label(NINE, text="---- hPa", color=0xFF9952, anchor_point=(0.0, 0.0), 
                                        anchored_position=(4, 16), scale=1)
        self.append(self.pressure_label)
                
    def update(self, store):
        self.pressure_label.text = f"{store.getVal('pressure'):.1f}"


class BoilBox(displayio.Group):
    def __init__(self, x, y):
        super().__init__(x=x, y=y)
        self.bg_grid = displayio.TileGrid(SMALL_BOX_BITMAP, pixel_shader=BOX_PALETTE)
        self.append(self.bg_grid)
        
        self.append(label.Label(NINE, text="Boiling", color=0x52E5FF, anchor_point=(0.0, 0.0), 
                                                anchored_position=(4, 0), scale=1))
                
        self.boil_label = label.Label(NINE, text="----", color=0x52E5FF, anchor_point=(0.0, 0.0), 
                                        anchored_position=(4, 16), scale=1)
        
        self.append(self.boil_label)

    def update(self, store):
        self.boil_label.text = f"{store.getConvertedVal('boiling_point'):.1f}" + store.get_setting("temperature_unit")
        
        
class HILOBox(displayio.Group):
    def __init__(self, x, y):
        super().__init__(x=x, y=y)

        self.bg_grid = displayio.TileGrid(SMALL_BOX_BITMAP, pixel_shader=BOX_PALETTE)
        self.append(self.bg_grid)
                
                
        self.append(label.Label(NINE, text="PsrLvl", color=0xFF7DE5, anchor_point=(0.0, 0.0), 
                                             anchored_position=(4, 0), scale=1))
        
        self.HILO_label = label.Label(NINE, text="----", color=0xFF7DE5, anchor_point=(0.0, 0.0), 
                                     anchored_position=(4, 16), scale=1)
        self.append(self.HILO_label)

    def update(self, store):
        prsr = ["V LOW", "LOW", "NORMAL", "HIGH", "V HIGH"]
        self.HILO_label.text = prsr[store.getConvertedVal('pressure_category')]


pinfo = [
    ("Stormy Weather", "Very unstable weather! Severe storms and winds are imminent."),
    ("Unstable Weather", "Unstable weather. Be ready for light wind and rain!"),
    ("Regular Weather", "Very regular and fair weather. Expect clouds and some sun."),
    ("Clear Skies", "Stable weather. Expect dry air, clear skies, and sunshine."),
    ("Sky high", "Stable weather, but intense cold or heat depending on season.")
]
        
class DescriptionBox(displayio.Group):
    def __init__(self, x, y):
        super().__init__(x=x, y=y)
        self.bg_grid = displayio.TileGrid(DESC_BOX_BITMAP, pixel_shader=BOX_PALETTE)
        self.append(self.bg_grid)
     
        self.header_label = label.Label(
            NINE_BOLD, text="----", color=0xEFBA0F, line_spacing=0.8,
            anchor_point=(0.0, 0.0), anchored_position=(5, 3), scale=1
        )
        
        self.description_label = label.Label(
            SUBTEN, text=wrap_text("Loading", 80, SUBTEN), line_spacing=1.05,
            color=0xFFFFFF, anchor_point=(0.0, 0.0), anchored_position=(5, 30), scale=1
        )
        
        self.append(self.header_label)
        self.append(self.description_label)
        

        self.last_cat = None
        
    def update(self, store):
        cat = store.getVal("pressure_category")
        
        # only re-wrap text if the pressure category actually changes
        if cat != self.last_cat:
            
            gc.collect()
            self.header_label.text = wrap_text(pinfo[cat][0], 82, NINE_BOLD)
            
            descy = wrap_pos(self.header_label.text, 25, 35)
            
            self.description_label.text = wrap_text(pinfo[cat][1], 82, SUBTEN)
            self.description_label.anchored_position = (5, descy)
            self.last_cat = cat


class AltitudeArea(displayio.Group):
    def __init__(self, x, y):
        super().__init__(x=x, y=y)
        
        self.altitude_label = label.Label(PRAGATI_54, text="--", color=0xFFFFFF, anchor_point=(0.0, 0.0), 
                                     anchored_position=(0, 6), scale=1)
        self.append(self.altitude_label)
        
    def update(self, store):
        self.altitude_label.text = f"{store.getConvertedVal('altitude'):.1f}" + store.get_setting("measurement_unit")


class PressurePage(Page):
    def __init__(self, store):
        super().__init__(header_text="Barometer")
        self.store = store
        
        self.pressure_box = PressureArea(x=14, y=84)
        self.group.append(self.pressure_box)
        
        self.boil_box = BoilBox(x=87, y=84)
        self.group.append(self.boil_box)
        
        self.altitude_text = AltitudeArea(x=14, y=28)
        self.group.append(self.altitude_text)
        
        self.description_box = DescriptionBox(x=142, y=132)
        self.group.append(self.description_box)
        
        self.HILO_box = HILOBox(x=160, y=84)
        self.group.append(self.HILO_box)
        
        self.graph_range = 15
        self.graph = DataGraph(xpos=14, ypos=132, width=122, height=90, group=self.group)
    
    def on_show(self):
        self.store.set_active_metric("altitude", self.graph_range)

    def on_short_select(self):
        global DATA_RANGE
        current_index = DATA_RANGE.index(self.graph_range)
        next_index = (current_index + 1) % len(DATA_RANGE)
        self.graph_range = DATA_RANGE[next_index]
        
        self.store.resize_active_reading(self.graph_range)

    def on_long_select(self):
        pass

    def on_short_next(self):
        pass

    def update_page(self):
        self.pressure_box.update(self.store)
        self.altitude_text.update(self.store)
        self.HILO_box.update(self.store)
        self.description_box.update(self.store)
        self.boil_box.update(self.store)
        
    def data_schedule_update(self):
        readings = self.store.getVariableData()
        self.graph.draw_the_shit(
                    readings.get_data_log(),
                    self.store.get_setting("interval"),
                    readings.max_samples
                )