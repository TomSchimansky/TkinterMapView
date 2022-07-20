# noinspection PyCompatibility
import tkinter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .map_widget import TkinterMapView


class CanvasTile:
    def __init__(self, map_widget: "TkinterMapView", image, tile_name_position):
        self.map_widget = map_widget
        self.image = image
        self.tile_name_position = tile_name_position

        self.upper_left_tile_pos = None
        self.lower_right_tile_pos = None

        self.canvas_object = None
        self.widget_tile_width = 0
        self.widget_tile_height = 0

    def __del__(self):
        # if CanvasTile object gets garbage collected or deleted, delete image from canvas
        self.delete()

    def set_image_and_position(self, image, tile_name_position):
        self.image = image
        self.tile_name_position = tile_name_position
        self.draw(image_update=True)

    def set_image(self, image):
        self.image = image
        self.draw(image_update=True)

    def get_canvas_pos(self):
        self.widget_tile_width = self.map_widget.lower_right_tile_pos[0] - self.map_widget.upper_left_tile_pos[0]
        self.widget_tile_height = self.map_widget.lower_right_tile_pos[1] - self.map_widget.upper_left_tile_pos[1]

        canvas_pos_x = ((self.tile_name_position[0] - self.map_widget.upper_left_tile_pos[
            0]) / self.widget_tile_width) * self.map_widget.width
        canvas_pos_y = ((self.tile_name_position[1] - self.map_widget.upper_left_tile_pos[
            1]) / self.widget_tile_height) * self.map_widget.height

        return canvas_pos_x, canvas_pos_y

    def delete(self):
        self.map_widget.canvas.delete(self.canvas_object)

    def draw(self, image_update=False):

        # calculate canvas position fro OSM coordinates
        canvas_pos_x, canvas_pos_y = self.get_canvas_pos()

        if self.canvas_object is None:
            if not (self.image == self.map_widget.not_loaded_tile_image or self.image == self.image == self.map_widget.empty_tile_image):
                self.canvas_object = self.map_widget.canvas.create_image(canvas_pos_x,
                                                                         canvas_pos_y,
                                                                         image=self.image,
                                                                         anchor=tkinter.NW,
                                                                         tags="tile")
        else:
            self.map_widget.canvas.coords(self.canvas_object, canvas_pos_x, canvas_pos_y)

            if image_update:
                if not (
                        self.image == self.map_widget.not_loaded_tile_image or self.image == self.image == self.map_widget.empty_tile_image):
                    self.map_widget.canvas.itemconfig(self.canvas_object, image=self.image)
                else:
                    self.map_widget.canvas.delete(self.canvas_object)
                    self.canvas_object = None

        self.map_widget.manage_z_order()
