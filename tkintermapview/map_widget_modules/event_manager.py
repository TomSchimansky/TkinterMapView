import math
import sys
import time

from .protocols import MapWidgetProtocol
from ..state.mouse_state import MouseState
from ..utils.enums import MouseButton


class EventManager:
    def __init__(self, map_widget: MapWidgetProtocol):
        self.map_widget = map_widget
        self._mouse_state = MouseState()
        self._bind_mouse_events()

    def _bind_mouse_events(self):
        m = self.map_widget
        m.canvas.bind("<B1-Motion>", self.mouse_move)
        m.canvas.bind("<Button-1>", self.mouse_click)
        m.canvas.bind("<ButtonRelease-1>", self.mouse_release)
        m.canvas.bind("<MouseWheel>", self.mouse_zoom)
        m.canvas.bind("<Button-4>", self.mouse_zoom)
        m.canvas.bind("<Button-5>", self.mouse_zoom)
        m.bind('<Configure>', self.update_dimensions)

    @property
    def mouse_state(self) -> MouseState:
        return self._mouse_state

    def mouse_move(self, event):
        m = self.map_widget
        mouse_move_x = self._mouse_state.last_mouse_down_position[0] - event.x
        mouse_move_y = self._mouse_state.last_mouse_down_position[1] - event.y

        delta_t = time.time() - self._mouse_state.last_mouse_down_time
        m.move_velocity = (0, 0) if delta_t == 0 else (mouse_move_x / delta_t, mouse_move_y / delta_t)

        self._mouse_state.last_mouse_down_position = (event.x, event.y)
        self._mouse_state.last_mouse_down_time = time.time()

        tile_x_range = m.lower_right_tile_pos[0] - m.upper_left_tile_pos[0]
        tile_y_range = m.lower_right_tile_pos[1] - m.upper_left_tile_pos[1]

        tile_move_x = (mouse_move_x / m.width) * tile_x_range
        tile_move_y = (mouse_move_y / m.height) * tile_y_range

        m.lower_right_tile_pos = (m.lower_right_tile_pos[0] + tile_move_x, m.lower_right_tile_pos[1] + tile_move_y)
        m.upper_left_tile_pos = (m.upper_left_tile_pos[0] + tile_move_x, m.upper_left_tile_pos[1] + tile_move_y)

        m.check_map_border_crossing()
        m.draw_move()

    def mouse_click(self, event):
        self.map_widget.fading_possible = False
        self._mouse_state.mouse_click_position = (event.x, event.y)

        # save mouse position where mouse is pressed down for moving
        self._mouse_state.last_mouse_down_position = (event.x, event.y)
        self._mouse_state.last_mouse_down_time = time.time()

    def mouse_release(self, event):
        m = self.map_widget
        m.fading_possible = True
        m.last_move_time = time.time()

        # check if mouse moved after mouse click event
        if self._mouse_state.mouse_click_position == (event.x, event.y):
            # mouse didn't move
            if self._mouse_state.map_click_callback is not None:
                # get decimal coords of current mouse position
                coordinate_mouse_pos = m.convert_canvas_coords_to_decimal_coords(event.x, event.y)
                self._mouse_state.map_click_callback(coordinate_mouse_pos)
        else:
            # mouse was moved, start fading animation
            m.after(1, m.fading_move)

    def mouse_zoom(self, event):
        m = self.map_widget
        rel_x, rel_y = event.x / m.width, event.y / m.height
        scale_factor = 0.1 if sys.platform == 'darwin' else 0.01

        if event.delta:  # For platforms using `event.delta`
            new_zoom = m.zoom + event.delta * scale_factor
        elif event.num == MouseButton.SCROLL_UP.value:
            new_zoom = m.zoom + 1
        elif event.num == MouseButton.SCROLL_DOWN.value:
            new_zoom = m.zoom - 1
        else:
            return  # Ignore unsupported events

        m.set_zoom(new_zoom, relative_pointer_x=rel_x, relative_pointer_y=rel_y)

    def update_dimensions(self, event):
        m = self.map_widget
        # only redraw if dimensions changed (for performance)
        if m.width != event.width or m.height != event.height:
            m.width = event.width
            m.height = event.height
            m.min_zoom = math.ceil(math.log2(math.ceil(m.width / m.tile_size)))

            m.set_zoom(m.zoom)  # call zoom to set the position vertices right
            m.draw_move()  # call move to draw new tiles or delete tiles
            m.draw_rounded_corners()
