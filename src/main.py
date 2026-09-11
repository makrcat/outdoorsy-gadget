import displayio, digitalio
from my_utilities import *

# import board, busio
from Page import *


from adafruit_display_shapes.line import Line
from mockIC import MockBME680
import time
from DashboardPage import DashboardPage
from TemperaturePage import TemperaturePage
from PressurePage import PressurePage
from AQIPage import AQIPage
from SettingsPage import SettingsPage

import gc
gc.collect()

displayio.release_displays()

display = None
bme680 = None
next_button = None
select_button = None
battery_pin = None


COMPUTER = True


if COMPUTER:
    import pygame
    from blinka_displayio_pygamedisplay import PyGameDisplay

    display = PyGameDisplay(240, 240)
    display.auto_refresh = False

    bme680 = MockBME680()
    bme680.sea_level_pressure = 1017.9
        


else:
    import board, busio
    from fourwire import FourWire
    import adafruit_bme680
    import adafruit_st7789
    import analogio


    next_button = digitalio.DigitalInOut(board.GP14) #14
    next_button.switch_to_input(pull=digitalio.Pull.UP)
    select_button = digitalio.DigitalInOut(board.GP26) #26
    select_button.switch_to_input(pull=digitalio.Pull.UP)
    battery_pin = analogio.AnalogIn(board.GP25)
    battery_pin.switch_to_input(pull=digitalio.Pull.UP)


    i2c_sensor = busio.I2C(
        scl=board.GP7,
        sda=board.GP6,
        frequency=100_000
    ) #400


    bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c_sensor, address=0x77) 
    bme680.sea_level_pressure = 1017.9


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
        rotation=180
    )


def get_voltage():
    global battery_pin
    if not COMPUTER:
        return battery_pin / 65535 * 3.7
    else:
        return 3.3


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
bat_palette[2] = 0x00FFFF
bat_palette[3] = 0xFFA500
bat_palette[4] = 0xFF0000  

bat_bitmap = displayio.Bitmap(22, 10, 5) 
bat_tilegrid = displayio.TileGrid(bat_bitmap, pixel_shader=bat_palette) 

bat_group = displayio.Group(x=display.width - 28, y=5) 
bat_group.append(bat_tilegrid) 
master_group.append(bat_group) 

signal = label.Label(
    terminalio.FONT, 
    text="00%", 
    color=0xFFFFFF, 
    anchor_point=(1.0, 0.0),
    anchored_position=(display.width - 28 -4, 4), 
    scale=1
)
master_group.append(signal)

def better_bitmap_fill(bat_bitmap, x, y, w, h, value):
    bitmaptools.fill_region(bat_bitmap, x, y, x+w, y+h, value)
    # if you enter 1 1 1 1 
    # it is just going to be one pixel.
    

def draw_battery_shell():
    bat_bitmap.fill(0)

    better_bitmap_fill(bat_bitmap, 0, 0, 20, 10, value=1)
    better_bitmap_fill(bat_bitmap, 20, 2, 2, 6, value=1) 
    better_bitmap_fill(bat_bitmap, 1, 1, 18, 8, value=0)

draw_battery_shell() # just once



BATTERY_CURVE = [
    (4.20, 100),
    (4.10,  90),
    (4.00,  80),
    (3.90,  70),
    (3.80,  60),
    (3.70,  50),
    (3.60,  40),
    (3.50,  30),
    (3.40,  20),
    (3.20,  10),
    (3.00,   0)
]

def voltage_to_percentage(voltage):

    for i in range(len(BATTERY_CURVE) - 1):
        v_high, p_high = BATTERY_CURVE[i]
        v_low, p_low = BATTERY_CURVE[i + 1]
        
        if voltage >= v_low:
            voltage_range = v_high - v_low
            percentage_range = p_high - p_low
            position_over = voltage - v_low
            
            return int(p_low + (position_over / voltage_range) * percentage_range)
        

            
    return 0

def _update_battery(voltage = 3.6):
    
    p_100 = voltage_to_percentage(voltage)
    signal.text = f"{p_100}%"
    
    percentage = p_100 / 100
    
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
    SettingsPage(data_store),
]

