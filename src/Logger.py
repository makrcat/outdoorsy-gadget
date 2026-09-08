import displayio, terminalio
from my_utilities import *
from Page import Page
from adafruit_display_text import label
from fonts import NINE_REG, SUBTEN


class TopTableView(displayio.Group):
    def __init__(self, xpos, ypos, width, height, rollingLog):
        super().__init__(x=xpos, y=ypos)
        
        self.width = width
        self.height = height
        self.rollingLog = rollingLog
        
        self.header_height = 22
        
        self.cellwidth = int(self.width / self.rollingLog.getCols())
        
        remaining_height = self.height - self.header_height
        self.cellheight = int(remaining_height / self.rollingLog.max_len)
        
        self.cell_labels = []
        
        self.palette = displayio.Palette(3)
        self.palette[0] = 0x000000
        self.palette[1] = 0xFFFFFF
        self.palette[2] = 0x444444
        
        self.bitmap = displayio.Bitmap(width, height, len(self.palette))
        self.tile_grid = displayio.TileGrid(self.bitmap, pixel_shader=self.palette)
        self.append(self.tile_grid)
        
        self._draw_header()
        self._draw_grid_lines()
        self._init_labels()
        
    def _draw_header(self):

        bitmaptools.fill_region(
            self.bitmap,
            x1=0, y1=0,
            x2=self.width, y2=self.header_height,
            value=1
        )
        
        bitmaptools.fill_region(
            self.bitmap, 
            x1=1, y1=1, 
            x2=self.width -1, y2=self.header_height, 
            value=2
        )
        
        
        for c in range(self.rollingLog.getCols()):
            header_thing = str(self.rollingLog.header[c])
            
            header_lbl = label.Label(NINE_REG, text=header_thing, color=0xFFFF00)
            header_lbl.anchor_point = (0.5, 0.5)
            x = int(c * self.cellwidth) + int(self.cellwidth / 2)
            y = int(self.header_height / 2)
            header_lbl.anchored_position = (x, y)
            
            self.append(header_lbl)
            
    def _draw_grid_lines(self):
        line_color_index = 1 
        

        for col in range(self.rollingLog.getCols() + 1):
            x = col * self.cellwidth
            if x >= self.width: 
                x = self.width - 1
                
            bitmaptools.fill_region(
                self.bitmap, 
                x1=x, y1=0, 
                x2=x + 1, y2=self.height -2, 
                value=line_color_index
            )
            

        for row in range(self.rollingLog.max_len + 1):
            y = self.header_height + (row * self.cellheight)
            if y >= self.height: 
                y = self.height - 1
                
            bitmaptools.fill_region(
                self.bitmap, 
                x1=0, y1=y, 
                x2=self.width, y2=y + 1, 
                value=line_color_index
            )
        
    def _init_labels(self):
        self.cell_labels = []
        current_log_len = len(self.rollingLog.log)
        
        for r in range(self.rollingLog.max_len):
            row_labels = []
            for c in range(self.rollingLog.getCols()):
                if r < current_log_len:
                    val = str(self.rollingLog.get_row(r)[c])
                else:
                    val = ""
                    
                lbl = label.Label(font=NINE_REG, text=val, line_spacing=0.9, color=0xFFFFFF,
                                  anchor_point = (0.0, 0.0))
                
                lbl.anchored_position= (
                    int(c * self.cellwidth) + 2,
                    int(self.header_height + (r * self.cellheight) + 1)
                )
                
                self.append(lbl)
                row_labels.append(lbl)
                
            self.cell_labels.append(row_labels)
            
    def __refresh_data__(self):
        current_log_len = len(self.rollingLog.log)
        
        for r in range(self.rollingLog.max_len):
            for c in range(self.rollingLog.getCols()):
                if r < current_log_len:
                    val = str(self.rollingLog.get_row(r)[c])
                else:
                    val = ""
                self.cell_labels[r][c].text = val


class LoggerPage(Page):
    def __init__(self, store):
        super().__init__(header_text="Logger")
        self.store = store
        
        self.table_view = TopTableView(10, 30, 220, 180, store.rollingLog)
        self.group.append(self.table_view)
        
        self.sub = label.Label(SUBTEN, text="Most recent data is on top!", anchor_point=(0.5, 0.5),
                               anchored_position=(120, 220), color=0xFFFFFF)
        self.group.append(self.sub)
        
    def on_show(self):
        self.store.set_active_metric(None)

    def on_short_select(self):
        pass

    def on_long_select(self):
        pass

    def on_short_next(self):
        pass 

    def update_page(self):
        pass
            
    def data_schedule_update(self):
        pass
