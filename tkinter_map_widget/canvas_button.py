import tkinter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .map_widget import TkinterMapWidget


class CanvasButton:
    def __init__(self, map_widget: "TkinterMapWidget", canvas_position, width=16, height=16, text="", command=None):
        self.map_widget = map_widget
        self.canvas_position = canvas_position
        self.width = width
        self.height = height
        self.text = text
        self.command = command

        self.canvas_rect = None
        self.canvas_text = None

        self.draw()

    def click(self, event):
        if self.command is not None:
            self.command()

    def hover_on(self, event):
        if self.canvas_rect is not None:
            self.map_widget.canvas.itemconfig(self.canvas_rect, fill="gray60", outline="gray40")

    def hover_off(self, event):
        if self.canvas_rect is not None:
            self.map_widget.canvas.itemconfig(self.canvas_rect, fill="gray20", outline="gray20")

    def draw(self):
        self.canvas_rect = self.map_widget.canvas.create_polygon(self.canvas_position[0], self.canvas_position[1],
                                                                 self.canvas_position[0] + self.width, self.canvas_position[1],
                                                                 self.canvas_position[0] + self.width,
                                                                 self.canvas_position[1] + self.height,
                                                                 self.canvas_position[0], self.canvas_position[1] + self.height,
                                                                 width=16,
                                                                 fill="gray20", outline="gray20",
                                                                 tag="button")

        self.canvas_text = self.map_widget.canvas.create_text(self.canvas_position[0] + self.width / 2,
                                                              self.canvas_position[1] + self.height / 2,
                                                              anchor=tkinter.CENTER,
                                                              text=self.text,
                                                              fill="white",
                                                              font="Tahoma 16",
                                                              tag="button")

        self.map_widget.canvas.tag_bind(self.canvas_rect, "<Button-1>", self.click)
        self.map_widget.canvas.tag_bind(self.canvas_text, "<Button-1>", self.click)
        self.map_widget.canvas.tag_bind(self.canvas_rect, "<Enter>", self.hover_on)
        self.map_widget.canvas.tag_bind(self.canvas_text, "<Enter>", self.hover_on)
        self.map_widget.canvas.tag_bind(self.canvas_rect, "<Leave>", self.hover_off)
        self.map_widget.canvas.tag_bind(self.canvas_text, "<Leave>", self.hover_off)
