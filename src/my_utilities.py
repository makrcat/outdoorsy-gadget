
import displayio
import terminalio
import time
import bitmaptools
from adafruit_display_text import label
import adafruit_display_text

import math

TIME_BTWN = 1.0
MAX_SAMPLES = 240
DATA_RANGE = [10, 30, 60, 120, 240]

def wrap_text(text, width, font):
    return "\n".join(adafruit_display_text.wrap_text_to_pixels(
                text, width, font=font
            ))

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
        self.active_metric = "temperature"
        self.active_reading = Reading()
        
        self.latest_values = {
            "temperature": 0,
            "humidity": 0,
            "pressure": 0,
            "altitude": 0,
            "gas_resistance": 0
        }
        
        self.settings = {
            "temperature_unit": "F",
            "measurement_unit": "m",
            "interval": 3.0,
        }
        
    def set_sea_level(self, val):
        self.sensor.sea_level_pressure = int(val)
        
    def get_sea_level(self):
        return self.sensor.sea_level_pressure

    def set_setting(self, key, value):
        if key in self.settings:
            self.settings[key] = value
        else:
            raise KeyError("That is not a valid key in settings")
        
    def get_setting(self, key):
        if key in self.settings:
            return self.settings[key]
        else:
            raise KeyError("That is not a valid key in settings")

    def getFL(self) -> float:
        temp_c = self.latest_values["temperature"]
        hum = self.latest_values["humidity"]

        # Approximate water vapor pressure (hPa) from temp and humidity
        # e = (humidity / 100) * 6.105 * exp((17.27 * temp) / (237.7 + temp))
        e = (hum / 100.0) * 6.105 * math.exp((17.27 * temp_c) / (237.7 + temp_c))

        # Steadman's approximation formula: Apparent Temp = T + 0.33 * e - 0.70 * wind - 4.0
        apparent_temp_c = temp_c + (0.33 * e) - 0.70
            
        return round(apparent_temp_c, 1)
    
    def getAQI(self) -> int:
        return 5

    def geteCO2(self) -> int:
        return 5000

    def getPressCat(self):
        p = self.getVal("pressure") 
        
        if p <= 1000:
            return 0
        elif p <= 1008:
            return 1
        elif p <= 1023:
            return 2
        elif p <= 1033:
            return 3
        else:
            return 4
        
    def log10(self, n):
        result = math.log(n) / math.log(10)
        return result
        
    def getBoilingPoint(self):
        p_mmhg = self.latest_values["pressure"] * 0.750062
    
        A = 8.07131
        B = 1730.63
        C = 233.426
        
        boiling_temp_c = (B / (A - self.log10(p_mmhg))) - C
        return boiling_temp_c
        
        
    def getDewPoint(self):
        
        temp_c = self.latest_values["temperature"]
        rh = self.latest_values["humidity"]

        a = 17.625
        b = 243.04 
        

        alpha = ((a * temp_c) / (b + temp_c)) + math.log(rh / 100.0)
        dew_point_c = (b * alpha) / (a - alpha)
        return dew_point_c
        
    def getVal(self, metric):
        if metric == 'gas_resistance':
            return self.latest_values["gas_resistance"]
        elif metric == 'altitude':
            return self.latest_values["altitude"]
        elif metric == 'pressure':
            return self.latest_values["pressure"]
        elif metric == 'humidity':
            return self.latest_values["humidity"]
        elif metric == 'temperature':
            return self.latest_values["temperature"]
        
        elif metric == 'aqi':
            return self.getAQI()
        elif metric == 'eCO2':
            return self.geteCO2()
        elif metric == 'dewpoint':
            return self.getDewPoint()
        elif metric == 'boiling_point':
            return self.getBoilingPoint()
        elif metric == 'feels_like':
            return self.getFL()
        elif metric == 'pressure_category':
            return self.getPressCat()
        

    def getConvertedVal(self, metric) -> str:
        val = self.getVal(metric)
        
        
        ## FT / M conversion
        if metric == 'altitude':
            if self.settings["measurement_unit"] == "ft":
                return round(val * 3.28084, 1)
            return round(val, 1)
        
        
        ## F / C conversion
        elif metric in ['temperature', 'feels_like', 'dewpoint', 'boiling_point']:
            if self.settings["temperature_unit"] == "F": 
                f_val = val * 9/5 + 32
                return round(f_val, 1)
            return round(val, 1)
        
        else:
            return val
        
        
        
        

    def update(self) -> None:
        try:
            offset = -4

            self.latest_values["temperature"] = self.sensor.temperature + offset
            self.latest_values["humidity"] = self.sensor.relative_humidity
            self.latest_values["pressure"] = self.sensor.pressure
            self.latest_values["altitude"] = self.sensor.altitude
            self.latest_values["gas_resistance"] = self.sensor.gas


            active_val = self.getVal(self.active_metric)
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
        self.max_label.x = 4
        self.max_label.y = 7
        self.ui_group.append(self.max_label)

        self.min_label = label.Label(terminalio.FONT, text="", color=0xFFFFFF)
        self.min_label.x = 4
        self.min_label.y = height - 10
        self.ui_group.append(self.min_label)
        
        self.leftLabel = label.Label(terminalio.FONT, text="t-60s", color=0xFFFFFF)
        self.leftLabel.x = 0
        self.leftLabel.y = height + 4
        self.ui_group.append(self.leftLabel)
        
        self.rightLabel = label.Label(terminalio.FONT, text="t-0", color=0xFFFFFF)
        self.rightLabel.x = width - 18
        self.rightLabel.y = height + 4
        self.ui_group.append(self.rightLabel)
        
        self._draw_axis()

    def _draw_rectangle(self, x, y, width, height, color_index):
        # Top edge
        bitmaptools.draw_line(self.bitmap, x, y, x + width - 1, y, color_index)
        # Right edge
        bitmaptools.draw_line(self.bitmap, x + width - 1, y, x + width - 1, y + height - 1, color_index)
        # Bottom edge

        bitmaptools.fill_region(
            self.bitmap, 
            x,
            (y + height - 3),
            x + width, 
            y + height,
            color_index
        )
                
        bitmaptools.fill_region(
            self.bitmap, 
            x,
            y,
            x + 3,
            y + height,
            color_index
        )
        

    def _draw_grid(self, ylines, xlines):

        wunit = int(self.width / (xlines + 1))
        hunit = int(self.height / (ylines + 1))

        for i in range(1, xlines + 1 + 1):
            bitmaptools.draw_line(self.bitmap, wunit * i, 0, wunit * i, self.height, 2)

        for j in range(1, ylines + 1 + 1):
            bitmaptools.draw_line(self.bitmap, 0, hunit * j, self.width, hunit * j, 2)

                
    def _draw_axis(self):
        self.bitmap.fill(0)
        self._draw_grid(2,3 )
        self._draw_rectangle(0, 0, self.width, self.height, 1)

   
        
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
    
class tempGradientObject:
    def __init__(self, xpos, ypos, width, height, pc, colorz, group, orientation="vertical"):
        self.xpos = xpos
        self.ypos = ypos
        self.width = width
        self.height = height
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

            
