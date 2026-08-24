import board
import busio
import displayio
import terminalio
import time
from adafruit_display_text import label
import adafruit_ssd1681
import adafruit_ssd1306
import digitalio
from fourwire import FourWire
import adafruit_bme680
import vectorio
from adafruit_display_shapes.line import Line
from abc import ABC, abstractmethod




## Reset displays
displayio.release_displays()


## initialize thingy
'''
spi = busio.SPI(clock=board.GP2, MOSI=board.GP3)
display_bus = FourWire(
    spi,
    command=board.GP4, 
    chip_select=board.GP5,
    reset=board.GP1, 
    baudrate=2000000,
)


display = adafruit_ssd1681.SSD1681(
    display_bus,
    width=200,
    height=200,
    busy_pin=board.GP0,     
    rotation=0,
    seconds_per_frame = 5
)
'''


### BUTTONS ###
next_button = digitalio.DigitalInOut(board.GP14)
next_button.switch_to_input(pull=digitalio.Pull.UP)
select_button = digitalio.DigitalInOut(board.GP15)
select_button.switch_to_input(pull=digitalio.Pull.UP)

i2c_sensor = busio.I2C(scl=board.GP5, sda=board.GP4, frequency=100_000) #400
bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c_sensor, address=0x77) 


## TEMPORARY

import i2cdisplaybus
import adafruit_displayio_sh1106
i2c_oled = busio.I2C(scl=board.GP7, sda=board.GP6)
display_bus = i2cdisplaybus.I2CDisplayBus(i2c_oled, device_address=0x3C)
display = adafruit_displayio_sh1106.SH1106(display_bus, width=128, height=64)

display.auto_refresh = False


###


### Variables

page = 1
upd = True
SMODE = False
NMODE = False

### DISPLAY STUFF

master_group = displayio.Group()
display.root_group = master_group

# permanent white background
color_palette = displayio.Palette(1)
color_palette[0] = 0xFFFFFF
bg_bitmap = displayio.Bitmap(200, 200, 1)
bg_tilegrid = displayio.TileGrid(bg_bitmap, pixel_shader=color_palette)
bg_line = Line(x0=0, y0=16, x1=200, y1=16, color=0x000000)

master_group.append(bg_tilegrid)
master_group.append(bg_line)


# Declare bat_group globally outside the function
bat_group = None

def _update_battery(level=5):
    print("running battery stuff)")
    global bat_group
    
    # 1. If the bat_group already exists, pop everything out of it until it's empty
    if bat_group is not None:
        while len(bat_group) > 0:
            bat_group.pop()
    else:
        # If it doesn't exist yet, create it and add it to the master_group once
        bat_group = displayio.Group()
        master_group.append(bat_group)

    battery_level = level
    bat_palette = displayio.Palette(1)
    bat_palette[0] = 0x000000
    square_bitmap = displayio.Bitmap(10, 10, 1)

    total_battery_width = (battery_level * 10) + ((battery_level - 1) * 2)
    start_x = display.width - total_battery_width - 3  # Uses display.width dynamically so it fits 128px or 200px screens!
    start_y = 3

    for i in range(battery_level):
        tile_grid = displayio.TileGrid(square_bitmap, pixel_shader=bat_palette)
        tile_grid.x = start_x + (i * (10 + 2))
        tile_grid.y = start_y
        bat_group.append(tile_grid)
###
content_group = displayio.Group()
master_group.append(content_group)


