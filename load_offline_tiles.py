from tkinter_map_widget import TkinterMapWidget
import os

MAIN_PATH = os.path.dirname(__file__)

upper_left_corner = (53.777470, 9.610161)
lower_right_corner = (53.718995, 9.723047)

zoom_begin = 0
zoom_end = 0

TkinterMapWidget.load_offline_tiles(MAIN_PATH + "/offline_tiles",
                                    upper_left_corner, lower_right_corner, zoom_begin, zoom_end)
