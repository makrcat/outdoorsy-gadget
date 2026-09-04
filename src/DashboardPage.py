import displayio, terminalio
from utilities import *
from Page import Page
from adafruit_display_shapes.rect import Rect
from adafruit_display_shapes.line import Line
from adafruit_display_text import label
from fonts import PRAGATI_42, HAXOR, NINE, PRAGATI_22


class TempBox(displayio.Group):
    def __init__(self, x, y):
        super().__init__(x=x, y=y)
        
        self.append(Rect(0, 0, 122, 84, outline=0xFFFFFF))
        
        self.temp_label = label.Label(
            PRAGATI_42, 
            text="--.- *C", 
            color=0xFFFFFF, 
            anchor_point=(0.0, 0.0),
            anchored_position=(20, 12), 
            scale=1
        )
        self.hum_label = label.Label(
            PRAGATI_22, 
            text="-- hu", 
            color=0xFFFFFF, 
            anchor_point=(0.0, 0.0),
            anchored_position=(20, 52), 
            scale=1
        )
        self.append(self.temp_label)
        self.append(self.hum_label)
        
        self.gradient = tempGradientObject(xpos=0, ypos=0, width=12, height=84, value=40, 
                                           colorz=[0x0FEFD8, 0xC300FF, 0xFF0000], group=self)
        self.append(Rect(0, 0, 12, 84, outline=0xFFFFFF))
        
        # Axis labels
        self.append(label.Label(terminalio.FONT, text='100', color=0xFFFFFF, x=-5, y=-6, scale=1))
        self.append(label.Label(terminalio.FONT, text='0', color=0xFFFFFF, x=4, y=76, scale=1))

    def update(self, store):
        self.temp_label.text = f"{store.getVal("temperature"):.1f}"
        self.hum_label.text = f"{store.getVal("humidity"):.1f}% hu"

class GasBox(displayio.Group):
    def __init__(self, x, y):
        super().__init__(x=x, y=y)
        
        self.append(Rect(0, 0, 108, 90, outline=0xFFFFFF))
        
        self.aqi_label = label.Label(
            PRAGATI_42, 
            text="--.-", 
            color=0xFFFFFF, 
            anchor_point=(0.0, 0.0),
            anchored_position=(10, 12),
            scale=1
        )

        
        self.eCO2_label = label.Label(
            PRAGATI_22, 
            text="--.-", 
            color=0xFFFFFF, 
            anchor_point=(0.0, 0.0), 
            anchored_position=(10, 52),
            scale=1
        )

        self.append(self.aqi_label)
        self.append(self.eCO2_label)

        self.gradient = tempGradientObject(
            xpos=4, ypos=78, width=100, height=7, value=100, group=self, 
            colorz=[0x31D726, 0xE6C329, 0xDF752F, 0xDB2424, 0x892ADC], 
            orientation='horizontal'
        )
        
        # Gradient Outline
        self.append(Rect(4, 78, 100, 7, outline=0xFFFFFF))

    def update(self, store):
        self.aqi_label.text = f"{store.getVal("aqi"):.1f}"
        self.eCO2_label.text = f"eCO2: {store.getVal("eCO2"):.0f}"
        

class AltBox(displayio.Group):
    def __init__(self, x, y):
        super().__init__(x=x, y=y)

        self.alt_label = label.Label(
            PRAGATI_42, 
            text="--m", 
            color=0xFFFFFF,
            anchor_point=(0.0, 0.0),
            anchored_position=(8, 12), 
            scale=1
            )
        self.press_label = label.Label(
            PRAGATI_22, 
            text="----", 
            color=0xFFFFFF, 
            anchor_point=(0.0, 0.0),
            anchored_position=(8, 52),  
            scale=1
        )
        self.append(self.alt_label)
        self.append(self.press_label)

        self.append(Rect(0, 0, 86, 84, outline=0xFFFFFF))
        self._draw_decor()
    
    def _draw_decor(self):
        width = 80
        height = 30

        bitmap = displayio.Bitmap(width, height, 2)
        palette = displayio.Palette(2)
        palette[0] = 0x000000
        palette[1] = 0xFFFFFF
        palette.make_transparent(0)

        for i in range(2):

            bitmaptools.draw_line(bitmap, 0, 15 + i, 35, 0 + i, 1)    # Left side
            bitmaptools.draw_line(bitmap, 35, 0 + i, 70, 15 + i, 1)  # Right side
            
            gap = 6
            
            bitmaptools.draw_line(bitmap, 0, 15 + gap + i, 35, 0 + gap + i, 1)   # Left side
            bitmaptools.draw_line(bitmap, 35, 0 + gap + i, 70, 15 + gap + i, 1)

        tile_grid = displayio.TileGrid(bitmap, pixel_shader=palette)
        tile_grid.x = 6
        tile_grid.y = -16
        self.append(tile_grid)

    def update(self, store):
        self.alt_label.text = f"{store.getVal("altitude"):.0f}m"
        self.press_label.text = f"{store.getVal("pressure"):.0f} hPa"

class LastBox(displayio.Group):
    def __init__(self, x, y):
        super().__init__(x=x, y=y)

        self.append(Rect(0, 0, 100, 90, outline=0xFFFFFF))


class DashboardPage(Page):
    
    def __init__(self, store):
        super().__init__(header_text="ALL data!")
        self.store = store

        self.temp_box = TempBox(x=13, y=40)
        self.alt_box = AltBox(x=143, y=40)
        self.gas_box = GasBox(x=13, y=132)
        self.last_box = LastBox(x=129, y=132)


        self.group.append(self.temp_box)
        self.group.append(self.alt_box)
        self.group.append(self.gas_box)
        self.group.append(self.last_box)
   

    def on_show(self):
        pass

    def on_short_select(self):
        pass

    def on_long_select(self):
        pass

    def on_short_next(self):
        pass

    def update_page(self):
        self.temp_box.update(self.store)
        self.alt_box.update(self.store)
        self.gas_box.update(self.store)

    def data_schedule_update(self):
        pass


