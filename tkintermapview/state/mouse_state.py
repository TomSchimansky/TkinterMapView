from dataclasses import dataclass
from typing import Union, Tuple, Callable


@dataclass
class MouseState:
    last_mouse_down_position: Union[Tuple[int, int], None] = None
    last_mouse_down_time: Union[float, None] = None
    mouse_click_position: Union[Tuple[int, int], None] = None
    map_click_callback: Union[Callable, None] = None
