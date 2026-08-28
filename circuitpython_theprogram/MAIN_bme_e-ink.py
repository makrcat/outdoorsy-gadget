import board
import busio
import displayio
import terminalio
import time
import bitmaptools
from adafruit_display_text import label
import digitalio
from fourwire import FourWire
import adafruit_bme680
from adafruit_display_shapes.line import Line
from adafruit_display_shapes.rect import Rect
from adafruit_displayio_layout.widgets.cartesian import Cartesian
import gc


## Reset displays
displayio.release_displays()

TIME_BTWN = 1.0
MAX_SAMPLES = 240
DATA_RANGE = [10, 30, 60, 120, 240]

### BUTTONS ###
next_button = digitalio.DigitalInOut(board.GP14) #14
next_button.switch_to_input(pull=digitalio.Pull.UP)
select_button = digitalio.DigitalInOut(board.GP26) #26
select_button.switch_to_input(pull=digitalio.Pull.UP)

i2c_sensor = busio.I2C(
    scl=board.GP7,
    sda=board.GP8,
    frequency=100_000
) #400
bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c_sensor, address=0x77) 
bme680.sea_level_pressure = 1017.9



'''

import i2cdisplaybus
import adafruit_displayio_sh1106

i2c_oled = busio.I2C(scl=board.GP7, sda=board.GP6)
display_bus = i2cdisplaybus.I2CDisplayBus(i2c_oled, device_address=0x3C)
display = adafruit_displayio_sh1106.SH1106(display_bus, width=128, height=64)
'''


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
display.auto_refresh = False


############3

class Reading:
    def __init__(self):
        global MAX_SAMPLES
        self.log = []
        self.time_log = []
        self.read_size = 5
        self.max_samples = MAX_SAMPLES
        self.last_change = None
        
    def get_data_log(self):
        return self.log

    def get_time_log(self):
        return self.time_log

    def addReading(self, r):
        global TIME_BTWN
        
        if len(self.log) == self.max_samples:
            self.log.pop(0)
            self.time_log.pop(0)
            
        self.log.append(r)
        
        # time log
        self.time_log.append(TIME_BTWN)

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
        self.active_metric = "temp"
        self.active_reading = Reading()
        
        self.latest_values = {
            "temp": 0,
            "hum": 0,
            "press": 0,
            "alt": 0,
            "iaq": 0
        }

    @property
    def temp(self) -> float:
        return self.latest_values["temp"]

    @property
    def humidity(self) -> float:
        return self.latest_values["hum"]

    @property
    def pressure(self) -> float:
        return self.latest_values["press"]

    @property
    def altitude(self) -> float:
        return self.latest_values["alt"]

    @property
    def iaq(self) -> float:
        return self.latest_values["iaq"]

    def update(self) -> None:
        try:
            offset = -4
            
            self.latest_values["temp"] = self.sensor.temperature + offset
            self.latest_values["hum"] = self.sensor.relative_humidity
            self.latest_values["press"] = self.sensor.pressure
            self.latest_values["alt"] = self.sensor.altitude
            self.latest_values["iaq"] = getattr(self.sensor, 'iaq', 0)
            
            active_val = self.latest_values[self.active_metric]
            self.active_reading.addReading(active_val)
            
        except Exception as e:
            print("Sensor read error:", e)
            
    def set_active_metric(self, metric_name):
        if metric_name != self.active_metric:
            self.active_metric = metric_name
            self.active_reading.log.clear()
            self.active_reading.time_log.clear()
            self.active_reading.last_change = None
            self.active_reading = Reading()
    
    def checkAndUpdate(self) -> bool:
        return self.active_reading.checkMaybeUpdate()

    def getVariableData(self):
        return self.active_reading


