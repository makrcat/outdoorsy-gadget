
import displayio
import terminalio
import bitmaptools
from adafruit_display_text import label, wrap_text_to_pixels
from array import array

import math

DATA_RANGE = [15, 30]

def wrap_text(text, width, font):
    return "\n".join(wrap_text_to_pixels(
                text, width, font=font
            ))


def wrap_pos(text, a, b):
    if "\n" not in text: 
        return a
    return b

class RollingLog:
    def __init__(self, cols, header: tuple, max_len=5):
        self.max_len = max_len
        self.cols = cols
        self.log = []
        self.header = header

    def add_entry(self, entry_tuple: tuple):
        if len(entry_tuple) != self.cols:
            return
        if len(self.log) >= self.max_len:
            self.log.pop(0)
        self.log.append(entry_tuple)

    def get_row(self, index: int):
        return self.log[index]
        
    def len(self):
        return len(self.log)
    
    def getRows(self):
        return self.max_len
    
    def getCols(self):
        return self.cols


class Reading:
    def __init__(self, max_samples):
        self.log = array("f")
        self.read_size = 5
        self.max_samples = max_samples
        self.last_change = None
        
    def get_data_log(self):
        return self.log

    def addReading(self, r):
        if len(self.log) == self.max_samples:
            self.log[:] = self.log[1:] 
        self.log.append(r)

    def _shouldUpdate(self):
        log_len = len(self.log)
        if log_len < self.read_size:
            return False
        
        if self.last_change is None:
            return True

        start_idx = log_len - self.read_size
        total = sum(self.log[i] for i in range(start_idx, log_len))
        mean = total / self.read_size
        latest = self.log[-1]
            
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
        return self.log[-1]
        # should have updated before so that it's not empty. you can't get reading if you never updated the log
        



class DataStore:
    def __init__(self, sensor):
        self.sensor = sensor
        self.active_metric = None
        self.active_reading = None
        
        self.latest_values = {
            "temperature": 0, "humidity": 0, "pressure": 0,
            "altitude": 0, "gas_resistance": 0
        }
        
        self.settings = {
            "temperature_unit": "F",
            "measurement_unit": "m",
            "interval": 3.0,
        }
        
        self.rollingLog = RollingLog(3, ("temp", "alt", "aqi"))
        
    def logger_add(self, tple):
        self.rollingLog.add_entry(tple)
        
    def logger_get_row(self, r):
        self.rollingLog.get_row(r)
        
    def addLog(self):
        temp = self.getConvertedVal("temperature")
        hu = self.getVal("humidity")
        alt = self.getConvertedVal("altitude")
        tstuff = f"t:{temp}\nhu:{hu:.1f}"
        self.logger_add((tstuff, "hi", "hi"))
        
    def set_sea_level(self, val):
        self.sensor.sea_level_pressure = int(val)
        
    def get_sea_level(self):
        return self.sensor.sea_level_pressure

    def set_setting(self, key, value):
        if key not in self.settings:
            raise KeyError("That is not a valid key in settings")
        if key == "interval":
            value = float(value)
        self.settings[key] = value
        
    def get_setting(self, key):
        if key in self.settings:
            return self.settings[key]
        raise KeyError("That is not a valid key in settings")

    def getFL(self) -> float:
        temp_c = self.latest_values["temperature"]
        hum = self.latest_values["humidity"]
        e = (hum / 100.0) * 6.105 * math.exp((17.27 * temp_c) / (237.7 + temp_c))
        apparent_temp_c = temp_c + (0.33 * e) - 0.70
        return round(apparent_temp_c, 1)
    
    def getAQI(self) -> int:
        return 5

    def geteCO2(self) -> int:
        return 5000

    def getPressCat(self):
        p = self.getVal("pressure")
        if p <= 1000: return 0
        elif p <= 1008: return 1
        elif p <= 1023: return 2
        elif p <= 1033: return 3
        else: return 4
        
    def log10(self, n):
        return math.log(n) / math.log(10)
        
    def getBoilingPoint(self):
        p_mmhg = self.latest_values["pressure"] * 0.750062
        A, B, C = 8.07131, 1730.63, 233.426
        return (B / (A - self.log10(p_mmhg))) - C
        
    def getDewPoint(self):
        temp_c = self.latest_values["temperature"]
        rh = self.latest_values["humidity"]
        a, b = 17.625, 243.04
        alpha = ((a * temp_c) / (b + temp_c)) + math.log(rh / 100.0)
        return (b * alpha) / (a - alpha)
        
    def getVal(self, metric):
        if metric in self.latest_values:
            return self.latest_values[metric]
        elif metric == 'aqi': return self.getAQI()
        elif metric == 'eCO2': return self.geteCO2()
        elif metric == 'dewpoint': return self.getDewPoint()
        elif metric == 'boiling_point': return self.getBoilingPoint()
        elif metric == 'feels_like': return self.getFL()
        elif metric == 'pressure_category': return self.getPressCat()

    def getConvertedVal(self, metric) -> str:
        val = self.getVal(metric)
        if metric == 'altitude':
            if self.settings["measurement_unit"] == "ft":
                return round(val * 3.28084, 1)
            return round(val, 1)
        elif metric in ['temperature', 'feels_like', 'dewpoint', 'boiling_point']:
            if self.settings["temperature_unit"] == "F":
                return round(val * 9/5 + 32, 1)
            return round(val, 1)
        return val

    def update(self) -> None:
        try:
            offset = -4
            self.latest_values["temperature"] = self.sensor.temperature + offset
            self.latest_values["humidity"] = self.sensor.relative_humidity
            self.latest_values["pressure"] = self.sensor.pressure
            self.latest_values["altitude"] = self.sensor.altitude
            self.latest_values["gas_resistance"] = self.sensor.gas

            if self.active_metric is not None:
                active_val = self.getVal(self.active_metric)
                self.active_reading.addReading(active_val)
                
        except Exception as e:
            print("Sensor read error:", e)
       
    def set_active_metric(self, metric_name, range=None):
        if metric_name != self.active_metric:
            self.active_metric = metric_name
            
            if metric_name is not None:
                self.active_reading = Reading(int(range / self.settings["interval"]))
            else:
                self.active_reading = None
    
    def checkAndUpdate(self) -> bool:
        return self.active_reading.checkMaybeUpdate()

    def getVariableData(self):
        return self.active_reading
    
    def resize_active_reading(self, new_range):
        if self.active_reading is None:
            return
        
        interval = self.settings["interval"]

        
        required_samples = int(new_range / interval)
        
        old_data = self.active_reading.get_data_log()
        new_reading = Reading(required_samples)
        for val in old_data:
            new_reading.addReading(val)
            
        self.active_reading = new_reading



