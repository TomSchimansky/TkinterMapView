import requests
import math
import threading
import tkinter
import time
import PIL
import sys
from PIL import Image, ImageTk


def deg2num(lat_deg, lon_deg, zoom):
    """ decimal coordinates to internal OSM coordinates"""

    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = (lon_deg + 180.0) / 360.0 * n
    ytile = (1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n
    return xtile, ytile


def num2deg(xtile, ytile, zoom):
    """ internal OSM coordinates to decimal coordinates """

    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return lat_deg, lon_deg


class CanvasPositionMarker:
    def __init__(self, map_widget: "CTkMapWidget", position, text=None):
        self.map_widget = map_widget
        self.position = position
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

    def delete(self):
        self.__del__()

    def appear(self):
        self.deleted = False

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

    def draw(self):
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
                        self.canvas_text = self.map_widget.canvas.create_text(canvas_pos_x, canvas_pos_y - 62,
                                                                              anchor=tkinter.CENTER,
                                                                              text=self.text,
                                                                              fill="#652A22",
                                                                              font="Tahoma 13 bold",
                                                                              tag="marker")
                    else:
                        self.map_widget.canvas.coords(self.canvas_text, canvas_pos_x, canvas_pos_y - 62)
                else:
                    if self.canvas_text is not None:
                        self.map_widget.canvas.delete(self.canvas_text)

            else:
                self.map_widget.canvas.delete(self.polygon, self.big_circle, self.canvas_text)
                self.polygon, self.big_circle, self.canvas_text = None, None, None

            self.map_widget.canvas.lift("marker")
            self.map_widget.canvas.lift("corner")
            self.map_widget.canvas.lift("button")


class CanvasTile:
    def __init__(self, map_widget: "CTkMapWidget", image, tile_name_position):
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
        self.map_widget.canvas.delete(self.canvas_object)

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

    def draw(self, image_update=False):

        # calculate canvas position fro OSM coordinates
        canvas_pos_x, canvas_pos_y = self.get_canvas_pos()

        if self.canvas_object is None:
            if not (self.image == self.map_widget.not_loaded_tile_image or self.image == self.image == self.map_widget.empty_tile_image):
                self.canvas_object = self.map_widget.canvas.create_image(canvas_pos_x,
                                                                         canvas_pos_y,
                                                                         image=self.image,
                                                                         anchor=tkinter.NW)
        else:
            self.map_widget.canvas.coords(self.canvas_object, canvas_pos_x, canvas_pos_y)

            if image_update:
                if not (
                        self.image == self.map_widget.not_loaded_tile_image or self.image == self.image == self.map_widget.empty_tile_image):
                    self.map_widget.canvas.itemconfig(self.canvas_object, image=self.image)
                else:
                    self.map_widget.canvas.delete(self.canvas_object)
                    self.canvas_object = None

        self.map_widget.canvas.lift("marker")
        self.map_widget.canvas.lift("corner")
        self.map_widget.canvas.lift("button")


class CanvasButton:
    def __init__(self, map_widget: "CTkMapWidget", canvas_position, width=16, height=16, text="", command=None):
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


class CTkMapWidget(tkinter.Frame):
    def __init__(self, *args,
                 width=200,
                 height=200,
                 corner_radius=0,
                 bg_color=None,
                 **kwargs):
        super().__init__(*args, **kwargs)

        self.width = width
        self.height = height
        self.corner_radius = corner_radius if corner_radius <= 30 else 30
        self.configure(width=self.width, height=self.height)

        if bg_color is None:
            self.bg_color = self.master.cget("bg")

        self.canvas = tkinter.Canvas(master=self,
                                     highlightthicknes=0,
                                     bg="#F1EFEA",
                                     width=self.width,
                                     height=self.height)
        self.canvas.place(x=0, y=0)

        # bind events for mouse button pressed, mouse movement, and scrolling
        self.canvas.bind("<B1-Motion>", self.mousemove)
        self.canvas.bind("<Button-1>", self.mouseclick)
        self.canvas.bind("<ButtonRelease-1>", self.mouserelease)
        self.canvas.bind("<MouseWheel>", self.mouseZoom)
        self.last_mouse_down_position = None
        self.last_mouse_down_time = None

        # movement fading
        self.fading_possible = True
        self.move_velocity = (0, 0)
        self.last_move_time = None

        # describes the tile layout
        self.zoom = 0
        self.upper_left_tile_pos = (0, 0)  # in OSM coords
        self.lower_right_tile_pos = (0, 0)
        self.tile_size = 256  # in pixel

        self.tile_image_cache = {}
        self.canvas_tile_array = []
        self.canvas_marker_list = []
        self.empty_tile_image = ImageTk.PhotoImage(Image.new("RGB", (256, 256), (190, 190, 190)))
        self.not_loaded_tile_image = ImageTk.PhotoImage(Image.new("RGB", (256, 256), (250, 250, 250)))
        self.tile_server = "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"
        self.overlay_tile_server = None
        self.max_zoom = 19
        self.min_zoom = math.ceil(math.log2(math.ceil(self.width / self.tile_size)))

        # pre caching for smoother movements (load tile images into cache at a certain radius around the pre_cache_position)
        self.pre_cache_position = None
        self.pre_cache_thread = threading.Thread(daemon=True, target=self.pre_cache)
        self.pre_cache_thread.start()

        # image loading in background threads
        self.image_load_queue_tasks = []
        self.image_load_queue_results = []
        self.after(10, self.update_canvas_tile_images)
        self.image_load_thread_pool = []

        for i in range(25):  # add 10 background threads which load tile images from self.image_load_queue_tasks
            image_load_thread = threading.Thread(daemon=True, target=self.load_images_background)
            image_load_thread.start()
            self.image_load_thread_pool.append(image_load_thread)

        # set initial position: Brandenburger Tor, Berlin
        self.set_position(52.516268, 13.377695)
        self.draw_initial_array()
        self.set_zoom(17)

        # zoom buttons
        self.button_zoom_in = CanvasButton(self, (20, 20), text="+", command=self.button_zoom_in)
        self.button_zoom_out = CanvasButton(self, (20, 60), text="-", command=self.button_zoom_out)

        # rounded corners
        if self.corner_radius > 0:
            radius = self.corner_radius
            self.canvas.create_arc(self.width - 2 * radius + 5, self.height - 2 * radius + 5, self.width + 5, self.height + 5,
                                   style=tkinter.ARC, tag="corner", width=10, outline=self.bg_color, start=-90)
            self.canvas.create_arc(2 * radius - 5, self.height - 2 * radius + 5, -5, self.height + 5,
                                   style=tkinter.ARC, tag="corner", width=10, outline=self.bg_color, start=180)
            self.canvas.create_arc(-5, -5, 2 * radius - 5, 2 * radius - 5,
                                   style=tkinter.ARC, tag="corner", width=10, outline=self.bg_color, start=-270)
            self.canvas.create_arc(self.width - 2 * radius + 5, -5, self.width + 5, 2 * radius - 5,
                                   style=tkinter.ARC, tag="corner", width=10, outline=self.bg_color, start=0)

    def set_overlay_tile_server(self, overlay_server):
        self.overlay_tile_server = overlay_server

    def set_tile_server(self, tile_server, tile_size=256, max_zoom=19):
        self.max_zoom = max_zoom
        self.tile_size = tile_size
        self.min_zoom = math.ceil(math.log2(math.ceil(self.width / self.tile_size)))
        self.tile_server = tile_server
        self.draw_initial_array()

    def set_position(self, deg_x, deg_y, text=None, marker=False):
        # convert given decimal coordinates to OSM coordinates and set corner positions accordingly
        current_tile_position = deg2num(deg_x, deg_y, self.zoom)
        self.upper_left_tile_pos = (current_tile_position[0] - ((self.width / 2) / self.tile_size),
                                    current_tile_position[1] - ((self.height / 2) / self.tile_size))

        self.lower_right_tile_pos = (current_tile_position[0] + ((self.width / 2) / self.tile_size),
                                     current_tile_position[1] + ((self.height / 2) / self.tile_size))

        if marker is True:
            self.set_marker(deg_x, deg_y, text)

        self.draw_initial_array()
        # self.draw_move()  # move can only handle position changes that big, so that the old and new view overlap

    def set_marker(self, deg_x, deg_y, text=None):
        marker = CanvasPositionMarker(self, (deg_x, deg_y), text=text)
        marker.draw()
        self.canvas_marker_list.append(marker)
        return marker

    def pre_cache(self):

        last_pre_cache_position = None
        radius = 1
        zoom = round(self.zoom)

        while True:
            if last_pre_cache_position != self.pre_cache_position:
                last_pre_cache_position = self.pre_cache_position
                zoom = round(self.zoom)
                radius = 1

            if last_pre_cache_position is not None and radius <= 8:

                # pre cache top and bottom row
                for x in range(self.pre_cache_position[0] - radius, self.pre_cache_position[0] + radius + 1):
                    if f"{zoom}{x}{self.pre_cache_position[1] + radius}" not in self.tile_image_cache:
                        self.request_image(zoom, x, self.pre_cache_position[1] + radius)
                    if f"{zoom}{x}{self.pre_cache_position[1] - radius}" not in self.tile_image_cache:
                        self.request_image(zoom, x, self.pre_cache_position[1] - radius)

                # pre cache left and right column
                for y in range(self.pre_cache_position[1] - radius, self.pre_cache_position[1] + radius + 1):
                    if f"{zoom}{self.pre_cache_position[0] + radius}{y}" not in self.tile_image_cache:
                        self.request_image(zoom, self.pre_cache_position[0] + radius, y)
                    if f"{zoom}{self.pre_cache_position[0] - radius}{y}" not in self.tile_image_cache:
                        self.request_image(zoom, self.pre_cache_position[0] - radius, y)

                # raise the radius
                radius += 1

            else:
                time.sleep(0.1)

            # 10.000 images = 80 MB RAM-usage
            if len(self.tile_image_cache) > 10_000:
                # delete older tile images...
                print("Very large cache!!!")

    def request_image(self, zoom, x, y):
        # request image from internet, does not check if its in cache
        try:
            url = self.tile_server.replace("{x}", str(x)).replace("{y}", str(y)).replace("{z}", str(zoom))
            image = Image.open(requests.get(url, stream=True).raw)

            if self.overlay_tile_server is not None:
                url = self.overlay_tile_server.replace("{x}", str(x)).replace("{y}", str(y)).replace("{z}", str(zoom))
                image_overlay = Image.open(requests.get(url, stream=True).raw)
                image = image.convert("RGBA")
                image_overlay = image_overlay.convert("RGBA")

                if image_overlay.size is not (self.tile_size, self.tile_size):
                    image_overlay = image_overlay.resize((self.tile_size, self.tile_size), Image.ANTIALIAS)

                image.paste(image_overlay, (0, 0), image_overlay)

            image_tk = ImageTk.PhotoImage(image)

            self.tile_image_cache[f"{zoom}{x}{y}"] = image_tk
            return image_tk

        except PIL.UnidentifiedImageError:
            self.tile_image_cache[f"{zoom}{x}{y}"] = self.empty_tile_image
            return self.empty_tile_image

        except requests.exceptions.ConnectionError as err:
            sys.stderr.write(f"{type(self).__name__} ConnectionError\n")
            return None

    def get_tile_image_from_cache(self, zoom, x, y):
        if f"{zoom}{x}{y}" not in self.tile_image_cache:
            return False
        else:
            return self.tile_image_cache[f"{zoom}{x}{y}"]

    def load_images_background(self):

        while True:
            if len(self.image_load_queue_tasks) > 0:
                # task queue structure: [((zoom, x, y), corresponding canvas tile object), ... ]
                task = self.image_load_queue_tasks.pop()

                zoom = task[0][0]
                x, y = task[0][1], task[0][2]
                canvas_tile = task[1]

                image = self.get_tile_image_from_cache(zoom, x, y)
                if image is False:
                    image = self.request_image(zoom, x, y)
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

    def insert_row(self, insert, y_name_position):

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

    def insert_column(self, insert, x_name_position):
        canvas_tile_column: list[CanvasTile] = []

        for y_pos in range(len(self.canvas_tile_array[0])):
            tile_name_position = x_name_position, self.canvas_tile_array[0][y_pos].tile_name_position[1]

            image = self.get_tile_image_from_cache(round(self.zoom), *tile_name_position)
            if image is False:
                canvas_tile = CanvasTile(self, self.not_loaded_tile_image, tile_name_position)
                self.image_load_queue_tasks.append(((round(self.zoom), *tile_name_position), canvas_tile))
            else:
                canvas_tile = CanvasTile(self, image, tile_name_position)

            canvas_tile.draw()

            canvas_tile_column.append(canvas_tile)

        self.canvas_tile_array.insert(insert, canvas_tile_column)

    def draw_initial_array(self):

        x_tile_range = math.ceil(self.lower_right_tile_pos[0]) - math.floor(self.upper_left_tile_pos[0])
        y_tile_range = math.ceil(self.lower_right_tile_pos[1]) - math.floor(self.upper_left_tile_pos[1])

        # upper left tile name position
        upper_left_x = math.floor(self.upper_left_tile_pos[0])
        upper_left_y = math.floor(self.upper_left_tile_pos[1])

        # create tile array with size (x_tile_range x y_tile_range)
        self.canvas_tile_array: list[list[CanvasTile]] = []

        for x_pos in range(x_tile_range):
            canvas_tile_column: list[CanvasTile] = []

            for y_pos in range(y_tile_range):
                tile_name_position = upper_left_x + x_pos, upper_left_y + y_pos

                image = self.get_tile_image_from_cache(round(self.zoom), *tile_name_position)
                if image is False:
                    canvas_tile = CanvasTile(self, self.not_loaded_tile_image, tile_name_position)
                    self.image_load_queue_tasks.append(((round(self.zoom), *tile_name_position), canvas_tile))
                else:
                    canvas_tile = CanvasTile(self, image, tile_name_position)

                canvas_tile_column.append(canvas_tile)

            self.canvas_tile_array.append(canvas_tile_column)

        for marker in self.canvas_marker_list:
            marker.draw()

        self.pre_cache_position = (round((self.upper_left_tile_pos[0] + self.lower_right_tile_pos[0]) / 2),
                                   round((self.upper_left_tile_pos[1] + self.lower_right_tile_pos[1]) / 2))

    def draw_move(self):

        if self.canvas_tile_array:

            for x_pos in range(len(self.canvas_tile_array)):
                for y_pos in range(len(self.canvas_tile_array[0])):
                    self.canvas_tile_array[x_pos][y_pos].draw()

            # insert or delete rows on top
            top_y_name_position = self.canvas_tile_array[0][0].tile_name_position[1]
            top_y_diff = self.upper_left_tile_pos[1] - top_y_name_position
            if top_y_diff <= 0:
                for y_diff in range(1, math.ceil(-top_y_diff) + 1):
                    self.insert_row(insert=0, y_name_position=top_y_name_position - y_diff)
            elif top_y_diff >= 1:
                for y_diff in range(1, math.ceil(top_y_diff)):
                    for x in range(len(self.canvas_tile_array)):
                        del self.canvas_tile_array[x][0]

            # insert or delete columns on left
            left_x_name_position = self.canvas_tile_array[0][0].tile_name_position[0]
            left_x_diff = self.upper_left_tile_pos[0] - left_x_name_position
            if left_x_diff <= 0:
                for x_diff in range(1, math.ceil(-left_x_diff) + 1):
                    self.insert_column(insert=0, x_name_position=left_x_name_position - x_diff)
            elif left_x_diff >= 1:
                for x_diff in range(1, math.ceil(left_x_diff)):
                    del self.canvas_tile_array[0]

            # insert or delete rows on bottom
            bottom_y_name_position = self.canvas_tile_array[0][-1].tile_name_position[1]
            bottom_y_diff = self.lower_right_tile_pos[1] - bottom_y_name_position
            if bottom_y_diff >= 1:
                for y_diff in range(1, math.ceil(bottom_y_diff)):
                    self.insert_row(insert=len(self.canvas_tile_array[0]), y_name_position=bottom_y_name_position + y_diff)
            elif bottom_y_diff <= 1:
                for y_diff in range(1, math.ceil(-bottom_y_diff) + 1):
                    for x in range(len(self.canvas_tile_array)):
                        del self.canvas_tile_array[x][-1]

            # insert or delete columns on right
            right_x_name_position = self.canvas_tile_array[-1][0].tile_name_position[0]
            right_x_diff = self.lower_right_tile_pos[0] - right_x_name_position
            if right_x_diff >= 1:
                for x_diff in range(1, math.ceil(right_x_diff)):
                    self.insert_column(insert=len(self.canvas_tile_array), x_name_position=right_x_name_position + x_diff)
            elif right_x_diff <= 1:
                for x_diff in range(1, math.ceil(-right_x_diff) + 1):
                    del self.canvas_tile_array[-1]

            for marker in self.canvas_marker_list:
                marker.draw()

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
                        self.image_load_queue_tasks.append(((round(self.zoom), *tile_name_position), self.canvas_tile_array[x_pos][y_pos]))

                    self.canvas_tile_array[x_pos][y_pos].set_image_and_position(image, tile_name_position)

            self.pre_cache_position = (round((self.upper_left_tile_pos[0] + self.lower_right_tile_pos[0]) / 2),
                                       round((self.upper_left_tile_pos[1] + self.lower_right_tile_pos[1]) / 2))
            self.draw_move()

    def mousemove(self, event):
        # calculate moving difference from last mouse position
        mouse_move_x = self.last_mouse_down_position[0] - event.x
        mouse_move_y = self.last_mouse_down_position[1] - event.y

        # set move velocity for movement fading out
        delta_t = time.time() - self.last_mouse_down_time
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

        self.draw_move()

    def mouseclick(self, event):
        self.fading_possible = False

        # save mouse position where mouse is pressed down for moving
        self.last_mouse_down_position = (event.x, event.y)
        self.last_mouse_down_time = time.time()

    def mouserelease(self, event):
        self.fading_possible = True
        self.last_move_time = time.time()

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

    def set_zoom(self, zoom, relative_pointer_x=0.5, relative_pointer_y=0.5):

        mouse_tile_pos_x = self.upper_left_tile_pos[0] + (self.lower_right_tile_pos[0] - self.upper_left_tile_pos[0]) * relative_pointer_x
        mouse_tile_pos_y = self.upper_left_tile_pos[1] + (self.lower_right_tile_pos[1] - self.upper_left_tile_pos[1]) * relative_pointer_y

        current_deg_mouse_position = num2deg(mouse_tile_pos_x,
                                             mouse_tile_pos_y,
                                             round(self.zoom))

        self.zoom = zoom

        if self.zoom > self.max_zoom:
            self.zoom = self.max_zoom
        if self.zoom < self.min_zoom:
            self.zoom = self.min_zoom

        current_tile_mouse_position = deg2num(*current_deg_mouse_position, round(self.zoom))

        self.upper_left_tile_pos = (current_tile_mouse_position[0] - relative_pointer_x * (self.width / self.tile_size),
                                    current_tile_mouse_position[1] - relative_pointer_y * (self.height / self.tile_size))

        self.lower_right_tile_pos = (current_tile_mouse_position[0] + (1 - relative_pointer_x) * (self.width / self.tile_size),
                                     current_tile_mouse_position[1] + (1 - relative_pointer_y) * (self.height / self.tile_size))

        self.check_map_border_crossing()
        self.draw_zoom()

    def mouseZoom(self, event):
        relative_mouse_x = event.x / self.width
        relative_mouse_y = event.y / self.height

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
        relative_mouse_x = 0.5
        relative_mouse_y = 0.5

        new_zoom = self.zoom + 1

        self.set_zoom(new_zoom, relative_pointer_x=relative_mouse_x, relative_pointer_y=relative_mouse_y)

    def button_zoom_out(self):
        relative_mouse_x = 0.5
        relative_mouse_y = 0.5

        new_zoom = self.zoom - 1

        self.set_zoom(new_zoom, relative_pointer_x=relative_mouse_x, relative_pointer_y=relative_mouse_y)
