![PyPI](https://img.shields.io/pypi/v/tkintermapview)
![PyPI - Downloads](https://img.shields.io/pypi/dm/tkintermapview?color=green&label=pip%20downloads)
![PyPI - License](https://img.shields.io/pypi/l/customtkinter)

# TkinterMapView - simple Tkinter map component

![](documentation_images/map_view_example.png)

TkinterMapView is a tile based interactive map renderer widget for the python Tkinter library.
By default, it displays the OpenStreetMap map, but you can change the tile server to
whatever you like, and it also supports a second tile server for overlays like OpenSeaMap.
You can set the current focus of the widget by a position or address, and place markers 
or a path on the map.

The above image program is produced by the code example `map_view_simple_example.py`.

But you can also embed the widget into a program like the following image shows.
For example by using the [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter#readme) library,
which provides rounded buttons and frames compatible with the macOS darkmode:

![](documentation_images/customtkinter_example.gif)

# Installation

```
pip3 install tkintermapview
```
Update: ``pip3 install tkintermapview --upgrade``

https://pypi.org/project/tkintermapview/

# Documentation / Tutorial

### Importing

Import tkinter as normal and from tkintermapview import the TkinterMapView widget.
```python
import tkinter
from tkintermapview import TkinterMapView
```
---
### Create the widget

Create the standard tkinter window and place a TkinterMapView in the middle of the window.
The first argument must be the widgets master, then you specify the `width`, `height` and `corner_radius`
of the widget.
```python
# create tkinter window
root_tk = tkinter.Tk()
root_tk.geometry(f"{800}x{600}")
root_tk.title("map_view_example.py")

# create map widget
map_widget = TkinterMapView(root_tk, width=800, height=600, corner_radius=0)
map_widget.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
```
If you also call `root_tk.mainloop()` at the end, this is already a fully working example to test the map widget.

---
### Set coordinate position

The standard position on which the map is focused is Berlin, Germany,
but you can change the position and zoom with the following commands.
The position must be given in decimal coordinates and the zoom ranges from
0 to 19 where 19 is the highest zoom level.
```python
# set current widget position and zoom
map_widget.set_position(48.860381, 2.338594)  # Paris, France
map_widget.set_zoom(15)
```
---
### Set address position

But you can not only set the position by decimal coordinates, but also by
an address string like ` "colosseo, rome, italy" ` or ` "3 St Margaret St, London, United Kingdom" `.
The address is converted to a position by the OpenStreetMap geocode service
Nomatim.
```python
# set current widget position by address
map_widget.set_address("colosseo, rome, italy")
```
---
### Set position with marker

If you also want a red marker at the set position with a text of the current location,
then you can pass the `marker=True` argument to the `set_position` or `set_address`
funtions. You get back a PositionMarker object, so that you can modify or delete the marker
later:
```python
# set current widget position by address
marker_1 = map_widget.set_address("colosseo, rome, italy")

print(marker_1.position, marker_1.text)  # get position and text

marker_1.set_text("Colosseo in Rome")  # set new text
# marker_1.set_position(48.860381, 2.338594)  # change position
# marker_1.delete()
```
---
### Create position markers

You can also set a position marker without focusing the widget on it.
You can pass a ``text`` argument to the function and get back the marker
object, so that you can store the marker and modify or delete it later.
```python
# set a position marker
marker_2 = map_widget.set_marker(52.516268, 13.377695, text="Brandenburger Tor")
marker_3 = map_widget.set_marker(52.55, 13.4, text="52.55, 13.4")
# marker_3.set_position(...)
# marker_3.set_text(...)
# marker_3.delete()
```
---
### Create path from position list

You can also create a path which connects multiple markers or completely new positions.
You pass a list with position tuples to the function `set_path` and get back a path object.
The path object can be modified by adding a new position or remove a specific position.
````python
# set a path
path_1 = map_widget.set_path([marker_2.position, marker_3.position, (52.57, 13.4), (52.55, 13.35)])
# path_1.add_position(...)
# path_1.remove_position(...)
# path_1.delete()
````
---
### Use other tile servers

TkinterMapView uses OpenStreetMap tiles by default, but you can also change the
tile server to every url that includes ``{x} {y} {z}`` coordinates.
For example, you can use the standard Google Maps map style or Google Maps
satellite images:
````python
# example tile sever:
self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)  # google normal
self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)  # google satellite
self.map_widget.set_tile_server("http://c.tile.stamen.com/watercolor/{z}/{x}/{y}.png")  # painting style
self.map_widget.set_tile_server("http://a.tile.stamen.com/toner/{z}/{x}/{y}.png")  # black and white
self.map_widget.set_tile_server("https://tiles.wmflabs.org/hikebike/{z}/{x}/{y}.png")  # detailed hiking
self.map_widget.set_tile_server("https://tiles.wmflabs.org/osm-no-labels/{z}/{x}/{y}.png")  # no labels

# example overlay tile server
self.map_widget.set_overlay_tile_server("http://tiles.openseamap.org/seamark//{z}/{x}/{y}.png")  # sea-map overlay
self.map_widget.set_overlay_tile_server("http://a.tiles.openrailwaymap.org/standard/{z}/{x}/{y}.png")  # railway infrastructure
````
---
When you also call `root_tk.mainloop()` at the end, you get a fully working example program.