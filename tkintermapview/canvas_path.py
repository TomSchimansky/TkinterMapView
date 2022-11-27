import tkinter
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .map_widget import TkinterMapView

from .utility_functions import decimal_to_osm, osm_to_decimal


class CanvasPath:
    def __init__(self,
                 map_widget: "TkinterMapView",
                 position_list: list,
                 color: str = "#3E69CB",
                 command=None,
                 name: str = None,
                 width: int = 9,
                 data: any = None):

        self.map_widget = map_widget
        self.position_list = position_list
        self.canvas_line_positions = []
        self.deleted = False

        self.path_color = color
        self.command = command
        self.canvas_line = None
        self.width = width
        self.name = name
        self.data = data

        self.last_upper_left_tile_pos = None
        self.last_position_list_length = len(self.position_list)

    def delete(self):
        if self in self.map_widget.canvas_path_list:
            self.map_widget.canvas_path_list.remove(self)

        self.map_widget.canvas.delete(self.canvas_line)
        self.canvas_line = None
        self.deleted = True

    def add_position(self, deg_x, deg_y, index=-1):
        if index == -1:
            self.position_list.append((deg_x, deg_y))
        else:
            self.position_list.insert(index, (deg_x, deg_y))
        # self.draw()

    def remove_position(self, deg_x, deg_y):
        self.position_list.remove((deg_x, deg_y))
        self.draw()

    def get_canvas_pos(self, position, widget_tile_width, widget_tile_height):
        tile_position = decimal_to_osm(*position, round(self.map_widget.zoom))

        canvas_pos_x = ((tile_position[0] - self.map_widget.upper_left_tile_pos[0]) / widget_tile_width) * self.map_widget.width
        canvas_pos_y = ((tile_position[1] - self.map_widget.upper_left_tile_pos[1]) / widget_tile_height) * self.map_widget.height

        return canvas_pos_x, canvas_pos_y

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

    def draw(self, move=False):
        new_line_length = self.last_position_list_length != len(self.position_list)
        self.last_position_list_length = len(self.position_list)

        widget_tile_width = self.map_widget.lower_right_tile_pos[0] - self.map_widget.upper_left_tile_pos[0]
        widget_tile_height = self.map_widget.lower_right_tile_pos[1] - self.map_widget.upper_left_tile_pos[1]

        if move is True and self.last_upper_left_tile_pos is not None and new_line_length is False:
            x_move = ((self.last_upper_left_tile_pos[0] - self.map_widget.upper_left_tile_pos[0]) / widget_tile_width) * self.map_widget.width
            y_move = ((self.last_upper_left_tile_pos[1] - self.map_widget.upper_left_tile_pos[1]) / widget_tile_height) * self.map_widget.height

            for i in range(0, len(self.position_list)* 2, 2):
                self.canvas_line_positions[i] += x_move
                self.canvas_line_positions[i + 1] += y_move
        else:
            self.canvas_line_positions = []
            for position in self.position_list:
                canvas_position = self.get_canvas_pos(position, widget_tile_width, widget_tile_height)
                self.canvas_line_positions.append(canvas_position[0])
                self.canvas_line_positions.append(canvas_position[1])

        if not self.deleted:
            if self.canvas_line is None:
                self.map_widget.canvas.delete(self.canvas_line)
                self.canvas_line = self.map_widget.canvas.create_line(self.canvas_line_positions,
                                                                      width=self.width, fill=self.path_color,
                                                                      capstyle=tkinter.ROUND, joinstyle=tkinter.ROUND,
                                                                      tag="path")

                if self.command is not None:
                    self.map_widget.canvas.tag_bind(self.canvas_line, "<Enter>", self.mouse_enter)
                    self.map_widget.canvas.tag_bind(self.canvas_line, "<Leave>", self.mouse_leave)
                    self.map_widget.canvas.tag_bind(self.canvas_line, "<Button-1>", self.click)
            else:
                self.map_widget.canvas.coords(self.canvas_line, self.canvas_line_positions)
        else:
            self.map_widget.canvas.delete(self.canvas_line)
            self.canvas_line = None

        self.map_widget.manage_z_order()
        self.last_upper_left_tile_pos = self.map_widget.upper_left_tile_pos