page_index = 0
current_page_instance = None


def show_page(idx):
    
    global current_page_instance
    
    while len(content_group) > 0:
        content_group.pop()
        
    current_page_instance = None
    gc.collect()
    
    current_page_instance = pages[idx]
    
    current_page_instance.on_show()
    content_group.append(current_page_instance.group)
    current_page_instance.update_page()
    
    gc.collect()
    
    

def pagers():
    global page_index
    page_index = (page_index + 1) % len(pages) 
    show_page(page_index)

def global_init():
    data_store.update()
    show_page(page_index)

global_init()

last_sensor_read = 0 # bug fixed










next_button_pressed_last = False
select_button_pressed_last = False
SMODE = False
NMODE = False
L_SMODE = False
select_time_start_down = 0
long_press_fired = False # prevent the long press always being written True while pressed
long_thresh = 2.5

def handle_buttons_modes():
    global next_button_pressed_last, select_button_pressed_last
    global NMODE, SMODE, L_SMODE, select_time_start_down, long_thresh, long_press_fired
    
    next_button_pressed = not next_button.value
    select_button_pressed = not select_button.value

    NMODE = False
    SMODE = False
    L_SMODE = False
    
    if select_button_pressed and not select_button_pressed_last: # JUST PRESSED
        select_time_start_down = time.monotonic()
        long_press_fired = False
        
    elif select_button_pressed:
        if (not long_press_fired) and time.monotonic() - select_time_start_down >= long_thresh:
            L_SMODE = True
            long_press_fired = True
            
    elif (select_button_pressed_last and not select_button_pressed 
          and time.monotonic() - select_time_start_down < long_thresh):
        SMODE = True
        
    if next_button_pressed and not next_button_pressed_last:
        NMODE = True
        
    next_button_pressed_last = next_button_pressed
    select_button_pressed_last = select_button_pressed
    
    
    
# Gemini-generated ####
def handle_buttons_modes_computer():
    global next_button_pressed_last, select_button_pressed_last
    global NMODE, SMODE, L_SMODE, select_time_start_down, long_thresh, long_press_fired
    
    NMODE = False
    SMODE = False
    L_SMODE = False

    # PYGAME window events (handles closing the window properly)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            raise SystemExit

    # Poll keyboard state continuously (similar to reading hardware pins)
    keys = pygame.key.get_pressed()
    next_button_pressed = keys[pygame.K_n] or keys[pygame.K_RIGHT]
    select_button_pressed = keys[pygame.K_s] or keys[pygame.K_RETURN]


    if select_button_pressed and not select_button_pressed_last:
        select_time_start_down = time.monotonic()
        long_press_fired = False
        
    elif select_button_pressed:
        if (not long_press_fired) and time.monotonic() - select_time_start_down >= long_thresh:
            L_SMODE = True
            long_press_fired = True
            
    elif (select_button_pressed_last and not select_button_pressed 
          and time.monotonic() - select_time_start_down < long_thresh):
        SMODE = True
        

    if next_button_pressed and not next_button_pressed_last:
        NMODE = True
        
    next_button_pressed_last = next_button_pressed
    select_button_pressed_last = select_button_pressed
#########################



last_gc_time = 0
GC_INTERVAL = 1.0
upd = False

while True:

    if COMPUTER: handle_buttons_modes_computer()
    else: handle_buttons_modes()

    now = time.monotonic()

    if now - last_gc_time > GC_INTERVAL:
        #print("Free RAM:", gc.mem_free(), "bytes")
        gc.collect()
        last_gc_time = now
    

    if now - last_sensor_read >= data_store.get_setting("interval"):
        data_store.update()
        
        last_sensor_read = now
        current_page_instance.data_schedule_update()
        upd = True

    if NMODE:
        if current_page_instance.on_short_next() != False:
            pagers()
        upd = True

    elif SMODE:
        current_page_instance.on_short_select()
        upd = True

    elif L_SMODE:
        current_page_instance.on_long_select()
        upd = True

    if upd:
        current_page_instance.update_page()
        upd = False
        
        _update_battery(get_voltage())
        gc.collect()
        display.refresh()

    time.sleep(0.01)