class SparkGraph:
    def __init__(self, xpos, ypos, width, height, group):
        self.xpos = xpos
        self.ypos = ypos
        self.width = width
        self.height = height
        self.group = group
        self.polygon = None
        

        self.palette = displayio.Palette(2)
        self.palette[0] = 0x000000
        self.palette[1] = 0xFFFFFF
            
            
        self.ui_group = displayio.Group(x=xpos, y=ypos)
        self.group.append(self.ui_group)


        self.bitmap = displayio.Bitmap(width, height, len(self.palette))
        self.tile_grid = displayio.TileGrid(self.bitmap, pixel_shader=self.palette)
        self.ui_group.append(self.tile_grid)

        self.max_label = label.Label(terminalio.FONT, text="", color=0xFFFFFF)
        self.max_label.anchor_point = (1.0, 1.0)
        self.max_label.x = -12
        self.max_label.y = 4
        self.ui_group.append(self.max_label)

        self.min_label = label.Label(terminalio.FONT, text="", color=0xFFFFFF)
        self.min_label.anchor_point = (1.0, 1.0)
        self.min_label.x = -12
        self.min_label.y = height - 4
        self.ui_group.append(self.min_label)
        
        self.leftLabel = label.Label(terminalio.FONT, text="t-60s", color=0xFFFFFF)
        self.leftLabel.x = 0
        self.leftLabel.y = height + 4
        self.ui_group.append(self.leftLabel)
        
        self.rightLabel = label.Label(terminalio.FONT, text="t-0", color=0xFFFFFF)
        self.rightLabel.x = width - 8
        self.rightLabel.y = height + 4
        self.ui_group.append(self.rightLabel)
        
        self._draw_axis()
        
    def _draw_axis(self):
        self.bitmap.fill(0)
        bitmaptools.draw_line(self.bitmap, 0, 0, 0, self.height - 1, 1)
        bitmaptools.draw_line(self.bitmap, 0, self.height - 1, self.width - 1, self.height - 1, 1)
        
    def updateLeftLabel(self, inc):
        self.leftLabel.text = "t-"+str(inc)+"s"

    def draw(self, plot_points, x_range_recent, rmin, rmax):
        
        self.max_label.text = str(int(rmax))
        self.min_label.text = str(int(rmin))
        self.updateLeftLabel(x_range_recent)

        self._draw_axis()

        if not plot_points:
            return

        x_range = x_range_recent if x_range_recent > 0 else 1
        y_range = (rmax - rmin) if rmax != rmin else 1

        x_scale = (self.width - 2) / x_range
        y_scale = (self.height - 2) / y_range

        prev_px = None
        prev_py = None

        for x_time, y_val in plot_points:
            
            px = int(1 + (x_time * x_scale))
            py = int((self.height - 2) - ((y_val - rmin) * y_scale))
          
            px = max(1, min(px, self.width - 2))
            py = max(1, min(py, self.height - 2))

            if prev_px is not None:
                bitmaptools.draw_line(self.bitmap, prev_px, prev_py, px, py, 1)
            else:
                self.bitmap[px, py] = 1

            prev_px, prev_py = px, py
        
        
        print(plot_points)
#TODO
            

