import board
import busio
import displayio
import terminalio
import time
from adafruit_display_text import label
import digitalio
from fourwire import FourWire
import adafruit_bme680
import vectorio
from adafruit_display_shapes.line import Line



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


## TEMPORARY displays: ########

import i2cdisplaybus
import adafruit_displayio_sh1106

i2c_oled = busio.I2C(scl=board.GP7, sda=board.GP6)
display_bus = i2cdisplaybus.I2CDisplayBus(i2c_oled, device_address=0x3C)
display = adafruit_displayio_sh1106.SH1106(display_bus, width=128, height=64)
display.auto_refresh = False

############3

class Reading:
    def __init__(self):
        self.log = []
        self.read_size = 6
        self.max_samples = 100
        self.last_change = None

    def addReading(self, r):
        if len(self.log) == self.max_samples:
            self.log.pop(0)
        self.log.append(r)

    def _shouldUpdate(self):
        if len(self.log) < self.read_size:
            return False
        
        if self.last_change is None:
            return True # yeah so there's no error down there vv

        samples = self.log[-1 * self.read_size:]
        
        mean = sum(samples) / len(samples)
        latest = samples[-1]
            
        if abs(mean - latest) > 0.2 or abs(self.last_change - mean) >= 0.1:
            return True

        return False

    def _updateVal(self):
        if self.log:
            self.last_change = self.log[-1]
        return self.last_change
    
    def checkMaybeUpdate(self) -> bool:
        if self._shouldUpdate():
            self._updateVal()
            return True
        return False

    def getReading(self):
        return self.log[-1] # should have updated before so that it's not empty. you can't get reading if you never updated the log
    
    
    
class DataStore:
    def __init__(self, sensor):
        self.sensor = sensor
        
        # Instantiate a Reading object for each metric
        self.temp_read = Reading()
        self.humidity_read = Reading()
        self.pressure_read = Reading()
        self.altitude_read = Reading()
        self.iaq_read = Reading()
        
        self.data_dict = {
            "temp": self.temp_read,
            "hum": self.humidity_read,
            "press": self.pressure_read,
            "alt": self.altitude_read,
            "iaq": self.iaq_read
        }
        
        self.longer_storage = {
            "temp":[],
            "hum":[],
            "press":[],
            "alt":[],
            "iaq":[]
        }
        
        # { "temp":[], "humidity:[], "pressure":[], "altitude":[], }

    @property
    def temp(self) -> float:
        return self.temp_read.getReading()

    @property
    def humidity(self) -> float:
        return self.humidity_read.getReading()

    @property
    def pressure(self) -> float:
        return self.pressure_read.getReading()

    @property
    def altitude(self) -> float:
        return self.altitude_read.getReading()

    @property
    def iaq(self) -> float:
        return self.iaq_read.getReading()

    def update(self) -> None:
        try:
            self.temp_read.addReading(self.sensor.temperature)
            self.humidity_read.addReading(self.sensor.relative_humidity)
            self.pressure_read.addReading(self.sensor.pressure)
            self.altitude_read.addReading(self.sensor.altitude)
            self.iaq_read.addReading(getattr(self.sensor, 'iaq', 0)) #TODO: what?
        except Exception as e:
            print("Sensor read error:", e)
    
    def checkAndUpdate(self, subjects: list[int]) -> bool:

        an = False
        
        for s in subjects:
            if self.data_dict[s].checkMaybeUpdate():
                an = True
                # gotta get through all of them
                
        return an
            
        

data_store = DataStore(bme680)


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

# bat group is premanently outside of the content group it's async updated
# do i really know waht async means not really
# its updated silently with other updates
bat_group = None

def _update_battery(level=5):
    global bat_group
    
    if bat_group is not None:
        while len(bat_group) > 0:
            bat_group.pop()
    else:
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

content_group = displayio.Group()
master_group.append(content_group)


### PAGE ARCHITECTURE ###

class Page():
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

    #@abstractmethod
    def _update_page(self):
        """UPDATE SCREEN"""
        pass

    #@abstractmethod
    def on_short_select(self):
        """Action when SELECT is clicked quickly."""
        pass

    #@abstractmethod
    def on_long_select(self):
        """Action when SELECT is held down (e.g., EXIT or REFRESH)."""
        pass
    
    #@abstractmethod
    def on_short_next(self):
        """Action when NEXT is clicked."""
        pass
    
    def run_idle(self):
        """Handle state changes and update page"""
        pass


