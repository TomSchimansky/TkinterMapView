from tkinter_map_widget import TkinterMapWidget
import os


MAIN_PATH = os.path.dirname(__file__)

TkinterMapWidget.load_offline_tiles(MAIN_PATH + "/offline_tiles", (53.777470, 9.610161), (53.718995, 9.723047), 0, 19)