class SparkGraph:
    def __init__(self, xpos, ypos, width, height, group):
        self.xpos = xpos
        self.ypos = ypos
        self.width = width
        self.height = height
        self.group = group

        self.palette = displayio.Palette(3)
        self.palette[0] = 0x000000
        self.palette[1] = 0xFFFFFF
        self.palette[2] = 0x444444
            
        self.ui_group = displayio.Group(x=xpos, y=ypos)
        self.group.append(self.ui_group)

        self.bitmap = displayio.Bitmap(width, height, len(self.palette))
        self.tile_grid = displayio.TileGrid(self.bitmap, pixel_shader=self.palette)
        self.ui_group.append(self.tile_grid)

        self.max_label = label.Label(terminalio.FONT, text="", color=0xFFFFFF)
        self.max_label.x, self.max_label.y = 4, 7
        self.ui_group.append(self.max_label)

        self.min_label = label.Label(terminalio.FONT, text="", color=0xFFFFFF)
        self.min_label.x, self.min_label.y = 4, height - 10
        self.ui_group.append(self.min_label)
        
        self.leftLabel = label.Label(terminalio.FONT, text="t-xs", color=0xFFFFFF)
        self.leftLabel.x, self.leftLabel.y = 0, height + 4
        self.ui_group.append(self.leftLabel)
        
        self.rightLabel = label.Label(terminalio.FONT, text="t-0", color=0xFFFFFF)
        self.rightLabel.x, self.rightLabel.y = width - 18, height + 4
        self.ui_group.append(self.rightLabel)
        
        self._draw_axis()

    def _draw_rectangle(self, x, y, width, height, color_index):
        bitmaptools.draw_line(self.bitmap, x, y, x + width - 1, y, color_index)
        bitmaptools.draw_line(self.bitmap, x + width - 1, y, x + width - 1, y + height - 1, color_index)
        bitmaptools.fill_region(self.bitmap, x, (y + height - 3), x + width, y + height, color_index)
        bitmaptools.fill_region(self.bitmap, x, y, x + 3, y + height, color_index)

    def _draw_grid(self, ylines, xlines):
        wunit = int(self.width / (xlines + 1))
        hunit = int(self.height / (ylines + 1))
        for i in range(1, xlines + 2):
            bitmaptools.draw_line(self.bitmap, wunit * i, 0, wunit * i, self.height, 2)
        for j in range(1, ylines + 2):
            bitmaptools.draw_line(self.bitmap, 0, hunit * j, self.width, hunit * j, 2)
            
    def _draw_axis(self):
        self.bitmap.fill(0)
        self._draw_grid(2, 3)
        self._draw_rectangle(0, 0, self.width, self.height, 1)
        
    def updateLeftLabel(self, inc):
        self.leftLabel.text = f"t-{inc}s"

    def draw(self, plot_points, x_range_recent, rmin, rmax, label):
        
        
        self.max_label.text = str(int(rmax))
        self.min_label.text = str(int(rmin))
        self.updateLeftLabel(label)

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
            py = max(1, min(py, self.height - 2))

            if prev_px is not None:
                x1 = max(1, min(prev_px, self.width - 2))
                x2 = max(1, min(px, self.width - 2))
                if x1 != x2:
                    bitmaptools.draw_line(self.bitmap, x1, prev_py, x2, py, 1)
            else:
                if 1 <= px < self.width - 1:
                    self.bitmap[px, py] = 1

            prev_px = px
            prev_py = py
            

