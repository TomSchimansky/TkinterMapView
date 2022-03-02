import tkinter
import customtkinter
from tkintermapview import TkinterMapView


class App(customtkinter.CTk):

    APP_NAME = "TkinterMapView with CustomTkinter example"
    WIDTH = 800
    HEIGHT = 500

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title(App.APP_NAME)
        self.geometry(str(App.WIDTH) + "x" + str(App.HEIGHT))
        self.minsize(App.WIDTH, App.HEIGHT)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.bind("<Command-q>", self.on_closing)
        self.bind("<Command-w>", self.on_closing)
        self.createcommand('tk::mac::Quit', self.on_closing)

        self.marker_list = []

        # ============ create two CTkFrames ============

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.frame_left = customtkinter.CTkFrame(master=self,
                                                 width=150)
        self.frame_left.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.frame_right = customtkinter.CTkFrame(master=self,
                                                  corner_radius=10)
        self.frame_right.grid(row=0, column=1, rowspan=1, pady=20, padx=20, sticky="nsew")

        # ============ frame_left ============

        self.frame_left.grid_rowconfigure(0, minsize=10)

        self.button_1 = customtkinter.CTkButton(master=self.frame_left,
                                                text="Set Marker",
                                                command=self.set_marker_event,
                                                width=120, height=30,
                                                border_width=0,
                                                corner_radius=8)
        self.button_1.grid(pady=10, padx=20, row=3, column=0)

        self.button_2 = customtkinter.CTkButton(master=self.frame_left,
                                                text="Clear Markers",
                                                command=self.clear_marker_event,
                                                width=120, height=30,
                                                border_width=0,
                                                corner_radius=8)
        self.button_2.grid(pady=10, padx=20, row=4, column=0)

        # ============ frame_right ============

        self.frame_right.grid_rowconfigure(0, weight=1)
        self.frame_right.grid_rowconfigure(1, weight=0)
        self.frame_right.grid_columnconfigure(0, weight=1)
        self.frame_right.grid_columnconfigure(1, weight=0)
        self.frame_right.grid_columnconfigure(2, weight=1)

        self.map_widget = TkinterMapView(self.frame_right, width=450, height=250, corner_radius=9)
        self.map_widget.grid(row=0, rowspan=1, column=0, columnspan=3, sticky="nswe", padx=20, pady=20)
        self.map_widget.set_address("Berlin")

        self.entry = customtkinter.CTkEntry(master=self.frame_right,
                                            placeholder_text="type address",
                                            width=140,
                                            height=30,
                                            corner_radius=8)
        self.entry.grid(row=1, column=0, sticky="we", padx=20, pady=20)
        self.entry.entry.bind("<Return>", self.search_event)

        self.button_5 = customtkinter.CTkButton(master=self.frame_right,
                                                height=30,
                                                text="Search",
                                                command=self.search_event,
                                                border_width=0,
                                                corner_radius=8)
        self.button_5.grid(row=1, column=1, sticky="w", padx=10, pady=20)

        self.slider_1 = customtkinter.CTkSlider(master=self.frame_right,
                                                width=200,
                                                height=16,
                                                from_=0, to=19,
                                                border_width=5,
                                                command=self.slider_event)
        self.slider_1.grid(row=1, column=2, sticky="e", padx=20, pady=20)
        self.slider_1.set(self.map_widget.zoom)

    def search_event(self, event=None):
        self.map_widget.set_address(self.entry.get())
        self.slider_1.set(self.map_widget.zoom)

    def slider_event(self, value):
        self.map_widget.set_zoom(value)

    def set_marker_event(self):
        current_position = self.map_widget.get_position()
        self.marker_list.append(self.map_widget.set_marker(current_position[0], current_position[1]))

    def clear_marker_event(self):
        for marker in self.marker_list:
            marker.delete()

    def on_closing(self, event=0):
        self.destroy()

    def start(self):
        self.mainloop()


if __name__ == "__main__":
    if float(customtkinter.__version__) < 3.2:
        print("Please update customtkinter: pip3 install customtkinter --upgrade")
        exit()

    app = App()
    app.start()
