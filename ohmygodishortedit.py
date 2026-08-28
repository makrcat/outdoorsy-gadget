import time
import board
import busio
import displayio
from fourwire import FourWire
import terminalio
from adafruit_display_text import label
import adafruit_st7789

displayio.release_displays()

#DC / RES / CS -> any standard digital pin (SPI0)
spi = busio.SPI(clock=board.GP2, MOSI=board.GP3)

#SCL IS SERIAL CLOCK. GP2 is SPI0 SCK
#SDA IS MOSI. GP3 is TX /MOSI

display_bus = FourWire(
    spi, 
    command=board.GP0, # data command is any SPI0. I did GP0
    chip_select=board.GP1,  # GP1 is SPI1 CSn
    reset=None  
)


display = adafruit_st7789.ST7789(
    display_bus, 
    width=240, 
    height=240, 
    rowstart=80,
    rotation=0
)

splash = displayio.Group()
display.root_group = splash

color_bitmap = displayio.Bitmap(240, 240, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0x0000FF 

bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
splash.append(bg_sprite)

text_area = label.Label(
    terminalio.FONT, text="CircuitPython\nST7789 OK!", color=0x00FF00, scale=2
)
text_area.x = 30
text_area.y = 110
splash.append(text_area)

while True:
    time.sleep(1.5)
    color_palette[0] = 0xFF0000  # Red
    time.sleep(1.5)
    color_palette[0] = 0x00FF00  # Green
    time.sleep(1.5)
    color_palette[0] = 0x0000FF  # Blue