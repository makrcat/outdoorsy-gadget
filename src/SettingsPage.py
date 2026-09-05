import displayio
import terminalio
from my_utilities import *
from Page import Page
from adafruit_display_shapes.line import Line
from adafruit_display_text import label
from adafruit_display_shapes.rect import Rect
from fonts import NINE_REG


class Selector(displayio.Group):
    def __init__(self, x, y, width, height, parent):
        super().__init__(x=x, y=y)
        self.width = width
        self.height = height
        self.parent = parent
        
        self.bg_rect = Rect(0, 0, width, height, fill=0x444444, outline=0xFFFFFF)
        self.append(self.bg_rect)
    

    def on_focus(self):
        self.bg_rect.outline = 0xFF0000
        
    def on_defocus(self):
        self.bg_rect.outline = 0xFFFFFF
        
    def on_select(self):
        pass

    def get_value(self):
        return None
    

class NumberSelector(Selector):
    def __init__(self, x, y, width, height, parent):
        super().__init__(x=x, y=y, width=width, height=height, parent=parent)
        self.current_val = 0
        
        self.label = label.Label(
            NINE_REG, 
            text=str(self.current_val), 
            color=0xFFFFFF, 
            anchor_point=(0.5, 0.5), 
            anchored_position=(width // 2, height // 2)
        )
        self.append(self.label)
        
    def on_select(self):
        self.current_val += 1
        if self.current_val > 9:
            self.current_val = 0
            
        self.label.text = str(self.current_val)
        
    def get_value(self):
        return self.current_val
    
    def set_selected(self, u):
        if 0 <= u <= 9:
            self.current_val = u
            self.label.text = str(self.current_val)
    

class StringSelector(Selector):
    def __init__(self, x, y, width, height, unitsList, parent):
        super().__init__(x=x, y=y, width=width, height=height, parent=parent)
        
        self.current_index = 0
        self.unitsList = unitsList
        
        self.label = label.Label(
            NINE_REG, 
            text=str(self.unitsList[self.current_index]), 
            color=0xFFFFFF, 
            anchor_point=(0.5, 0.5), 
            anchored_position=(width // 2, height // 2)
        )
        self.append(self.label)
        
    def on_select(self):
        self.current_index += 1
        if self.current_index >= len(self.unitsList):
            self.current_index = 0
            
        self.label.text = self.unitsList[self.current_index]
        
    def get_value(self):
        return self.unitsList[self.current_index]
    
    def set_selected(self, u):
        if u in self.unitsList:
            self.current_index = self.unitsList.index(u)
            self.label.text = self.unitsList[self.current_index]


class IntervalGroup(displayio.Group):
    def __init__(self, x, y, width, height, store):
        super().__init__(x=x, y=y)
        self.width = width
        self.height = height
        self.store = store

        self.append(label.Label(NINE_REG, text="interval:", color=0xFFFFFF, 
            anchor_point=(0.0, 0.0),  anchored_position=(0, 0)))
        
        self.tens = NumberSelector(x=180, y=0, width=14, height=20, parent=self)
        self.ones = NumberSelector(x=195, y=0, width=14, height=20, parent=self)
        
        self.append(self.tens)
        self.append(self.ones)
        
        self.append(label.Label(NINE_REG, text="s", color=0xFFFFFF, 
            anchor_point=(0.0, 0.0),  
            anchored_position=(195 + 16, 1), scale=1))
        
        self._load()
            
    def _load(self):
        interval_val = self.store.get_setting("interval") or 0
        self.tens.set_selected(int(interval_val // 10))
        self.ones.set_selected(int(interval_val % 10))
        
    def update_value(self, store):
        tens = self.tens.get_value()
        ones = self.ones.get_value()
        result = 10 * int(tens) + int(ones)
        store.set_setting("interval", result)
            

class SeaLevelGroup(displayio.Group):
    def __init__(self, x, y, width, height, store):
        super().__init__(x=x, y=y)
        self.width = width
        self.height = height
        self.store = store

        self.append(label.Label(NINE_REG, text="sea level:", color=0xFFFFFF, 
            anchor_point=(0.0, 0.0),  anchored_position=(0, 0)))
        self.append(label.Label(NINE_REG, text="10", color=0xFFFFFF, 
            anchor_point=(0.0, 0.0),  anchored_position=(130, 1)))

        self.hPa1 = NumberSelector(x=150, y=0, width=14, height=20, parent=self)
        self.hPa2 = NumberSelector(x=165, y=0, width=14, height=20, parent=self)
        self.hPa3 = NumberSelector(x=185, y=0, width=14, height=20, parent=self)
        
        self.append(self.hPa1)
        self.append(self.hPa2)
        self.append(self.hPa3)

        self.append(label.Label(NINE_REG, text=".", color=0x00FFFF,
            anchor_point=(0.0, 0.0),  anchored_position=(165 + 12, 3), scale=1))
        
        self.append(label.Label(NINE_REG, text="hPa", color=0xFFFFFF, 
            anchor_point=(0.0, 0.0),  
            anchored_position=(185 + 16, 1), scale=1))
        
        self._load()
        
        
    def _load(self):
        val = self.store.get_sea_level()
        
        # remove 100 get the remaining part 17.2
        remainder = val - 1000.0
        
        h1 = int(remainder // 10) 
        h2 = int(remainder % 10)
        h3 = int(round((remainder * 10) % 10))

        self.hPa1.set_selected(h1)
        self.hPa2.set_selected(h2)
        self.hPa3.set_selected(h3)
            
    def update_value(self, store):
        h1 = int(self.hPa1.get_value())
        h2 = int(self.hPa2.get_value())
        h3 = int(self.hPa3.get_value())
        
        result = 1000.0 + (h1 * 10.0) + h2 + (h3 / 10.0)
        store.set_sea_level(result)
        

class MeasurementUnitGroup(displayio.Group):
    def __init__(self, x, y, width, height, store):
        super().__init__(x=x, y=y)
        self.width = width
        self.height = height
        self.store = store

        self.append(label.Label(NINE_REG, text="measurement:", color=0xFFFFFF, 
            anchor_point=(0.0, 0.0),  anchored_position=(0, 0)))

        self.measurement_unit_selector = StringSelector(
            x=240 - 40 - 30, y=0, width=40, height=20, 
            unitsList=["ft", "m"], parent=self
        )
        self.append(self.measurement_unit_selector)
        
        self._load()
        
    def _load(self):
        self.measurement_unit_selector.set_selected(self.store.get_setting("measurement_unit")) 
        
    def update_value(self, store):
        store.set_setting("measurement_unit", self.measurement_unit_selector.get_value())   
    
        
class TemperatureUnitGroup(displayio.Group):
    def __init__(self, x, y, width, height, store):
        super().__init__(x=x, y=y)
        self.width = width
        self.height = height
        self.store = store
        
        self.append(label.Label(NINE_REG, text="temperature:", color=0xFFFFFF, 
            anchor_point=(0.0, 0.0),  anchored_position=(0, 0)))

        self.temp_selector = StringSelector(
            x=240 - 40 - 30, y=0, width=40, height=20, 
            unitsList=["K", "F", "C"], parent=self
        )
        self.append(self.temp_selector)
        
        self._load()
        
    def _load(self):
        self.temp_selector.set_selected(self.store.get_setting("temperature_unit")) 
        
    def update_value(self, store):
        store.set_setting("temperature_unit", self.temp_selector.get_value())
                   

class SettingsPage(Page):
    def __init__(self, store):
        super().__init__(header_text="Settings")
        self.store = store
        self.is_editing = False

        self.sea_level_group = SeaLevelGroup(6, 30, 240 - 4, 30, store)
        self.group.append(self.sea_level_group)
        
        self.measurement_group = MeasurementUnitGroup(6, 60, 240 - 4, 30, store)
        self.group.append(self.measurement_group)
        
        self.temperature_group = TemperatureUnitGroup(6, 90, 240 - 4, 30, store)
        self.group.append(self.temperature_group)
                
        self.interval_group = IntervalGroup(6, 120, 240 - 4, 30, store)
        self.group.append(self.interval_group)
               
        self.cur_i = 0
        
        self.selectors = [
            self.sea_level_group.hPa1,
            self.sea_level_group.hPa2,
            self.sea_level_group.hPa3,
            self.measurement_group.measurement_unit_selector,
            self.temperature_group.temp_selector,
            self.interval_group.tens,
            self.interval_group.ones,
        ]
        
    def on_show(self):
        pass
    
    def on_long_select(self):
        self.is_editing = not self.is_editing
        
        if self.is_editing:
            self.selectors[self.cur_i].on_focus()
        else:
            self.selectors[self.cur_i].on_defocus()

    def on_short_select(self):
        if not self.is_editing:
            return
        
        selector = self.selectors[self.cur_i]
        selector.on_select()
        
        
        selector.parent.update_value(self.store)
        
    def on_short_next(self):
        if self.is_editing:
            self.selectors[self.cur_i].on_defocus()
            self.cur_i = (self.cur_i + 1) % len(self.selectors)
            self.selectors[self.cur_i].on_focus()
            return False

    def update_page(self):
        pass
            
    def data_schedule_update(self):
        pass