class DataGraph:
    def __init__(self, xpos, ypos, width, height, group):
        
        self.sparkgraph = SparkGraph(xpos, ypos, width, height, group)   
        
    def _getLastRange(self, data_log, time_log, x_range_recent):
        """ data log is a bunch of [33.3, 44.4, 55.5] data for say, temperature.
            now time_log is a bunch of corresponding TIME_BTWN at the time of measurement..
            data updates in parallel with its "waited-before" seconds in the time log at the same index
            
            first get the by_n_seconds counting backwards. all of those
            [33.3, 55.5, notskipping.notskip, blah blah, latest_temp]
            [3,    3,    3                  , 3        , 10]
            
            
            and return a thing that's sort of graphable"""
        

        start_idx = -1 # -1
        accumulated_time = 0
        
        
        for i in range(len(time_log) - 1, -1, -1):
            accumulated_time += time_log[i]
            if accumulated_time >= x_range_recent:
                start_idx = i #it goes one extra but that's ok
                break
             
        recent_data = []
        recent_time = []
        
        alignLeft = False
  
        if start_idx == -1:
            alignLeft = True
        else:
            alignLeft = False

        return start_idx, alignLeft

    def _getPlotPointsAndMinMax(self, data_log, time_log, x_range_recent):
        # CLAER PAST STUFF

        if not data_log or not time_log:
            return
        
        if len(data_log) != len(time_log):
            print("why is data log not the same length as time log")
            print(data_log)
            print(time_log)
            return


        start_idx, alignLeft = self._getLastRange(data_log, time_log, x_range_recent)
        if start_idx == -1: start_idx = 0
            # didnt find a startindex
        # start idx and forward..
        
        # for regular startFromLeft plot points..
        plot_points = []
        new_x_time = 0
        
        
        # everyminus is for offsetting them 
        everyminus = 0
        if not alignLeft:
            total_recent_time = sum(time_log[i] for i in range(start_idx, len(time_log))) # start_idx + 1 // OLDCODE
            everyminus = total_recent_time - x_range_recent
            
            
        rmax = float('-inf')
        rmin = float('inf')
        
        # GET PLOT POINTS
        for i in range(start_idx, len(data_log)):
        # Force elapsed time for the first point to 0
            delta_t = 0 if i == start_idx else time_log[i]
            new_x_time += delta_t
            plot_points.append((new_x_time - everyminus, data_log[i]))
            
            if data_log[i] < rmin: rmin = data_log[i]
            if data_log[i] > rmax: rmax = data_log[i]
            
        #if abs(rmin - rmax) < 2.0: #TODO
         
        rmin -= 0.2
        rmax += 0.2
            
        return plot_points, (rmin, rmax)
    
    def draw_the_shit(self, data_log, time_log, x_range_recent):
        plot_points, (rmin, rmax) = self._getPlotPointsAndMinMax(
            data_log, time_log, x_range_recent
        )

        self.sparkgraph.draw(plot_points, x_range_recent, rmin, rmax)
    

data_store = DataStore(bme680)


### DISPLAY STUFF

master_group = displayio.Group()
display.root_group = master_group

# permanent white background
color_palette = displayio.Palette(1)
color_palette[0] = 0x000000
bg_bitmap = displayio.Bitmap(200, 200, 1)
bg_tilegrid = displayio.TileGrid(bg_bitmap, pixel_shader=color_palette)
bg_line = Line(x0=0, y0=16, x1=200, y1=16, color=0xFFFFFF)

master_group.append(bg_tilegrid)
master_group.append(bg_line)

# bat group is premanently outside of the content group it's async updated
# do i really know waht async means not really
# its updated silently with other updates


bat_palette = displayio.Palette(2)
bat_palette[0] = 0x000000
bat_palette[1] = 0xFFFFFF

bat_bitmap = displayio.Bitmap(14, 8, 2)
bat_tilegrid = displayio.TileGrid(bat_bitmap, pixel_shader=bat_palette)

bat_group = displayio.Group(x=display.width - 15, y=1)
bat_group.append(bat_tilegrid)
master_group.append(bat_group)

def draw_battery_shell():
    # Clear bitmap
    bat_bitmap.fill(0)
    
    # Draw outer box (12x8)
    for x in range(0, 12):
        bat_bitmap[x, 0] = 1
        bat_bitmap[x, 7] = 1
    for y in range(0, 8):
        bat_bitmap[0, y] = 1
        bat_bitmap[11, y] = 1
        
    # Draw terminal tip on the right (2x4 pixels centered vertically)
    for y in range(2, 6):
        bat_bitmap[12, y] = 1
        bat_bitmap[13, y] = 1

draw_battery_shell()

def _update_battery(percentage=0.5):
    percentage = max(0.0, min(1.0, percentage))
    
    # Clear the inner fill area (columns 2 to 9, rows 2 to 5)
    for x in range(2, 10):
        for y in range(2, 6):
            bat_bitmap[x, y] = 0
            
    # Calculate how many columns to fill (max width is 8 pixels: cols 2 through 9)
    max_fill_width = 8
    fill_width = int(percentage * max_fill_width)
    
    # Draw the new fill pixels
    if fill_width > 0:
        for x in range(2, 2 + fill_width):
            for y in range(2, 6):
                bat_bitmap[x, y] = 1


content_group = displayio.Group()
master_group.append(content_group)



### PAGE ARCHITECTURE ###