class DataStore:
    def __init__(self, sensor, max_samples=60):
        self.sensor = sensor
        self.max_samples = max_samples
        
        self.temp_history = []
        self.humidity_history = []
        self.pressure_history = []
        self.altitude_history = []
        self.iaq_history = []

    @property
    def temp(self) -> float:
        return self.temp_history[-1]

    @property
    def humidity(self) -> float:
        return self.humidity_history[-1]

    @property
    def pressure(self) -> float:
        return self.pressure_history[-1]

    @property
    def altitude(self) -> float:
        return self.altitude_history[-1]

    @property
    def iaq(self) -> int:
        return self.iaq_history[-1]

    def _add_to_history(self, history_list, value):
        """Helper to append a reading and maintain max_samples."""
        history_list.append(value)
        if len(history_list) > self.max_samples:
            history_list.pop(0)

    def update(self):
        """Read sensor once and log to history buffers."""
        try:
            # Read fresh values from the sensor
            new_temp = self.sensor.temperature
            new_humidity = self.sensor.relative_humidity
            new_pressure = self.sensor.pressure
            new_altitude = self.sensor.altitude
            new_iaq = getattr(self.sensor, 'iaq', 0) # Fallback if sensor lacks IAQ

            # Update histories using our helper
            self._add_to_history(self.temp_history, new_temp)
            self._add_to_history(self.humidity_history, new_humidity)
            self._add_to_history(self.pressure_history, new_pressure)
            self._add_to_history(self.altitude_history, new_altitude)
            self._add_to_history(self.iaq_history, new_iaq)

        except Exception as e:
            print("Sensor read error:", e)

data_store = DataStore(bme680)



class Page:
    def __init__(self, header_text=""):
        self.header_text = header_text
        self.group = displayio.Group()
        self.in_select_mode = False
        self.header_label = label.Label(
            terminalio.FONT, text=header_text, color=0x000000, x=3, y=5
        )
        self.group.append(self.header_label)

    def set_header(self, text):
        """Helper to quickly change the top bar when entering select mode."""
        self.header_label.text = text

    @abstractmethod
    def update_page(self):
        """UPDATE SCREEN"""
        pass
        

    @abstractmethod
    def on_short_select(self):
        """Action when SELECT is clicked quickly."""
        pass

    @abstractmethod
    def on_long_select(self):
        """Action when SELECT is held down (e.g., EXIT or REFRESH)."""
        pass
    
    @abstractmethod
    def on_short_next(self):
        """Action when NEXT is clicked."""
        pass

class DashboardPage(Page):
    def __init__(self, store):
        super().__init__(header_text="SELECT to refresh")
        self.store = store

        self.temp_lbl = label.Label(terminalio.FONT, text="--.- *F", color=0x000000, x=6, y=25)
        self.group.append(self.temp_lbl)

    def update_page(self):
        self.temp_lbl.text = f"{self.store.temp:.1f} *F"

    def on_short_select(self):
        """Action when SELECT is clicked quickly."""
        pass

    def on_long_select(self):
        """Action when SELECT is held down (e.g., EXIT or REFRESH)."""
        pass

    def on_short_next(self):
        """Action when NEXT is clicked."""
        pass

class TemperaturePage(Page):
    def __init__(self, store):
        super().__init__(header_text="Temperature")
        self.store = store

    def update_page(self):
        pass

    def on_short_select(self):
        """Action when SELECT is clicked quickly."""
        pass

    def on_long_select(self):
        """Action when SELECT is held down (e.g., EXIT or REFRESH)."""
        pass

    def on_short_next(self):
        """Action when NEXT is clicked."""
        pass    

temp = 0
temp_offset = -3
alt = 0
rh = 0

# Old size stuff
'''
page1_group = displayio.Group()
page1_group.append(label.Label(terminalio.FONT, text="SELECT to refresh", color=0x000000, x=3, y=7))
temp_label = label.Label(terminalio.FONT, text="--.-", color=0x000000, x=6, y=36, scale=3)
another = label.Label(terminalio.FONT, text="*C", color=0x000000, x=80, y=36, scale=2)

hum_label = label.Label(terminalio.FONT, text="-- %", color=0x000000, x=6, y=64, scale=2)
page1_group.append(temp_label) 
page1_group.append(hum_label)
page1_group.append(another)
'''

# TEMPORARY
page1_group = displayio.Group()

page1_group.append(
    label.Label(
        terminalio.FONT,
        text="SELECT to refresh",
        color=0x000000,
        x=3,
        y=5
    )
)

temp_label = label.Label(
    terminalio.FONT,
    text="--.-",
    color=0x000000,
    x=6,
    y=25,
    scale=1
)

