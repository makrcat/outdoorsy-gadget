
import displayio
import terminalio
import time
import bitmaptools
from adafruit_display_text import label
from utilities import *
from Page import *


from adafruit_display_shapes.line import Line
from adafruit_display_shapes.rect import Rect
from adafruit_displayio_layout.widgets.cartesian import Cartesian
from mockIC import MockBME680
from DashboardPage import DashboardPage
from TemperaturePage import TemperaturePage
from PressurePage import PressurePage
from AQIPage import AQIPage

import gc

## Reset displays
displayio.release_displays()

COMPUTER = True

display = None
bme680 = None
next_button = None
select_button = None



if not COMPUTER:
    import board
    import digitalio
    from fourwire import FourWire
    import adafruit_bme680
else:

    import pygame
    from blinka_displayio_pygamedisplay import PyGameDisplay


if COMPUTER:
    display = PyGameDisplay(240, 240)
    display.auto_refresh = False

    bme680 = MockBME680()
    bme680.sea_level_pressure = 1017.9

else:

    ### BUTTONS ###
    next_button = digitalio.DigitalInOut(board.GP14) #14
    next_button.switch_to_input(pull=digitalio.Pull.UP)
    select_button = digitalio.DigitalInOut(board.GP26) #26
    select_button.switch_to_input(pull=digitalio.Pull.UP)


    i2c_sensor = busio.I2C(
        scl=board.GP7,
        sda=board.GP6,
        frequency=100_000
    ) #400

    bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c_sensor, address=0x77) 
    bme680.sea_level_pressure = 1017.9

    import adafruit_st7789

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



data_store = DataStore(bme680)

### DISPLAY STUFF
master_group = displayio.Group()
display.root_group = master_group


HEADER_HEIGHT = 20
# permanent black background
color_palette = displayio.Palette(1)
color_palette[0] = 0x000000
bg_bitmap = displayio.Bitmap(display.width, display.height, 1)
bg_tilegrid = displayio.TileGrid(bg_bitmap, pixel_shader=color_palette)
bg_line = Line(x0=0, y0=HEADER_HEIGHT, x1=display.width, y1=HEADER_HEIGHT, color=0xFFFFFF)

master_group.append(bg_tilegrid)
master_group.append(bg_line)


# bat group is premanently outside of the content group it's async updated
# do i really know waht async means not really
# its updated silently with other updates


bat_palette = displayio.Palette(5) 
bat_palette[0] = 0x000000 
bat_palette[1] = 0xFFFFFF
bat_palette[2] = 0xFF0000
bat_palette[3] = 0x00FFFF
bat_palette[4] = 0xFFFF00  

bat_bitmap = displayio.Bitmap(22, 10, 5) 
bat_tilegrid = displayio.TileGrid(bat_bitmap, pixel_shader=bat_palette) 

bat_group = displayio.Group(x=display.width - 28, y=5) 
bat_group.append(bat_tilegrid) 
master_group.append(bat_group) 

def better_bitmap_fill(bat_bitmap, x, y, w, h, value):
    bitmaptools.fill_region(bat_bitmap, x, y, x+w, y+h, value)
    # if you enter 1 1 1 1 
    # it is just going to be one pixel.
    

def draw_battery_shell():
    bat_bitmap.fill(0)
    
    better_bitmap_fill(bat_bitmap, 0, 0, 20, 10, value=1)
    better_bitmap_fill(bat_bitmap, 20, 2, 22, 6, value=1)
    better_bitmap_fill(bat_bitmap, 1, 1, 18, 8, value=0)

draw_battery_shell() # just once

def _update_battery(percentage=0.5):
    if percentage > 0.6:
        pcolor = 2
    elif percentage > 0.2:
        pcolor = 3
    else:
        pcolor = 4
    
    width = max(1, int(percentage * 16))
    better_bitmap_fill(bat_bitmap, 1, 1, 18, 8, value=0)
    better_bitmap_fill(bat_bitmap, 2, 2, width, 6, value=pcolor)
        
        


content_group = displayio.Group()
master_group.append(content_group)



### PAGE ARCHITECTURE ###


pages = [
    DashboardPage(data_store),
    TemperaturePage(data_store),
    PressurePage(data_store),
    AQIPage(data_store),
]

page_index = 0
SMODE = False
NMODE = False


def show_page(idx):
    while len(content_group) > 0:
        content_group.pop()

    current_page = pages[idx]
    current_page.on_show()

    content_group.append(current_page.group)
    current_page.update_page()
    gc.collect()

def pagers():
    global page_index
    page_index = (page_index + 1) % len(pages)
    show_page(page_index)

def global_init():
    data_store.update()
    show_page(0)

global_init()

next_button_pressed_last = False
select_button_pressed_last = False


def handle_buttons_modes():
    global next_button_pressed_last, select_button_pressed_last
    global NMODE, SMODE
    
    next_button_pressed = not next_button.value
    select_button_pressed = not select_button.value

    SMODE = False
    NMODE = False
    
    if select_button_pressed and not select_button_pressed_last:
        SMODE = True
        
    if next_button_pressed and not next_button_pressed_last:
        NMODE = True
        
    next_button_pressed_last = next_button_pressed
    select_button_pressed_last = select_button_pressed
        
    # print(f"NEXT: {next_button_pressed}, SELECT: {select_button_pressed}")

last_sensor_read = 0 # bug fixed

def handle_buttons_modes_computer():
    global NMODE, SMODE
    
    SMODE = False
    NMODE = False

    # PYGAME window events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            raise SystemExit
            
        elif event.type == pygame.KEYDOWN:
            #k, s
            if event.key == pygame.K_n or event.key == pygame.K_RIGHT:
                NMODE = True
            elif event.key == pygame.K_s or event.key == pygame.K_RETURN:
                SMODE = True

while True:

    #change
    if COMPUTER:
        handle_buttons_modes_computer()
    else:
        handle_button_modes()

    now = time.monotonic()
    if now - last_sensor_read >= TIME_BTWN: 
        data_store.update()
        last_sensor_read = now
        
        pages[page_index].data_schedule_update()

    if NMODE: pagers()
        
    if SMODE: pages[page_index].on_short_select()
        
    pages[page_index].update_page()
    _update_battery()
    display.refresh()
        
    time.sleep(0.01) 