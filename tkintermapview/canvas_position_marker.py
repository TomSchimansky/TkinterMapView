import tkinter
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .map_widget import TkinterMapView

from .coordinate_convert_functions import deg2num, num2deg


class CanvasPositionMarker:
    def __init__(self, map_widget: "TkinterMapView", position, text=None, text_color="#652A22"):
        self.map_widget = map_widget
        self.position = position
        self.text_color = text_color
        self.connection_list = []
        self.deleted = False

        self.polygon = None
        self.big_circle = None
        self.canvas_text = None
        self.text = text

    def __del__(self):
        self.map_widget.canvas.delete(self.polygon, self.big_circle, self.canvas_text)
        self.polygon, self.big_circle, self.canvas_text = None, None, None
        self.deleted = True
        self.map_widget.canvas.update()

    def delete(self):
        self.__del__()

    def set_position(self, deg_x, deg_y):
        self.position = (deg_x, deg_y)
        self.draw()

    def set_text(self, text):
        self.text = text
        self.draw()

    def get_canvas_pos(self, position):
        tile_position = deg2num(*position, round(self.map_widget.zoom))

        widget_tile_width = self.map_widget.lower_right_tile_pos[0] - self.map_widget.upper_left_tile_pos[0]
        widget_tile_height = self.map_widget.lower_right_tile_pos[1] - self.map_widget.upper_left_tile_pos[1]

        canvas_pos_x = ((tile_position[0] - self.map_widget.upper_left_tile_pos[0]) / widget_tile_width) * self.map_widget.width
        canvas_pos_y = ((tile_position[1] - self.map_widget.upper_left_tile_pos[1]) / widget_tile_height) * self.map_widget.height

        return canvas_pos_x, canvas_pos_y

    def draw(self, event=None):
        canvas_pos_x, canvas_pos_y = self.get_canvas_pos(self.position)

        if not self.deleted:
            if 0 - 50 < canvas_pos_x < self.map_widget.width + 50 and 0 < canvas_pos_y < self.map_widget.height + 70:
                if self.polygon is None:
                    self.polygon = self.map_widget.canvas.create_polygon(canvas_pos_x - 14, canvas_pos_y - 23,
                                                                         canvas_pos_x, canvas_pos_y,
                                                                         canvas_pos_x + 14, canvas_pos_y - 23,
                                                                         fill="#C5542D", width=2, outline="#C5542D", tag="marker")
                else:
                    self.map_widget.canvas.coords(self.polygon,
                                                  canvas_pos_x - 14, canvas_pos_y - 23,
                                                  canvas_pos_x, canvas_pos_y,
                                                  canvas_pos_x + 14, canvas_pos_y - 23)
                if self.big_circle is None:
                    self.big_circle = self.map_widget.canvas.create_oval(canvas_pos_x - 14, canvas_pos_y - 45,
                                                                         canvas_pos_x + 14, canvas_pos_y - 17,
                                                                         fill="#9B261E", width=6, outline="#C5542D", tag="marker")
                else:
                    self.map_widget.canvas.coords(self.big_circle,
                                                  canvas_pos_x - 14, canvas_pos_y - 45,
                                                  canvas_pos_x + 14, canvas_pos_y - 17)

                if self.text is not None:
                    if self.canvas_text is None:
                        if sys.platform == "darwin":
                            font = "Tahoma 13 bold"
                        else:
                            font = "Tahoma 11 bold"

                        self.canvas_text = self.map_widget.canvas.create_text(canvas_pos_x, canvas_pos_y - 62,
                                                                              anchor=tkinter.CENTER,
                                                                              text=self.text,
                                                                              fill="#590505",
                                                                              font=font,
                                                                              tag=("marker", "marker_text"))
                    else:
                        self.map_widget.canvas.coords(self.canvas_text, canvas_pos_x, canvas_pos_y - 62)
                        self.map_widget.canvas.itemconfig(self.canvas_text, text=self.text)
                else:
                    if self.canvas_text is not None:
                        self.map_widget.canvas.delete(self.canvas_text)

            else:
                self.map_widget.canvas.delete(self.polygon, self.big_circle, self.canvas_text)
                self.polygon, self.big_circle, self.canvas_text = None, None, None

            self.map_widget.manage_z_order()
