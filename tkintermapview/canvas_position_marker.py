import tkinter
import sys
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from .map_widget import TkinterMapView

from .utility_functions import decimal_to_osm, osm_to_decimal


class CanvasPositionMarker:
    def __init__(self,
                 map_widget: "TkinterMapView",
                 position: tuple,
                 text: str = None,
                 text_color: str = "#652A22",
                 font=None,
                 marker_color_circle: str = "#9B261E",
                 marker_color_outside: str = "#C5542D",
                 command: Callable = None,
                 image=None,
                 image_zoom_visibility: tuple = (0, float("inf")),
                 data: any = None,
                 range: float = None):

        self.map_widget = map_widget
        self.position = position
        self.text_color = text_color
        self.marker_color_circle = marker_color_circle
        self.marker_color_outside = marker_color_outside
        self.text = text
        self.image = image
        self.image_hidden = False
        self.image_zoom_visibility = image_zoom_visibility
        self.deleted = False
        self.command = command
        self.data = data
        self.range = range

        self.polygon = None
        self.big_circle = None
        self.canvas_text = None
        self.canvas_image = None
        self.canvas_icon = None
        self.canvas_range = None

        if font is None:
            if sys.platform == "darwin":
                self.font = "Tahoma 13 bold"
            else:
                self.font = "Tahoma 11 bold"
        else:
            self.font = font

    def delete(self):
        if self in self.map_widget.canvas_marker_list:
            self.map_widget.canvas_marker_list.remove(self)

        self.map_widget.canvas.delete(self.polygon, self.big_circle, self.canvas_text)
        self.polygon, self.big_circle, self.canvas_text = None, None, None
        self.deleted = True
        self.map_widget.canvas.update()

    def set_position(self, deg_x, deg_y):
        self.position = (deg_x, deg_y)
        self.draw()

    def set_text(self, text):
        self.text = text
        self.draw()

    def hide_image(self, image_hidden):
        self.image_hidden = image_hidden
        self.draw()

    def mouse_enter(self, event=None):
        if sys.platform == "darwin":
            self.map_widget.canvas.config(cursor="pointinghand")
        elif sys.platform.startswith("win"):
            self.map_widget.canvas.config(cursor="hand2")
        else:
            self.map_widget.canvas.config(cursor="hand2")  # not tested what it looks like on Linux!

    def mouse_leave(self, event=None):
        self.map_widget.canvas.config(cursor="arrow")

    def click(self, event=None):
        if self.command is not None:
            self.command(self)

    def get_canvas_range(self, range:float):
        tile_position = decimal_to_osm(*self.position, round(self.map_widget.zoom))
        tile_range = decimal_to_osm(self.position[0]+range, self.position[1], round(self.map_widget.zoom))
        return abs(tile_position[1]-tile_range[1])

    def get_canvas_pos(self, position):
        tile_position = decimal_to_osm(*position, round(self.map_widget.zoom))

        widget_tile_width = self.map_widget.lower_right_tile_pos[0] - self.map_widget.upper_left_tile_pos[0]
        widget_tile_height = self.map_widget.lower_right_tile_pos[1] - self.map_widget.upper_left_tile_pos[1]

        canvas_pos_x = ((tile_position[0] - self.map_widget.upper_left_tile_pos[0]) / widget_tile_width) * self.map_widget.width
        canvas_pos_y = ((tile_position[1] - self.map_widget.upper_left_tile_pos[1]) / widget_tile_height) * self.map_widget.height

        return canvas_pos_x, canvas_pos_y

    def draw(self, event=None):
        canvas_pos_x, canvas_pos_y = self.get_canvas_pos(self.position)
        x_offset = 50
        y_offset = 70
        if self.range is not None:      
            image_range = self.get_canvas_range(self.range)
            x_offset = max(2*image_range, x_offset)
            y_offset = max(2*image_range, y_offset)

        if not self.deleted:
            if 0 - x_offset < canvas_pos_x < self.map_widget.width + x_offset and 0-y_offset < canvas_pos_y < self.map_widget.height + y_offset:
                if self.polygon is None:
                    self.polygon = self.map_widget.canvas.create_polygon(canvas_pos_x - 14, canvas_pos_y - 23,
                                                                         canvas_pos_x, canvas_pos_y,
                                                                         canvas_pos_x + 14, canvas_pos_y - 23,
                                                                         fill=self.marker_color_outside, width=2,
                                                                         outline=self.marker_color_outside, tag="marker")
                    if self.command is not None:
                        self.map_widget.canvas.tag_bind(self.polygon, "<Enter>", self.mouse_enter)
                        self.map_widget.canvas.tag_bind(self.polygon, "<Leave>", self.mouse_leave)
                        self.map_widget.canvas.tag_bind(self.polygon, "<Button-1>", self.click)
                else:
                    self.map_widget.canvas.coords(self.polygon,
                                                  canvas_pos_x - 14, canvas_pos_y - 23,
                                                  canvas_pos_x, canvas_pos_y,
                                                  canvas_pos_x + 14, canvas_pos_y - 23)
                if self.big_circle is None:
                    self.big_circle = self.map_widget.canvas.create_oval(canvas_pos_x - 14, canvas_pos_y - 45,
                                                                         canvas_pos_x + 14, canvas_pos_y - 17,
                                                                         fill=self.marker_color_circle, width=6,
                                                                         outline=self.marker_color_outside, tag="marker")
                    if self.command is not None:
                        self.map_widget.canvas.tag_bind(self.big_circle, "<Enter>", self.mouse_enter)
                        self.map_widget.canvas.tag_bind(self.big_circle, "<Leave>", self.mouse_leave)
                        self.map_widget.canvas.tag_bind(self.big_circle, "<Button-1>", self.click)
                else:
                    self.map_widget.canvas.coords(self.big_circle,
                                                  canvas_pos_x - 14, canvas_pos_y - 45,
                                                  canvas_pos_x + 14, canvas_pos_y - 17)

                if self.text is not None:
                    if self.canvas_text is None:
                        self.canvas_text = self.map_widget.canvas.create_text(canvas_pos_x, canvas_pos_y - 56,
                                                                              anchor=tkinter.S,
                                                                              text=self.text,
                                                                              fill=self.text_color,
                                                                              font=self.font,
                                                                              tag=("marker", "marker_text"))
                        if self.command is not None:
                            self.map_widget.canvas.tag_bind(self.canvas_text, "<Enter>", self.mouse_enter)
                            self.map_widget.canvas.tag_bind(self.canvas_text, "<Leave>", self.mouse_leave)
                            self.map_widget.canvas.tag_bind(self.canvas_text, "<Button-1>", self.click)
                    else:
                        self.map_widget.canvas.coords(self.canvas_text, canvas_pos_x, canvas_pos_y - 56)
                        self.map_widget.canvas.itemconfig(self.canvas_text, text=self.text)
                else:
                    if self.canvas_text is not None:
                        self.map_widget.canvas.delete(self.canvas_text)

                if self.image is not None and self.image_zoom_visibility[0] <= self.map_widget.zoom <= self.image_zoom_visibility[1]\
                        and not self.image_hidden:

                    if self.canvas_image is None:
                        self.canvas_image = self.map_widget.canvas.create_image(canvas_pos_x, canvas_pos_y - 85,
                                                                                anchor=tkinter.S,
                                                                                image=self.image,
                                                                                tag=("marker", "marker_image"))
                    else:
                        self.map_widget.canvas.coords(self.canvas_image, canvas_pos_x, canvas_pos_y - 85)
                else:
                    if self.canvas_image is not None:
                        self.map_widget.canvas.delete(self.canvas_image)
                        self.canvas_image = None
                if self.range is not None:
                    if self.canvas_range is None:
                        self.canvas_range = self.map_widget.canvas.create_oval(canvas_pos_x - image_range, canvas_pos_y - image_range,
                                                                            canvas_pos_x + image_range, canvas_pos_y + image_range,
                                                                            width=3,
                                                                            outline=self.marker_color_outside,
                                                                            tag=("marker"))
                        if self.command is not None:
                            self.map_widget.canvas.tag_bind(self.canvas_range, "<Enter>", self.mouse_enter)
                            self.map_widget.canvas.tag_bind(self.canvas_range, "<Leave>", self.mouse_leave)
                            self.map_widget.canvas.tag_bind(self.canvas_range, "<Button-1>", self.click)       
                    else:
                        self.map_widget.canvas.coords(self.canvas_range, canvas_pos_x - image_range, canvas_pos_y - image_range,
                                                                        canvas_pos_x + image_range, canvas_pos_y + image_range)
                else:
                    if self.canvas_range is not None:
                        self.map_widget.canvas.delete(self.canvas_range)
                        self.canvas_range = None
            else:
                self.map_widget.canvas.delete(self.polygon, self.big_circle, self.canvas_text, self.canvas_image, self.canvas_range)
                self.polygon, self.big_circle, self.canvas_text, self.canvas_image, self.canvas_range = None, None, None, None, None

            self.map_widget.manage_z_order()
