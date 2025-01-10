from typing import Protocol, Tuple, Callable, Union


class MapWidgetProtocol(Protocol):
    canvas: any
    width: int
    height: int
    lower_right_tile_pos: Tuple[float, float]
    upper_left_tile_pos: Tuple[float, float]
    move_velocity: Tuple[float, float]
    fading_possible: bool
    last_move_time: Union[float, None]
    zoom: float

    def convert_canvas_coords_to_decimal_coords(self, canvas_x: int, canvas_y: int) -> tuple: ...
    def check_map_border_crossing(self) -> None: ...
    def draw_move(self) -> None: ...
    def set_zoom(self, zoom: float, relative_pointer_x: float, relative_pointer_y: float) -> None: ...
    def after(self, ms: int, func: Callable) -> None: ...
    def bind(self, sequence: str, func: Callable) -> None: ...