class Page():
    def __init__(self, header_text=""):
        self.header_text = header_text
        self.group = displayio.Group()
        self.in_select_mode = False
        self.header_label = label.Label(
            terminalio.FONT, text=header_text, color=0xFFFFFF, x=3, y=5
        )
        self.group.append(self.header_label)
    
    def on_show(self):
        pass

    def set_header(self, text):
        """Helper to quickly change the top bar when entering select mode."""
        self.header_label.text = text

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
    
    def update_page(self):
        """Handle state changes and update page"""
        pass

    def data_schedule_update(self):
        pass

class DashboardPage(Page):
    def __init__(self, store):
        super().__init__(header_text="ALL data!")
        self.store = store

        # TEMPORARY layout
        self.temp_label = label.Label(terminalio.FONT, text="--.-", color=0xFFFFFF, x=6, y=25, scale=1)
        self.another = label.Label(terminalio.FONT, text="*C", color=0xFFFFFF, x=45, y=25, scale=1)
        self.hum_label = label.Label(terminalio.FONT, text="-- %", color=0xFFFFFF, x=6, y=40, scale=1)
        self.alt_label = label.Label(terminalio.FONT, text="-- %", color=0xFFFFFF, x=60, y=25, scale=1)
        self.press_label = label.Label(terminalio.FONT, text="-- %", color=0xFFFFFF, x=60, y=45, scale=1)

        self.group.append(self.temp_label)
        self.group.append(self.hum_label)
        self.group.append(self.alt_label)
        self.group.append(self.press_label)
        #self.group.append(self.another)

    def on_show(self):
        pass

    def on_short_select(self):
        pass

    def on_long_select(self):
        pass

    def on_short_next(self):
        pass

    def update_page(self):

        self.temp_label.text = f"{self.store.temp:.1f}"
        self.hum_label.text = f"{self.store.humidity:.1f} %"
        self.alt_label.text = f"{self.store.altitude:.1f} m"
        self.press_label.text = f"{self.store.pressure:.1f} hPa"

    def data_schedule_update(self):
        pass

class TemperaturePage(Page):
    def __init__(self, store):
        
        super().__init__(header_text="Temperature")
        self.store = store
        
        self.temp_lbl = label.Label(terminalio.FONT, text="--.- *C", color=0xFFFFFF, x=0, y=25, scale=1)
        self.hum_lbl = label.Label(terminalio.FONT, text="--.- %", color=0xFFFFFF, x=0, y=45, scale=1)
        self.group.append(self.temp_lbl)
        self.group.append(self.hum_lbl)
        
        self.graph_range = 10
        self.graph = DataGraph(xpos=40, ypos=18, width=80, height=40, group=self.group)
        
    def on_show(self):
        self.store.set_active_metric("temp")

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
        
        changed = self.store.checkAndUpdate()
        if changed:
            self.temp_lbl.text = f"{self.store.temp:.1f} *C"
        
        self.hum_lbl.text = f"{self.store.humidity:.1f} %"
            
    def data_schedule_update(self):
        readings = self.store.getVariableData()
        self.graph.draw_the_shit(readings.get_data_log(), readings.get_time_log(), self.graph_range)


class PressurePage(Page):
    def __init__(self, store):
        super().__init__(header_text="Barometer")
        self.store = store
        
        self.press_lbl = label.Label(terminalio.FONT, text="--.- hPa", color=0xFFFFFF, x=0, y=25, scale=1)
        self.alt_lbl = label.Label(terminalio.FONT, text="--.- m", color=0xFFFFFF, x=0, y=45, scale=1)
        self.group.append(self.press_lbl)
        self.group.append(self.alt_lbl)
        
        self.graph_range = 10
        self.graph = DataGraph(xpos=40, ypos=18, width=80, height=40, group=self.group)
    
    def on_show(self):
        self.store.set_active_metric("alt")

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
        
        changed = self.store.checkAndUpdate()
        if changed:
            self.alt_lbl.text = f"{self.store.altitude:.1f} m"
            
        self.press_lbl.text = f"{self.store.pressure:.1f} hPa"

    def data_schedule_update(self):
        readings = self.store.getVariableData()
        self.graph.draw_the_shit(readings.get_data_log(), readings.get_time_log(), self.graph_range)
        
pages = [
    DashboardPage(data_store),
    TemperaturePage(data_store),
    PressurePage(data_store)
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

while True:

    handle_buttons_modes() # update button modes booleans

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