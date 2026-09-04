import displayio, terminalio
from utilities import *
from Page import Page
from adafruit_display_shapes.line import Line
from adafruit_display_text import label
from adafruit_display_shapes.rect import Rect
from fonts import PRAGATI_54, BREMLIN_40, NINE_REG, NINE, SPLEEN_EIGHT, HAXOR


class Selector(displayio.Group):
    def __init__(self, x, y, width, height):
        super().__init__(x=x, y=y)
        self.width = width
        self.height = height
        
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
    def __init__(self, x, y, width, height):
        super().__init__(x=x, y=y, width=width, height=height)

        self.current_val = 0
        
        self.label = label.Label(
            terminalio.FONT, 
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
    
class StringSelector(Selector):
    def __init__(self, x, y, width, height, unitsList):
        super().__init__(x=x, y=y, width=width, height=height)

        self.current_index = 0
        self.unitsList = unitsList
        
        self.label = label.Label(
            terminalio.FONT, 
            text=str(self.unitsList[self.current_index]), 
            color=0xFFFFFF, 
            anchor_point=(0.5, 0.5), 
            anchored_position=(width // 2, height // 2)
        )
        self.append(self.label)
        
    def on_select(self):
        self.current_index += 1
        if self.current_index == len(self.unitsList):
            self.current_index = 0
            
        self.label.text = self.unitsList[self.current_index]
        
    def get_value(self):
        return self.unitsList[self.current_index]
    
    def set_active_unit(self, u):
        self.current_val = self.unitsList.index(u)


class IntervalGroup(displayio.Group):
    def __init__(self, x, y, width, height):
        super().__init__(x=x, y=y)
        self.width = width
        self.height = height

        
        self.append(label.Label(NINE, text="interval:", color=0xFFFFFF, 
            anchor_point=(0.0, 0.0),  anchored_position= (0, 0)))
        
        self.tens = NumberSelector(x=180, y=0, width=14, height=20)
        self.ones = NumberSelector(x=195, y=0, width=14, height=20)
        
        self.append(self.tens)
        self.append(self.ones)
        
        self.append(label.Label(terminalio.FONT, text="s", color=0xFFFFFF, 
            anchor_point=(0.0, 0.0),  
            anchored_position=(195 + 16, 4), scale=1))


class SeaLevelGroup(displayio.Group):
    def __init__(self, x, y, width, height):
        super().__init__(x=x, y=y)
        self.width = width
        self.height = height

        
        self.append(label.Label(NINE, text="sea level:", color=0xFFFFFF, 
            anchor_point=(0.0, 0.0),  anchored_position= (0, 0)))
        self.append(label.Label(terminalio.FONT, text="1 0", color=0xFFFFFF, 
            anchor_point=(0.0, 0.0),  anchored_position=(140, 4)))

        self.hPa1 = NumberSelector(x=160, y=0, width=14, height=20)
        self.hPa2 = NumberSelector(x=175, y=0, width=14, height=20)
        self.hPa3 = NumberSelector(x=195, y=0, width=14, height=20)
        
        self.append(self.hPa1)
        self.append(self.hPa2)
        self.append(self.hPa3)

        self.append(label.Label(HAXOR, text=".", color = 0x00FFFF,
        anchor_point=(0.0, 0.0),  anchored_position=(175 + 14, 3), scale=1))
        
        self.append(label.Label(terminalio.FONT, text="hPa", color=0xFFFFFF, 
            anchor_point=(0.0, 0.0),  
            anchored_position=(195 + 16, 4), scale=1))

class MeasurementUnitGroup(displayio.Group):
    def __init__(self, x, y, width, height):
        super().__init__(x=x, y=y)
        self.width = width
        self.height = height

        
        self.append(label.Label(NINE, text="measurement:", color=0xFFFFFF, 
            anchor_point=(0.0, 0.0),  anchored_position= (0, 0)))

        self.measurement_unit_selector = StringSelector(x=240 - 40 - 30, y=0, width=40, height=20, unitsList=["ft", "m"])
        self.measurement_unit_selector.set_active_unit("m") #TODO
        
        self.append(self.measurement_unit_selector)
        
class TemperatureUnitGroup(displayio.Group):
    def __init__(self, x, y, width, height):
        super().__init__(x=x, y=y)
        self.width = width
        self.height = height

        
        self.append(label.Label(NINE, text="temperature:", color=0xFFFFFF, 
            anchor_point=(0.0, 0.0),  anchored_position= (0, 0)))

        self.temp_selector = StringSelector(x=240 - 40 - 30, y=0, width=40, height=20, unitsList=["K", "F", "C"])
        self.temp_selector.set_active_unit("C") #TODO
        
        self.append(self.temp_selector)
                
                   

class SettingsPage(Page):
    def __init__(self, store):
        super().__init__(header_text="Settings")
        self.store = store
        self.is_editing = False

        self.sea_level_group = SeaLevelGroup(6, 30, 240 - 4, 30)
        self.group.append(self.sea_level_group)
        
        self.measurement_group = MeasurementUnitGroup(6, 60, 240 - 4, 30)
        self.group.append(self.measurement_group)
        
        self.temperature_group = TemperatureUnitGroup(6, 90, 240 - 4, 30)
        self.group.append(self.temperature_group)
                
        self.interval_group = IntervalGroup(6, 120, 240 - 4, 30)
        self.group.append(self.interval_group)
               
                
        ####
        self.selectors = [
            self.sea_level_group.hPa1,
            self.sea_level_group.hPa2,
            self.sea_level_group.hPa3,
            self.measurement_group.measurement_unit_selector,
            self.temperature_group.temp_selector,
            self.interval_group.tens,
            self.interval_group.ones,
        ]
        
        self.current_focus_index = 0
        
        
    def on_show(self):
        pass
    
    def on_long_select(self):
        self.is_editing = not self.is_editing
        
        if self.is_editing:
            self.selectors[self.current_focus_index].on_focus()
        else:
            self.selectors[self.current_focus_index].on_defocus()

    def on_short_select(self):
        if not self.is_editing:
            return
        
        self.selectors[self.current_focus_index].on_select()
        
    def on_short_next(self):
        if self.is_editing:
            self.selectors[self.current_focus_index].on_defocus()
            self.current_focus_index = (self.current_focus_index + 1) % len(self.selectors)
            self.selectors[self.current_focus_index].on_focus()
            return False

    def update_page(self):
        pass
            
    def data_schedule_update(self):
        pass