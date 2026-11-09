from PIL import Image, ImageTk
import tkinter
import os
from tkintermapview import TkinterMapView

# create tkinter window
root_tk = tkinter.Tk()
root_tk.geometry(f"{1000}x{700}")
root_tk.title("map_view_simple_example.py")

# create map widget
map_widget = TkinterMapView(root_tk, width=1000, height=700, corner_radius=0)
map_widget.pack(fill="both", expand=True)

# load images in PhotoImage object
tor_image = ImageTk.PhotoImage(Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "tor.jpg")).resize((300, 200)))
airport_image = ImageTk.PhotoImage(Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "airport.jpg")).resize((300, 200)))


# create marker through .set_address() with image, which is visible at zoom levels 14 to infinity
marker_1 = map_widget.set_address("Brandenburger Tor", marker=True, image=tor_image, image_zoom_visibility=(14, float("inf")))

# make image visible/invisible when marker is clicked
def click_airport_marker_event(marker):
    print("marker clicked:", marker.text)
    if marker.image_hidden is True:
        marker.hide_image(False)
    else:
        marker.hide_image(True)

# create marker through .set_marker() with image, which is visible at all zoom levels
marker_2 = map_widget.set_marker(52.47314336937092, 13.40380288606593, text="Old airport", image=airport_image,
                                 image_zoom_visibility=(0, float("inf")), command=click_airport_marker_event)
marker_2.hide_image(True)  # hide image

# create marker with custom colors and font
marker_3 = map_widget.set_marker(52.52084109254517, 13.409429827034389, text="Tower", text_color="green",
                                 marker_color_circle="black", marker_color_outside="gray40", font=("Helvetica Bold", 24))


root_tk.mainloop()