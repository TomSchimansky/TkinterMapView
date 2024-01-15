import tkinter
import os
from tkintermapview import TkinterMapView

# create tkinter window
root_tk = tkinter.Tk()
root_tk.geometry(f"{1000}x{700}")
root_tk.title("map_view_simple_example.py")

# path for the database to use
script_directory = os.path.dirname(os.path.abspath(__file__))
database_path = os.path.join(script_directory, "offline_tiles.db")

# create map widget and only use the tiles from the database, not the online server (use_database_only=True)
map_widget = TkinterMapView(root_tk, width=1000, height=700, corner_radius=0, use_database_only=True,
                            max_zoom=17, database_path=database_path)
map_widget.pack(fill="both", expand=True)
map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga")
#map_widget.set_overlay_tile_server("http://tiles.openseamap.org/seamark//{z}/{x}/{y}.png")

map_widget.set_address("nyc")

root_tk.mainloop()
