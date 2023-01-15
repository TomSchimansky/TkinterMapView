import os
import tkinter
import tkintermapview
from PIL import Image, ImageTk

# create tkinter window
root_tk = tkinter.Tk()
root_tk.geometry(f"{1000}x{700}")
root_tk.title("map_view_simple_example.py")

# create map widget
map_widget = tkintermapview.TkinterMapView(root_tk, width=1000, height=700, corner_radius=0)
map_widget.pack(fill="both", expand=True)

# load images
current_path = os.path.join(os.path.dirname(os.path.abspath(__file__)))
plane_image = ImageTk.PhotoImage(Image.open(os.path.join(current_path, "images", "plane.png")).resize((40, 40)))
plane_circle_1_image = ImageTk.PhotoImage(Image.open(os.path.join(current_path, "images", "plane_circle_1.png")).resize((35, 35)))
plane_circle_2_image = ImageTk.PhotoImage(Image.open(os.path.join(current_path, "images", "plane_circle_2.png")).resize((35, 35)))
airport_image = ImageTk.PhotoImage(Image.open(os.path.join(current_path, "images", "airport.jpg")).resize((100, 70)))


def marker_callback(marker):
    print(marker.text)
    marker.delete()


# create markers
marker_1 = map_widget.set_marker(52.476062, 13.394172, text="Plane 1", icon=plane_image, command=marker_callback)
marker_2 = map_widget.set_marker(52.352659, 13.499669, text="Plane 2", icon=plane_circle_1_image,
                                 image=airport_image, command=marker_callback)
# root_tk.after(3000, lambda: marker_2.change_icon(plane_image))

# set initial position of map widget
map_widget.set_address("Airport Berlin BER")
map_widget.set_zoom(11)

root_tk.mainloop()