class DashboardPage(Page):
    def __init__(self, store):
        super().__init__(header_text="SELECT to refresh")
        self.store = store

        # TEMPORARY layout
        self.temp_label = label.Label(terminalio.FONT, text="--.-", color=0x000000, x=6, y=25, scale=1)
        self.another = label.Label(terminalio.FONT, text="*C", color=0x000000, x=45, y=25, scale=1)
        self.hum_label = label.Label(terminalio.FONT, text="-- %", color=0x000000, x=6, y=40, scale=1)
        self.alt_label = label.Label(terminalio.FONT, text="-- %", color=0x000000, x=60, y=25, scale=1)
        self.press_label = label.Label(terminalio.FONT, text="-- %", color=0x000000, x=60, y=45, scale=1)

        self.group.append(self.temp_label)
        self.group.append(self.hum_label)
        self.group.append(self.alt_label)
        self.group.append(self.press_label)
        self.group.append(self.another)

    def _update_page(self):
        self.temp_label.text = f"{self.store.temp:.1f}"
        self.hum_label.text = f"{self.store.humidity:.1f} %"
        self.alt_label.text = f"{self.store.altitude:.1f} m"
        self.press_label.text = f"{self.store.pressure:.1f} hPa"

    def on_short_select(self):
        pass

    def on_long_select(self):
        pass

    def on_short_next(self):
        pass

    def run_idle(self):
        
        up = self.store.checkAndUpdate(["temp", "alt", "hum", "iaq", "press"])
        if up: self._update_page()
        return up


class TemperaturePage(Page):
    def __init__(self, store):
        super().__init__(header_text="Temperature")
        self.store = store
        
        self.temp_lbl = label.Label(terminalio.FONT, text="--.- *C", color=0x000000, x=6, y=25, scale=1)
        self.hum_lbl = label.Label(terminalio.FONT, text="RH: --.- %", color=0x000000, x=6, y=45, scale=1)
        self.group.append(self.temp_lbl)
        self.group.append(self.hum_lbl)

    def _update_page(self):
        self.temp_lbl.text = f"{self.store.temp:.1f} *C"
        self.hum_lbl.text = f"RH: {self.store.humidity:.1f} %"

    def on_short_select(self):
        pass

    def on_long_select(self):
        pass

    def on_short_next(self):
        pass 

    def run_idle(self):
        
        up = self.store.checkAndUpdate(["temp", "hum"])
        if up: self._update_page()
        return up


class PressurePage(Page):
    def __init__(self, store):
        super().__init__(header_text="Barometer")
        self.store = store
        
        self.press_lbl = label.Label(terminalio.FONT, text="--.- hPa", color=0x000000, x=6, y=25, scale=1)
        self.alt_lbl = label.Label(terminalio.FONT, text="--.- m", color=0x000000, x=6, y=45, scale=1)
        self.group.append(self.press_lbl)
        self.group.append(self.alt_lbl)

    def _update_page(self):
        self.press_lbl.text = f"{self.store.pressure:.1f} hPa"
        self.alt_lbl.text = f"{self.store.altitude:.1f} m"

    def on_short_select(self):
        # ok actually i think. we should uh. have it always idly run, on short select force an update. yeah
        pass

    def on_long_select(self):
        pass

    def on_short_next(self):
        pass

    def run_idle(self):
        
        up = self.store.checkAndUpdate(["alt", "press"])
        if up: self._update_page()
        return up

# 3 active pages array
pages = [
    DashboardPage(data_store),
    TemperaturePage(data_store),
    PressurePage(data_store)
]

page_index = 0
upd = True
SMODE = False
NMODE = False


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


def show_page(idx):
    while len(content_group) > 0:
        content_group.pop()

    current_page = pages[idx]
    content_group.append(current_page.group)
    current_page._update_page()


def pagers():
    global page_index
    page_index = (page_index + 1) % len(pages)
    show_page(page_index)


def _on_upd_async_updates():
    _update_battery()


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
        
    print(f"NEXT: {next_button_pressed}, SELECT: {select_button_pressed}")

'''
def print_active_sensors():
    while not i2c_sensor.try_lock():
        pass

    try:
        print([hex(x) for x in i2c_sensor.scan()])
    finally:
        i2c_sensor.unlock()
'''

last_sensor_read = 0 # bug fixed

while True:

    handle_buttons_modes() # update button modes booleans
    
    ######## handle data sensor stuff

    now = time.monotonic()
    if now - last_sensor_read >= 3.0:  # Read every 3 seconds
        data_store.update()
        last_sensor_read = now
    ########


    # e-ink stuff.. later
    '''
    if NMODE or SMODE: # pretend thsi is partial updates
        if display.busy:
            print("Alert: Display is busy processing an update! Please wait.")
    '''

    # NEW
    if NMODE:
        try:
            pagers()
        except Exception as e:
            print(e)
        upd = True
        
        print("SMODE: paging next:" + str(page_index + 1))
        
    if SMODE:
        print("SMODE: select:" + str(page_index + 1))
        pages[page_index].on_short_select()
        upd = True
        
        # END NEW

    if NMODE or SMODE:
        time.sleep(0.08) # button debounce
        
    if pages[page_index].run_idle(): upd = True
        
    if upd:
        _on_upd_async_updates()
        display.refresh()
        upd = False
        
    time.sleep(0.05) 