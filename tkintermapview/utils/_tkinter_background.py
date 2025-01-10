from tkinter import Misc, Frame, Tk, Toplevel, LabelFrame, ttk
from typing import Protocol, Union, Literal

DEFAULT_BACKGROUND = "#000000"


class LegacyProtocol(Protocol):
    fg_color: Union[str, list[str]]
    _appearance_mode: int


class CustomTkinterProtocol(Protocol):
    _apply_appearance_mode: callable


def _detect_custom_tkinter(value: Misc) -> Literal["customtkinter", "customtkinter_legacy"]:
    if hasattr(value, "_apply_appearance_mode"):
        return "customtkinter"
    elif hasattr(value, "fg_color"):
        return "customtkinter_legacy"


def _detect_tkinter_type(value: Misc) -> Literal["tkinter", "ttk", "customtkinter", "customtkinter_legacy"]:
    if (hasattr(value, "canvas") and hasattr(value, "fg_color")) or (
            hasattr(value, "_canvas") and hasattr(value, "_fg_color")):
        return _detect_custom_tkinter(value)
    elif isinstance(value, (Frame, Tk, Toplevel, LabelFrame)):
        return "tkinter"
    elif isinstance(value, (ttk.Frame, ttk.LabelFrame, ttk.Notebook)):
        return "ttk"


def _get_background_ttk(value: Misc) -> str:
    try:
        return ttk.Style().lookup(value.winfo_class(), 'background')
    except Exception:
        return DEFAULT_BACKGROUND


def _get_background_legacy(value: LegacyProtocol) -> str:
    if type(value.fg_color) == tuple or type(value.fg_color) == list:
        return value.fg_color[value._appearance_mode]
    else:
        return value.fg_color


def get_background_color(master: Union[Misc, LegacyProtocol, CustomTkinterProtocol]) -> str:
    match _detect_custom_tkinter(master):
        case "tkinter":
            return master.cget("bg")
        case "ttk":
            return _get_background_ttk(master)
        case "customtkinter":
            master._apply_appearance_mode(master.cget("fg_color"))
        case "customtkinter_legacy":
            return _get_background_legacy(master)
        case _:
            return _get_background_ttk(master)
