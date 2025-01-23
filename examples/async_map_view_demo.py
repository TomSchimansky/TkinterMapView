import tkinter
import tkintermapview
from async_tkinter_loop import async_mainloop

# create tkinter window
root_tk = tkinter.Tk()
root_tk.geometry(f"{1000}x{700}")
root_tk.title("map_view_simple_example.py")

# create map widget
map_widget = tkintermapview.AsyncTkinterMapView(root_tk, width=9000, height=600, corner_radius=10)
map_widget.pack(fill="both", expand=True)

# set other tile server (standard is OpenStreetMap)
map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)  # google normal
# map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)  # google satellite

# set current position and zoom
# map_widget.set_position(52.516268, 13.377695, marker=False)  # Berlin, Germany
# map_widget.set_zoom(17)

# set current position with address
# map_widget.set_address("Berlin Germany", marker=False)

def marker_click(marker):
    print(f"marker clicked - text: {marker.text}  position: {marker.position}")

# set a position marker (also with a custom color and command on click)
marker_2 = map_widget.set_marker(52.516268, 13.377695, text="Brandenburger Tor", command=marker_click)
marker_3 = map_widget.set_marker(52.55, 13.4, text="52.55, 13.4")
# marker_3.set_position(...)
# marker_3.set_text(...)
# marker_3.delete()

# set a path
path_1 = map_widget.set_path([marker_2.position, marker_3.position, (52.568, 13.4), (52.569, 13.35)])
# path_1.add_position(...)
# path_1.remove_position(...)
# path_1.delete()

# root_tk.mainloop()
async_mainloop(root_tk)
