import board
import busio
import displayio
import i2cdisplaybus
import terminalio
from adafruit_display_text import label
import adafruit_displayio_sh1106


displayio.release_displays()
i2c = busio.I2C(scl=board.GP5, sda=board.GP4)

display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)

WIDTH = 132
HEIGHT = 64
BORDER = 2

display = adafruit_displayio_sh1106.SH1106(display_bus, width=WIDTH, height=HEIGHT)

splash = displayio.Group(x=2, y=0)
display.root_group = splash

color_bitmap = displayio.Bitmap(128, HEIGHT, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0xFFFFFF  

bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
splash.append(bg_sprite)

inner_bitmap = displayio.Bitmap(124, 60, 1)
inner_palette = displayio.Palette(1)
inner_palette[0] = 0x000000 
inner_sprite = displayio.TileGrid(
    inner_bitmap, pixel_shader = inner_palette, x = BORDER, y = BORDER
)
splash.append(inner_sprite)

text = "Hello World!"
text_area = label.Label(
    terminalio.FONT, text=text, color=0xFFFFFF, x=28, y=HEIGHT // 2 - 1
)
splash.append(text_area)

while True:
    pass