another = label.Label(
    terminalio.FONT,
    text="*C",
    color=0x000000,
    x=45,
    y=25,
    scale=1
)

hum_label = label.Label(
    terminalio.FONT,
    text="-- %",
    color=0x000000,
    x=6,
    y=40,
    scale=1
)

alt_label = label.Label(
    terminalio.FONT,
    text="-- %",
    color=0x000000,
    x=60,
    y=25,
    scale=1
)

press_label = label.Label(
    terminalio.FONT,
    text="-- %",
    color=0x000000,
    x=60,
    y=45,
    scale=1
)

page1_group.append(temp_label)
page1_group.append(hum_label)
page1_group.append(alt_label)
page1_group.append(press_label)
page1_group.append(another)
### TEMPORARY


def screen1():
    global temp, rh, temp_label, hum_label, upd, bme680

    try:
        t_temp = bme680.temperature
        t_rh = bme680.relative_humidity
        
        pressure = bme680.pressure
        alt = bme680.altitude
        
        # if the update button is pressed, startReading. set thing to "calibrating" and then start reading.
        # Calibrating.
        #start thingy. get numbers.
        # update numbers.
        
        temp_label.text = f"{t_temp:.1f}"
        hum_label.text = f"{t_rh:.1f} %"
        alt_label.text = f"{alt:.1f} m"
        press_label.text = f"{pressure:.1f} hPa"
    except Exception as e:
        print(e)
    
def screen2():
    # TODO: Add page 2 content later
    pass

def screen3():
    # TODO: Add page 3 content later
    pass

def screen4():
    # TODO: Add page 4 content later
    pass


def show_page(page_num):
    print("running showpage")
    global upd
    
    while len(content_group) > 0:
        content_group.pop()
        
    if page_num == 1:
        content_group.append(page1_group)
        screen1()
    elif page_num == 2:
        content_group.append(page2_group)
        screen2()
    elif page_num == 3:
        content_group.append(page3_group)
        screen3()
    elif page_num == 4:
        content_group.append(page4_group)
        screen4()

def pagers():
    print("pagers")
    global page
    page += 1
    if page > 4:
        page = 1
    show_page(page)
    
    
def _on_upd_async_updates():
    _update_battery()

def global_init():
    show_page(1)
    
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
        
    print(f"NEXT: {next_button_pressed}, SELECT: {select_button_pressed}")
    
def print_active_sensors():
    while not i2c_sensor.try_lock():
        pass

    try:
        print([hex(x) for x in i2c_sensor.scan()])
    finally:
        i2c_sensor.unlock()
        
while True:

    handle_buttons_modes()
    print_active_sensors()
    
    '''
    if NMODE or SMODE: # pretend thsi is partial updates
        if display.busy:
            print("Alert: Display is busy processing an update! Please wait.")
            
            

        elif display.time_to_refresh > 0:
            print(f"Alert: Too fast! Wait {display.time_to_refresh:.1f} more seconds.")
            
        
        
        else:
            
            if NMODE:
                try:
                    pagers()
                except Exception as e:
                    print(e)
                    
                time.sleep(0.2)
                upd = True
            
            if SMODE:
                if page == 1:
                    screen1()
                elif page == 2:
                    screen2()
                elif page == 3:
                    screen3()
                elif page == 4:
                    screen4()
                upd = True
'''
    
    
    # NEW
    if NMODE:
        try:
            pagers()
        except Exception as e:
            print(e)
        upd = True
        
        
        print("SMODE: paging next:" + str(page))
        
    if SMODE:
        print("SMODE: select:" + str(page))
        if page == 1:
            screen1()
        elif page == 2:
            screen2()
        elif page == 3:
            screen3()
        elif page == 4:
            screen4()
        upd = True
        
        # END NEW
        
    if NMODE or SMODE:
        time.sleep(0.15)
        
    if upd:
        _on_upd_async_updates()
        display.refresh()
        upd = False
        
    time.sleep(0.05)

# gotta refactor thi