class DataGraph:
    def __init__(self, xpos, ypos, width, height, group):
        self.sparkgraph = SparkGraph(xpos, ypos, width, height, group)   

    def draw_the_shit(self, data_log, interval, max_samples):
        start_idx = max(0, len(data_log) - max_samples)
        
        plot_points = []
        new_x_time = 0
        rmax = float('-inf')
        rmin = float('inf')

        for i in range(start_idx, len(data_log)):
            val = data_log[i]
            plot_points.append((new_x_time, val))
            new_x_time += interval
            if val < rmin: rmin = val
            if val > rmax: rmax = val

        rmin -= 0.2
        rmax += 0.2

        # Calculate the exact time span based on the sample window slots (N - 1 intervals)
        total_time_span = (max_samples - 1) * interval 
        lbl = int((max_samples) * interval )

        self.sparkgraph.draw(plot_points, int(total_time_span), rmin, rmax, lbl)
        
    
class tempGradientObject:
    def __init__(self, xpos, ypos, width, height, pc, colorz, group, orientation="vertical"):
        self.xpos = xpos
        self.ypos = ypos
        self.width = width
        self.height = height
        
        if orientation == 'horizontal':
            self.value = (pc * self.width)
        else:
            self.value = (pc * self.height)
            
        self.colorz = colorz
        self.group = group
        self.orientation = orientation
        self.background = 0x444444
        
        if self.orientation == "horizontal":
            self.steps = self.width
        else:
            self.steps = self.height

        self.palette = displayio.Palette(1 + self.steps)
        
        color_list = self.outputHEXfrom()
        for i in range(0, self.steps):
            self.palette[i] = color_list[i]

        self.palette[self.steps] = self.background # last color as black background

        if self.orientation == "horizontal":
            self.bitmap = displayio.Bitmap(self.width, 1, len(self.palette))
            self.tile_grid = displayio.TileGrid(
                self.bitmap, pixel_shader=self.palette, x=self.xpos, y=self.ypos,
                width=1, height=self.height, tile_width=self.width, tile_height=1
            )
        else:
            self.bitmap = displayio.Bitmap(1, self.height, len(self.palette))
            self.tile_grid = displayio.TileGrid(
                self.bitmap, pixel_shader=self.palette, x=self.xpos, y=self.ypos,
                width=self.width, height=1, tile_width=1, tile_height=self.height
            )

        self.group.append(self.tile_grid)   
        self._draw()

    def _timesrepeatedAndRemainder(self, step, total):
        times_repeated = total // step
        remainder = total % step
        return int(times_repeated), remainder

    def _interpolate_color(self, color_start, color_end, ratio):
        r_start = (color_start >> 16) & 0xFF
        g_start = (color_start >> 8) & 0xFF
        b_start = color_start & 0xFF

        r_end = (color_end >> 16) & 0xFF
        g_end = (color_end >> 8) & 0xFF
        b_end = color_end & 0xFF

        r_interp = int(r_start + (r_end - r_start) * ratio)
        g_interp = int(g_start + (g_end - g_start) * ratio)
        b_interp = int(b_start + (b_end - b_start) * ratio)

        return (r_interp << 16) | (g_interp << 8) | b_interp

    def outputHEXfrom(self):
        listofcolors = []
        colors = self.colorz
        pixels = self.steps

        stops = len(colors)
        step_length = pixels / (stops - 1)

        for i in range(1, pixels):
            if i <= self.value:
                pixel_index = i - 1
                times_repeated, remainder = self._timesrepeatedAndRemainder(step_length, pixel_index)
                color_start = colors[times_repeated]
                color_end = colors[times_repeated + 1]

                remainder_ratio = remainder / step_length
                color = self._interpolate_color(color_start, color_end, remainder_ratio)
                listofcolors.append(color)
            else:
                listofcolors.append(self.background)

        if self.value == pixels:
            listofcolors.append(colors[-1])
        else:
            listofcolors.append(self.background)

        return listofcolors

    def _draw(self):
        if self.orientation == "horizontal":
            
            for x in range(self.width):
                self.bitmap[x, 0] = x
        else:
            
            for y in range(self.height):
                color_index = self.height - 1 - y 
                self.bitmap[0, y] = color_index

    def update(self, pc):
        self.value = int(pc * self.height)
        
        color_list = self.outputHEXfrom()
        for i in range(len(color_list)):
            self.palette[i] = color_list[i]
            
        self._draw()

            
