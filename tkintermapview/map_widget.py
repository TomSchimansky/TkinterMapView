import requests
import math
import threading
import tkinter
import tkinter.ttk as ttk
import tkinter.messagebox
import time
import PIL
import sys
import io
import sqlite3
import pyperclip
import geocoder
from PIL import Image, ImageTk
from typing import Callable, List, Dict, Union, Tuple
from functools import partial

from .canvas_position_marker import CanvasPositionMarker
from .canvas_tile import CanvasTile
from .utility_functions import decimal_to_osm, osm_to_decimal
from .canvas_button import CanvasButton
from .canvas_path import CanvasPath
from .canvas_polygon import CanvasPolygon


class TkinterMapView(tkinter.Frame):
    def __init__(self, *args,
                 width: int = 300,
                 height: int = 200,
                 corner_radius: int = 0,
                 bg_color: str = None,
                 database_path: str = None,
                 use_database_only: bool = False,
                 max_zoom: int = 19,
                 **kwargs):
        super().__init__(*args, **kwargs)

        self.width = width
        self.height = height
        self.corner_radius = corner_radius if corner_radius <= 30 else 30  # corner_radius can't be greater than 30
        self.configure(width=self.width, height=self.height)

        # detect color of master widget for rounded corners
        if bg_color is None:
            # map widget is placed in a CTkFrame from customtkinter library
            if (hasattr(self.master, "canvas") and hasattr(self.master, "fg_color")) or (hasattr(self.master, "_canvas") and hasattr(self.master, "_fg_color")):
                # customtkinter version >=5.0.0
                if hasattr(self.master, "_apply_appearance_mode"):
                    self.bg_color: str = self.master._apply_appearance_mode(self.master.cget("fg_color"))
                # customtkinter version <=4.6.3
                elif hasattr(self.master, "fg_color"):
                    if type(self.master.fg_color) == tuple or type(self.master.fg_color) == list:
                        self.bg_color: str = self.master.fg_color[self.master._appearance_mode]
                    else:
                        self.bg_color: str = self.master.fg_color

            # map widget is placed on a tkinter.Frame or tkinter.Tk
            elif isinstance(self.master, (tkinter.Frame, tkinter.Tk, tkinter.Toplevel, tkinter.LabelFrame)):
                self.bg_color: str = self.master.cget("bg")

            # map widget is placed in a ttk widget
            elif isinstance(self.master, (ttk.Frame, ttk.LabelFrame, ttk.Notebook)):
                try:
                    ttk_style = ttk.Style()
                    self.bg_color = ttk_style.lookup(self.master.winfo_class(), 'background')
                except Exception:
                    self.bg_color: str = "#000000"

            # map widget is placed on an unknown widget
            else:
                self.bg_color: str = "#000000"
        else:
            self.bg_color = bg_color

        self.grid_rowconfigure(0, weight=1)  # configure 1x1 grid system
        self.grid_columnconfigure(0, weight=1)

        self.canvas = tkinter.Canvas(master=self,
                                     highlightthicknes=0,
                                     bg="#F1EFEA",
                                     width=self.width,
                                     height=self.height)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # zoom buttons
        self.button_zoom_in = CanvasButton(self, (20, 20), text="+", command=self.button_zoom_in)
        self.button_zoom_out = CanvasButton(self, (20, 60), text="-", command=self.button_zoom_out)

        # bind events for mouse button pressed, mouse movement, and scrolling
        self.canvas.bind("<B1-Motion>", self.mouse_move)
        self.canvas.bind("<Button-1>", self.mouse_click)
        self.canvas.bind("<ButtonRelease-1>", self.mouse_release)
        self.canvas.bind("<MouseWheel>", self.mouse_zoom)
        self.canvas.bind("<Button-4>", self.mouse_zoom)
        self.canvas.bind("<Button-5>", self.mouse_zoom)
        self.bind('<Configure>', self.update_dimensions)
        self.last_mouse_down_position: Union[tuple, None] = None
        self.last_mouse_down_time: Union[float, None] = None
        self.mouse_click_position: Union[tuple, None] = None
        self.map_click_callback: Union[Callable, None] = None  # callback function for left click on map

        # movement fading
        self.fading_possible: bool = True
        self.move_velocity: Tuple[float, float] = (0, 0)
        self.last_move_time: Union[float, None] = None

        # describes the tile layout
        self.zoom: float = 0
        self.upper_left_tile_pos: Tuple[float, float] = (0, 0)  # in OSM coords
        self.lower_right_tile_pos: Tuple[float, float] = (0, 0)
        self.tile_size: int = 256  # in pixel
        self.last_zoom: float = self.zoom

        # canvas objects, image cache and standard empty images
        self.canvas_tile_array: List[List[CanvasTile]] = []
        self.canvas_marker_list: List[CanvasPositionMarker] = []
        self.canvas_path_list: List[CanvasPath] = []
        self.canvas_polygon_list: List[CanvasPolygon] = []

        self.tile_image_cache: Dict[str, PIL.ImageTk.PhotoImage] = {}
        self.empty_tile_image = ImageTk.PhotoImage(Image.new("RGB", (self.tile_size, self.tile_size), (190, 190, 190)))  # used for zooming and moving
        self.not_loaded_tile_image = ImageTk.PhotoImage(Image.new("RGB", (self.tile_size, self.tile_size), (250, 250, 250)))  # only used when image not found on tile server

        # tile server and database
        self.tile_server = "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"
        self.database_path = database_path
        self.use_database_only = use_database_only
        self.overlay_tile_server: Union[str, None] = None
        self.max_zoom = max_zoom  # should be set according to tile server max zoom
        self.min_zoom: int = math.ceil(math.log2(math.ceil(self.width / self.tile_size)))  # min zoom at which map completely fills widget

        # pre caching for smoother movements (load tile images into cache at a certain radius around the pre_cache_position)
        self.pre_cache_position: Union[Tuple[float, float], None] = None
        self.pre_cache_thread = threading.Thread(daemon=True, target=self.pre_cache)
        self.pre_cache_thread.start()

        # image loading in background threads
        self.image_load_queue_tasks: List[tuple] = []  # task: ((zoom, x, y), canvas_tile_object)
        self.image_load_queue_results: List[tuple] = []  # result: ((zoom, x, y), canvas_tile_object, photo_image)
        self.after(10, self.update_canvas_tile_images)
        self.image_load_thread_pool: List[threading.Thread] = []

        # add background threads which load tile images from self.image_load_queue_tasks
        for i in range(25):
            image_load_thread = threading.Thread(daemon=True, target=self.load_images_background)
            image_load_thread.start()
            self.image_load_thread_pool.append(image_load_thread)

        # set initial position
        self.set_zoom(17)
        self.set_position(52.516268, 13.377695)  # Brandenburger Tor, Berlin

        # right click menu
        self.right_click_menu_commands: List[dict] = []  # list of dictionaries with "label": str, "command": Callable, "pass_coords": bool
        if sys.platform == "darwin":
            self.canvas.bind("<Button-2>", self.mouse_right_click)
        else:
            self.canvas.bind("<Button-3>", self.mouse_right_click)

        self.draw_rounded_corners()

    def draw_rounded_corners(self):
        self.canvas.delete("corner")

        if sys.platform.startswith("win"):
            pos_corr = -1
        else:
            pos_corr = 0

        if self.corner_radius > 0:
            radius = self.corner_radius
            self.canvas.create_arc(self.width - 2 * radius + 5 + pos_corr, self.height - 2 * radius + 5 + pos_corr,
                                   self.width + 5 + pos_corr, self.height + 5 + pos_corr,
                                   style=tkinter.ARC, tag="corner", width=10, outline=self.bg_color, start=-90)
            self.canvas.create_arc(2 * radius - 5, self.height - 2 * radius + 5 + pos_corr, -5, self.height + 5 + pos_corr,
                                   style=tkinter.ARC, tag="corner", width=10, outline=self.bg_color, start=180)
            self.canvas.create_arc(-5, -5, 2 * radius - 5, 2 * radius - 5,
                                   style=tkinter.ARC, tag="corner", width=10, outline=self.bg_color, start=-270)
            self.canvas.create_arc(self.width - 2 * radius + 5 + pos_corr, -5, self.width + 5 + pos_corr, 2 * radius - 5,
                                   style=tkinter.ARC, tag="corner", width=10, outline=self.bg_color, start=0)

    def update_dimensions(self, event):
        # only redraw if dimensions changed (for performance)
        if self.width != event.width or self.height != event.height:
            self.width = event.width
            self.height = event.height
            self.min_zoom = math.ceil(math.log2(math.ceil(self.width / self.tile_size)))

            self.set_zoom(self.zoom)  # call zoom to set the position vertices right
            self.draw_move()  # call move to draw new tiles or delete tiles
            self.draw_rounded_corners()

    def add_right_click_menu_command(self, label: str, command: Callable, pass_coords: bool = False) -> None:
        self.right_click_menu_commands.append({"label": label, "command": command, "pass_coords": pass_coords})

    def add_left_click_map_command(self, callback_function):
        self.map_click_callback = callback_function

    def convert_canvas_coords_to_decimal_coords(self, canvas_x: int, canvas_y: int) -> tuple:
        relative_mouse_x = canvas_x / self.canvas.winfo_width()
        relative_mouse_y = canvas_y / self.canvas.winfo_height()

        tile_mouse_x = self.upper_left_tile_pos[0] + (self.lower_right_tile_pos[0] - self.upper_left_tile_pos[0]) * relative_mouse_x
        tile_mouse_y = self.upper_left_tile_pos[1] + (self.lower_right_tile_pos[1] - self.upper_left_tile_pos[1]) * relative_mouse_y

        coordinate_mouse_pos = osm_to_decimal(tile_mouse_x, tile_mouse_y, round(self.zoom))
        return coordinate_mouse_pos

    def mouse_right_click(self, event):
        coordinate_mouse_pos = self.convert_canvas_coords_to_decimal_coords(event.x, event.y)

        def click_coordinates_event():
            try:
                pyperclip.copy(f"{coordinate_mouse_pos[0]:.7f} {coordinate_mouse_pos[1]:.7f}")
                tkinter.messagebox.showinfo(title="", message="Coordinates copied to clipboard!")

            except Exception as err:
                if sys.platform.startswith("linux"):
                    tkinter.messagebox.showinfo(title="", message="Error copying to clipboard.\n" + str(err) + "\n\nTry to install xclip:\n'sudo apt-get install xclip'")
                else:
                    tkinter.messagebox.showinfo(title="", message="Error copying to clipboard.\n" + str(err))

        m = tkinter.Menu(self, tearoff=0)
        m.add_command(label=f"{coordinate_mouse_pos[0]:.7f} {coordinate_mouse_pos[1]:.7f}",
                      command=click_coordinates_event)

        if len(self.right_click_menu_commands) > 0:
            m.add_separator()

        for command in self.right_click_menu_commands:
            if command["pass_coords"]:
                m.add_command(label=command["label"], command=partial(command["command"], coordinate_mouse_pos))
            else:
                m.add_command(label=command["label"], command=command["command"])

        m.tk_popup(event.x_root, event.y_root)  # display menu

    def set_overlay_tile_server(self, overlay_server: str):
        self.overlay_tile_server = overlay_server

    def set_tile_server(self, tile_server: str, tile_size: int = 256, max_zoom: int = 19):
        self.image_load_queue_tasks = []
        self.max_zoom = max_zoom
        self.tile_size = tile_size
        self.min_zoom = math.ceil(math.log2(math.ceil(self.width / self.tile_size)))
        self.tile_server = tile_server
        self.tile_image_cache: Dict[str, PIL.ImageTk.PhotoImage] = {}
        self.canvas.delete("tile")
        self.image_load_queue_results = []
        self.draw_initial_array()

    def get_position(self) -> tuple:
        """ returns current middle position of map widget in decimal coordinates """

        return osm_to_decimal((self.lower_right_tile_pos[0] + self.upper_left_tile_pos[0]) / 2,
                              (self.lower_right_tile_pos[1] + self.upper_left_tile_pos[1]) / 2,
                              round(self.zoom))

    def set_position(self, deg_x, deg_y, text=None, marker=False, **kwargs) -> CanvasPositionMarker:
        """ set new middle position of map in decimal coordinates """

        # convert given decimal coordinates to OSM coordinates and set corner positions accordingly
        current_tile_position = decimal_to_osm(deg_x, deg_y, self.zoom)
        self.upper_left_tile_pos = (current_tile_position[0] - ((self.width / 2) / self.tile_size),
                                    current_tile_position[1] - ((self.height / 2) / self.tile_size))

        self.lower_right_tile_pos = (current_tile_position[0] + ((self.width / 2) / self.tile_size),
                                     current_tile_position[1] + ((self.height / 2) / self.tile_size))

        if marker is True:
            marker_object = self.set_marker(deg_x, deg_y, text, **kwargs)
        else:
            marker_object = None

        self.check_map_border_crossing()
        self.draw_initial_array()

        return marker_object

    def set_address(self, address_string: str, marker: bool = False, text: str = None, **kwargs) -> CanvasPositionMarker:
        """ Function uses geocode service of OpenStreetMap (Nominatim).
            https://geocoder.readthedocs.io/providers/OpenStreetMap.html """

        result = geocoder.osm(address_string)

        if result.ok:

            # determine zoom level for result by bounding box
            if hasattr(result, "bbox"):
                zoom_not_possible = True

                for zoom in range(self.min_zoom, self.max_zoom + 1):
                    lower_left_corner = decimal_to_osm(*result.bbox['southwest'], zoom)
                    upper_right_corner = decimal_to_osm(*result.bbox['northeast'], zoom)
                    tile_width = upper_right_corner[0] - lower_left_corner[0]

                    if tile_width > math.floor(self.width / self.tile_size):
                        zoom_not_possible = False
                        self.set_zoom(zoom)
                        break

                if zoom_not_possible:
                    self.set_zoom(self.max_zoom)
            else:
                self.set_zoom(10)

            if text is None:
                try:
                    text = result.geojson['features'][0]['properties']['address']
                except:
                    text = address_string

            return self.set_position(*result.latlng, marker=marker, text=text, **kwargs)
        else:
            return False

    def set_marker(self, deg_x: float, deg_y: float, text: str = None, **kwargs) -> CanvasPositionMarker:
        marker = CanvasPositionMarker(self, (deg_x, deg_y), text=text, **kwargs)
        marker.draw()
        self.canvas_marker_list.append(marker)
        return marker

    def set_path(self, position_list: list, **kwargs) -> CanvasPath:
        path = CanvasPath(self, position_list, **kwargs)
        path.draw()
        self.canvas_path_list.append(path)
        return path

    def set_polygon(self, position_list: list, **kwargs) -> CanvasPolygon:
        polygon = CanvasPolygon(self, position_list, **kwargs)
        polygon.draw()
        self.canvas_polygon_list.append(polygon)
        return polygon

    def delete(self, map_object: any):
        if isinstance(map_object, (CanvasPath, CanvasPositionMarker, CanvasPolygon)):
            map_object.delete()

    def manage_z_order(self):
        self.canvas.lift("polygon")
        self.canvas.lift("path")
        self.canvas.lift("marker")
        self.canvas.lift("marker_image")
        self.canvas.lift("corner")
        self.canvas.lift("button")

    def pre_cache(self):
        """ single threaded pre-chache tile images in area of self.pre_cache_position """

        last_pre_cache_position = None
        radius = 1
        zoom = round(self.zoom)

        if self.database_path is not None:
            db_connection = sqlite3.connect(self.database_path)
            db_cursor = db_connection.cursor()
        else:
            db_cursor = None

        while True:
            if last_pre_cache_position != self.pre_cache_position:
                last_pre_cache_position = self.pre_cache_position
                zoom = round(self.zoom)
                radius = 1

            if last_pre_cache_position is not None and radius <= 8:

                # pre cache top and bottom row
                for x in range(self.pre_cache_position[0] - radius, self.pre_cache_position[0] + radius + 1):
                    if f"{zoom}{x}{self.pre_cache_position[1] + radius}" not in self.tile_image_cache:
                        self.request_image(zoom, x, self.pre_cache_position[1] + radius, db_cursor=db_cursor)
                    if f"{zoom}{x}{self.pre_cache_position[1] - radius}" not in self.tile_image_cache:
                        self.request_image(zoom, x, self.pre_cache_position[1] - radius, db_cursor=db_cursor)

                # pre cache left and right column
                for y in range(self.pre_cache_position[1] - radius, self.pre_cache_position[1] + radius + 1):
                    if f"{zoom}{self.pre_cache_position[0] + radius}{y}" not in self.tile_image_cache:
                        self.request_image(zoom, self.pre_cache_position[0] + radius, y, db_cursor=db_cursor)
                    if f"{zoom}{self.pre_cache_position[0] - radius}{y}" not in self.tile_image_cache:
                        self.request_image(zoom, self.pre_cache_position[0] - radius, y, db_cursor=db_cursor)

                # raise the radius
                radius += 1

            else:
                time.sleep(0.1)

            # 10_000 images = 80 MB RAM-usage
            if len(self.tile_image_cache) > 10_000:  # delete random tiles if cache is too large
                # create list with keys to delete
                keys_to_delete = []
                for key in self.tile_image_cache.keys():
                    if len(self.tile_image_cache) - len(keys_to_delete) > 10_000:
                        keys_to_delete.append(key)

                # delete keys in list so that len(self.tile_image_cache) == 10_000
                for key in keys_to_delete:
                    del self.tile_image_cache[key]

    def request_image(self, zoom: int, x: int, y: int, db_cursor=None) -> ImageTk.PhotoImage:

        # if database is available check first if tile is in database, if not try to use server
        if db_cursor is not None:
            try:
                db_cursor.execute("SELECT t.tile_image FROM tiles t WHERE t.zoom=? AND t.x=? AND t.y=? AND t.server=?;",
                                  (zoom, x, y, self.tile_server))
                result = db_cursor.fetchone()

                if result is not None:
                    image = Image.open(io.BytesIO(result[0]))
                    image_tk = ImageTk.PhotoImage(image)
                    self.tile_image_cache[f"{zoom}{x}{y}"] = image_tk
                    return image_tk
                elif self.use_database_only:
                    return self.empty_tile_image
                else:
                    pass

            except sqlite3.OperationalError:
                if self.use_database_only:
                    return self.empty_tile_image
                else:
                    pass

            except Exception:
                return self.empty_tile_image

        # try to get the tile from the server
        try:
            url = self.tile_server.replace("{x}", str(x)).replace("{y}", str(y)).replace("{z}", str(zoom))
            image = Image.open(requests.get(url, stream=True, headers={"User-Agent": "TkinterMapView"}).raw)

            if self.overlay_tile_server is not None:
                url = self.overlay_tile_server.replace("{x}", str(x)).replace("{y}", str(y)).replace("{z}", str(zoom))
                image_overlay = Image.open(requests.get(url, stream=True, headers={"User-Agent": "TkinterMapView"}).raw)
                image = image.convert("RGBA")
                image_overlay = image_overlay.convert("RGBA")

                if image_overlay.size is not (self.tile_size, self.tile_size):
                    image_overlay = image_overlay.resize((self.tile_size, self.tile_size), Image.ANTIALIAS)

                image.paste(image_overlay, (0, 0), image_overlay)

            image_tk = ImageTk.PhotoImage(image)

            self.tile_image_cache[f"{zoom}{x}{y}"] = image_tk
            return image_tk

        except PIL.UnidentifiedImageError:  # image does not exist for given coordinates
            self.tile_image_cache[f"{zoom}{x}{y}"] = self.empty_tile_image
            return self.empty_tile_image

        except requests.exceptions.ConnectionError:
            return self.empty_tile_image

        except Exception:
            return self.empty_tile_image

    def get_tile_image_from_cache(self, zoom: int, x: int, y: int):
        if f"{zoom}{x}{y}" not in self.tile_image_cache:
            return False
        else:
            return self.tile_image_cache[f"{zoom}{x}{y}"]

    def load_images_background(self):
        if self.database_path is not None:
            db_connection = sqlite3.connect(self.database_path)
            db_cursor = db_connection.cursor()
        else:
            db_cursor = None

        while True:
            if len(self.image_load_queue_tasks) > 0:
                # task queue structure: [((zoom, x, y), corresponding canvas tile object), ... ]
                task = self.image_load_queue_tasks.pop()

                zoom = task[0][0]
                x, y = task[0][1], task[0][2]
                canvas_tile = task[1]

                image = self.get_tile_image_from_cache(zoom, x, y)
                if image is False:
                    image = self.request_image(zoom, x, y, db_cursor=db_cursor)
                    if image is None:
                        self.image_load_queue_tasks.append(task)
                        continue

                # result queue structure: [((zoom, x, y), corresponding canvas tile object, tile image), ... ]
                self.image_load_queue_results.append(((zoom, x, y), canvas_tile, image))

            else:
                time.sleep(0.01)

    def update_canvas_tile_images(self):

        while len(self.image_load_queue_results) > 0:
            # result queue structure: [((zoom, x, y), corresponding canvas tile object, tile image), ... ]
            result = self.image_load_queue_results.pop(0)

            zoom, x, y = result[0][0], result[0][1], result[0][2]
            canvas_tile = result[1]
            image = result[2]

            # check if zoom level of result is still up to date, otherwise don't update image
            if zoom == round(self.zoom):
                canvas_tile.set_image(image)

        # This function calls itself every 10 ms with tk.after() so that the image updates come
        # from the main GUI thread, because tkinter can only be updated from the main thread.
        self.after(10, self.update_canvas_tile_images)

    def insert_row(self, insert: int, y_name_position: int):

        for x_pos in range(len(self.canvas_tile_array)):
            tile_name_position = self.canvas_tile_array[x_pos][0].tile_name_position[0], y_name_position

            image = self.get_tile_image_from_cache(round(self.zoom), *tile_name_position)
            if image is False:
                canvas_tile = CanvasTile(self, self.not_loaded_tile_image, tile_name_position)
                self.image_load_queue_tasks.append(((round(self.zoom), *tile_name_position), canvas_tile))
            else:
                canvas_tile = CanvasTile(self, image, tile_name_position)

            canvas_tile.draw()

            self.canvas_tile_array[x_pos].insert(insert, canvas_tile)

    def insert_column(self, insert: int, x_name_position: int):
        canvas_tile_column = []

        for y_pos in range(len(self.canvas_tile_array[0])):
            tile_name_position = x_name_position, self.canvas_tile_array[0][y_pos].tile_name_position[1]

            image = self.get_tile_image_from_cache(round(self.zoom), *tile_name_position)
            if image is False:
                # image is not in image cache, load blank tile and append position to image_load_queue
                canvas_tile = CanvasTile(self, self.not_loaded_tile_image, tile_name_position)
                self.image_load_queue_tasks.append(((round(self.zoom), *tile_name_position), canvas_tile))
            else:
                # image is already in cache
                canvas_tile = CanvasTile(self, image, tile_name_position)

            canvas_tile.draw()

            canvas_tile_column.append(canvas_tile)

        self.canvas_tile_array.insert(insert, canvas_tile_column)

    def draw_initial_array(self):
        self.image_load_queue_tasks = []

        x_tile_range = math.ceil(self.lower_right_tile_pos[0]) - math.floor(self.upper_left_tile_pos[0])
        y_tile_range = math.ceil(self.lower_right_tile_pos[1]) - math.floor(self.upper_left_tile_pos[1])

        # upper left tile name position
        upper_left_x = math.floor(self.upper_left_tile_pos[0])
        upper_left_y = math.floor(self.upper_left_tile_pos[1])

        for x_pos in range(len(self.canvas_tile_array)):
            for y_pos in range(len(self.canvas_tile_array[0])):
                self.canvas_tile_array[x_pos][y_pos].__del__()

        # create tile array with size (x_tile_range x y_tile_range)
        self.canvas_tile_array = []

        for x_pos in range(x_tile_range):
            canvas_tile_column = []

            for y_pos in range(y_tile_range):
                tile_name_position = upper_left_x + x_pos, upper_left_y + y_pos

                image = self.get_tile_image_from_cache(round(self.zoom), *tile_name_position)
                if image is False:
                    # image is not in image cache, load blank tile and append position to image_load_queue
                    canvas_tile = CanvasTile(self, self.not_loaded_tile_image, tile_name_position)
                    self.image_load_queue_tasks.append(((round(self.zoom), *tile_name_position), canvas_tile))
                else:
                    # image is already in cache
                    canvas_tile = CanvasTile(self, image, tile_name_position)

                canvas_tile_column.append(canvas_tile)

            self.canvas_tile_array.append(canvas_tile_column)

        # draw all canvas tiles
        for x_pos in range(len(self.canvas_tile_array)):
            for y_pos in range(len(self.canvas_tile_array[0])):
                self.canvas_tile_array[x_pos][y_pos].draw()

        # draw other objects on canvas
        for marker in self.canvas_marker_list:
            marker.draw()
        for path in self.canvas_path_list:
            path.draw()
        for polygon in self.canvas_polygon_list:
            polygon.draw()

        # update pre-cache position
        self.pre_cache_position = (round((self.upper_left_tile_pos[0] + self.lower_right_tile_pos[0]) / 2),
                                   round((self.upper_left_tile_pos[1] + self.lower_right_tile_pos[1]) / 2))

    def draw_move(self, called_after_zoom: bool = False):

        if self.canvas_tile_array:

            # insert or delete rows on top
            top_y_name_position = self.canvas_tile_array[0][0].tile_name_position[1]
            top_y_diff = self.upper_left_tile_pos[1] - top_y_name_position
            if top_y_diff <= 0:
                for y_diff in range(1, math.ceil(-top_y_diff) + 1):
                    self.insert_row(insert=0, y_name_position=top_y_name_position - y_diff)
            elif top_y_diff >= 1:
                for y_diff in range(1, math.ceil(top_y_diff)):
                    for x in range(len(self.canvas_tile_array)-1, -1, -1):
                        if len(self.canvas_tile_array[x]) > 1:
                            self.canvas_tile_array[x][0].delete()
                            del self.canvas_tile_array[x][0]

            # insert or delete columns on left
            left_x_name_position = self.canvas_tile_array[0][0].tile_name_position[0]
            left_x_diff = self.upper_left_tile_pos[0] - left_x_name_position
            if left_x_diff <= 0:
                for x_diff in range(1, math.ceil(-left_x_diff) + 1):
                    self.insert_column(insert=0, x_name_position=left_x_name_position - x_diff)
            elif left_x_diff >= 1:
                for x_diff in range(1, math.ceil(left_x_diff)):
                    if len(self.canvas_tile_array) > 1:
                        for y in range(len(self.canvas_tile_array[0]) - 1, -1, -1):
                            self.canvas_tile_array[0][y].delete()
                            del self.canvas_tile_array[0][y]
                        del self.canvas_tile_array[0]

            # insert or delete rows on bottom
            bottom_y_name_position = self.canvas_tile_array[0][-1].tile_name_position[1]
            bottom_y_diff = self.lower_right_tile_pos[1] - bottom_y_name_position
            if bottom_y_diff >= 1:
                for y_diff in range(1, math.ceil(bottom_y_diff)):
                    self.insert_row(insert=len(self.canvas_tile_array[0]), y_name_position=bottom_y_name_position + y_diff)
            elif bottom_y_diff <= 1:
                for y_diff in range(1, math.ceil(-bottom_y_diff) + 1):
                    for x in range(len(self.canvas_tile_array)-1, -1, -1):
                        if len(self.canvas_tile_array[x]) > 1:
                            self.canvas_tile_array[x][-1].delete()
                            del self.canvas_tile_array[x][-1]

            # insert or delete columns on right
            right_x_name_position = self.canvas_tile_array[-1][0].tile_name_position[0]
            right_x_diff = self.lower_right_tile_pos[0] - right_x_name_position
            if right_x_diff >= 1:
                for x_diff in range(1, math.ceil(right_x_diff)):
                    self.insert_column(insert=len(self.canvas_tile_array), x_name_position=right_x_name_position + x_diff)
            elif right_x_diff <= 1:
                for x_diff in range(1, math.ceil(-right_x_diff) + 1):
                    if len(self.canvas_tile_array) > 1:
                        for y in range(len(self.canvas_tile_array[-1]) - 1, -1, -1):
                            self.canvas_tile_array[-1][y].delete()
                            del self.canvas_tile_array[-1][y]
                        del self.canvas_tile_array[-1]

            # draw all canvas tiles
            for x_pos in range(len(self.canvas_tile_array)):
                for y_pos in range(len(self.canvas_tile_array[0])):
                    self.canvas_tile_array[x_pos][y_pos].draw()

            # draw other objects on canvas
            for marker in self.canvas_marker_list:
                marker.draw()
            for path in self.canvas_path_list:
                path.draw(move=not called_after_zoom)
            for polygon in self.canvas_polygon_list:
                polygon.draw(move=not called_after_zoom)

            # update pre-cache position
            self.pre_cache_position = (round((self.upper_left_tile_pos[0] + self.lower_right_tile_pos[0]) / 2),
                                       round((self.upper_left_tile_pos[1] + self.lower_right_tile_pos[1]) / 2))

    def draw_zoom(self):

        if self.canvas_tile_array:
            # clear tile image loading queue, so that no old images from other zoom levels get displayed
            self.image_load_queue_tasks = []

            # upper left tile name position
            upper_left_x = math.floor(self.upper_left_tile_pos[0])
            upper_left_y = math.floor(self.upper_left_tile_pos[1])

            for x_pos in range(len(self.canvas_tile_array)):
                for y_pos in range(len(self.canvas_tile_array[0])):

                    tile_name_position = upper_left_x + x_pos, upper_left_y + y_pos

                    image = self.get_tile_image_from_cache(round(self.zoom), *tile_name_position)
                    if image is False:
                        image = self.not_loaded_tile_image
                        # noinspection PyCompatibility
                        self.image_load_queue_tasks.append(((round(self.zoom), *tile_name_position), self.canvas_tile_array[x_pos][y_pos]))

                    self.canvas_tile_array[x_pos][y_pos].set_image_and_position(image, tile_name_position)

            self.pre_cache_position = (round((self.upper_left_tile_pos[0] + self.lower_right_tile_pos[0]) / 2),
                                       round((self.upper_left_tile_pos[1] + self.lower_right_tile_pos[1]) / 2))

            self.draw_move(called_after_zoom=True)

    def mouse_move(self, event):
        # calculate moving difference from last mouse position
        mouse_move_x = self.last_mouse_down_position[0] - event.x
        mouse_move_y = self.last_mouse_down_position[1] - event.y

        # set move velocity for movement fading out
        delta_t = time.time() - self.last_mouse_down_time
        if delta_t == 0:
            self.move_velocity = (0, 0)
        else:
            self.move_velocity = (mouse_move_x / delta_t, mouse_move_y / delta_t)

        # save current mouse position for next move event
        self.last_mouse_down_position = (event.x, event.y)
        self.last_mouse_down_time = time.time()

        # calculate exact tile size of widget
        tile_x_range = self.lower_right_tile_pos[0] - self.upper_left_tile_pos[0]
        tile_y_range = self.lower_right_tile_pos[1] - self.upper_left_tile_pos[1]

        # calculate the movement in tile coordinates
        tile_move_x = (mouse_move_x / self.width) * tile_x_range
        tile_move_y = (mouse_move_y / self.height) * tile_y_range

        # calculate new corner tile positions
        self.lower_right_tile_pos = (self.lower_right_tile_pos[0] + tile_move_x, self.lower_right_tile_pos[1] + tile_move_y)
        self.upper_left_tile_pos = (self.upper_left_tile_pos[0] + tile_move_x, self.upper_left_tile_pos[1] + tile_move_y)

        self.check_map_border_crossing()
        self.draw_move()

    def mouse_click(self, event):
        self.fading_possible = False

        self.mouse_click_position = (event.x, event.y)

        # save mouse position where mouse is pressed down for moving
        self.last_mouse_down_position = (event.x, event.y)
        self.last_mouse_down_time = time.time()

    def mouse_release(self, event):
        self.fading_possible = True
        self.last_move_time = time.time()

        # check if mouse moved after mouse click event
        if self.mouse_click_position == (event.x, event.y):
            # mouse didn't move
            if self.map_click_callback is not None:
                # get decimal coords of current mouse position
                coordinate_mouse_pos = self.convert_canvas_coords_to_decimal_coords(event.x, event.y)
                self.map_click_callback(coordinate_mouse_pos)
        else:
            # mouse was moved, start fading animation
            self.after(1, self.fading_move)

    def fading_move(self):
        delta_t = time.time() - self.last_move_time
        self.last_move_time = time.time()

        # only do fading when at least 10 fps possible and fading is possible (no mouse movement at the moment)
        if delta_t < 0.1 and self.fading_possible is True:

            # calculate fading velocity
            mouse_move_x = self.move_velocity[0] * delta_t
            mouse_move_y = self.move_velocity[1] * delta_t

            # lower the fading velocity
            lowering_factor = 2 ** (-9 * delta_t)
            self.move_velocity = (self.move_velocity[0] * lowering_factor, self.move_velocity[1] * lowering_factor)

            # calculate exact tile size of widget
            tile_x_range = self.lower_right_tile_pos[0] - self.upper_left_tile_pos[0]
            tile_y_range = self.lower_right_tile_pos[1] - self.upper_left_tile_pos[1]

            # calculate the movement in tile coordinates
            tile_move_x = (mouse_move_x / self.width) * tile_x_range
            tile_move_y = (mouse_move_y / self.height) * tile_y_range

            # calculate new corner tile positions
            self.lower_right_tile_pos = (self.lower_right_tile_pos[0] + tile_move_x, self.lower_right_tile_pos[1] + tile_move_y)
            self.upper_left_tile_pos = (self.upper_left_tile_pos[0] + tile_move_x, self.upper_left_tile_pos[1] + tile_move_y)

            self.check_map_border_crossing()
            self.draw_move()

            if abs(self.move_velocity[0]) > 1 or abs(self.move_velocity[1]) > 1:
                self.after(1, self.fading_move)

    def set_zoom(self, zoom: int, relative_pointer_x: float = 0.5, relative_pointer_y: float = 0.5):

        mouse_tile_pos_x = self.upper_left_tile_pos[0] + (self.lower_right_tile_pos[0] - self.upper_left_tile_pos[0]) * relative_pointer_x
        mouse_tile_pos_y = self.upper_left_tile_pos[1] + (self.lower_right_tile_pos[1] - self.upper_left_tile_pos[1]) * relative_pointer_y

        current_deg_mouse_position = osm_to_decimal(mouse_tile_pos_x,
                                                    mouse_tile_pos_y,
                                                    round(self.zoom))
        self.zoom = zoom

        if self.zoom > self.max_zoom:
            self.zoom = self.max_zoom
        if self.zoom < self.min_zoom:
            self.zoom = self.min_zoom

        current_tile_mouse_position = decimal_to_osm(*current_deg_mouse_position, round(self.zoom))

        self.upper_left_tile_pos = (current_tile_mouse_position[0] - relative_pointer_x * (self.width / self.tile_size),
                                    current_tile_mouse_position[1] - relative_pointer_y * (self.height / self.tile_size))

        self.lower_right_tile_pos = (current_tile_mouse_position[0] + (1 - relative_pointer_x) * (self.width / self.tile_size),
                                     current_tile_mouse_position[1] + (1 - relative_pointer_y) * (self.height / self.tile_size))

        if round(self.zoom) != round(self.last_zoom):
            self.check_map_border_crossing()
            self.draw_zoom()
            self.last_zoom = round(self.zoom)

    def mouse_zoom(self, event):
        relative_mouse_x = event.x / self.width  # mouse pointer position on map (x=[0..1], y=[0..1])
        relative_mouse_y = event.y / self.height

        if sys.platform == "darwin":
            new_zoom = self.zoom + event.delta * 0.1
        elif sys.platform.startswith("win"):
            new_zoom = self.zoom + event.delta * 0.01
        elif event.num == 4:
            new_zoom = self.zoom + 1
        elif event.num == 5:
            new_zoom = self.zoom - 1
        else:
            new_zoom = self.zoom + event.delta * 0.1

        self.set_zoom(new_zoom, relative_pointer_x=relative_mouse_x, relative_pointer_y=relative_mouse_y)

    def check_map_border_crossing(self):
        diff_x, diff_y = 0, 0
        if self.upper_left_tile_pos[0] < 0:
            diff_x += 0 - self.upper_left_tile_pos[0]

        if self.upper_left_tile_pos[1] < 0:
            diff_y += 0 - self.upper_left_tile_pos[1]
        if self.lower_right_tile_pos[0] > 2 ** round(self.zoom):
            diff_x -= self.lower_right_tile_pos[0] - (2 ** round(self.zoom))
        if self.lower_right_tile_pos[1] > 2 ** round(self.zoom):
            diff_y -= self.lower_right_tile_pos[1] - (2 ** round(self.zoom))

        self.upper_left_tile_pos = self.upper_left_tile_pos[0] + diff_x, self.upper_left_tile_pos[1] + diff_y
        self.lower_right_tile_pos = self.lower_right_tile_pos[0] + diff_x, self.lower_right_tile_pos[1] + diff_y

    def button_zoom_in(self):
        # zoom into middle of map
        self.set_zoom(self.zoom + 1, relative_pointer_x=0.5, relative_pointer_y=0.5)

    def button_zoom_out(self):
        # zoom out of middle of map
        self.set_zoom(self.zoom - 1, relative_pointer_x=0.5, relative_pointer_y=0.5)
