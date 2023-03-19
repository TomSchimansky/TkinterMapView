import os
import tkinter
import tkintermapview

# create tkinter window
root_tk = tkinter.Tk()
root_tk.geometry(f"{1000}x{700}")
root_tk.title("map_with_offline_tiles.py")

# path for the database to use
script_directory = os.path.dirname(os.path.abspath(__file__))
database_path = os.path.join(script_directory, "offline_tiles_nyc.db")

# create map widget and only use the tiles from the database, not the online server (use_database_only=True)
map_widget = tkintermapview.TkinterMapView(root_tk, width=1000, height=700, corner_radius=0,
                                           database_path=database_path, use_database_only=True, max_zoom=17)
map_widget.pack(fill="both", expand=True)

map_widget.set_address("nyc")

root_tk.mainloop()
