import tkinter
import tkinter.messagebox
import os
import customtkinter
from tkinter_map_widget import TkinterMapWidget

MAIN_PATH = os.path.dirname(__file__)


class App(tkinter.Tk):

    APP_NAME = "TkinterMapView demo"
    ABOUT_TEXT = ""
    WIDTH = 800
    HEIGHT = 790

    def __init__(self, *args, **kwargs):
        customtkinter.enable_macos_darkmode()
        tkinter.Tk.__init__(self, *args, **kwargs)

        self.resizable(False, False)
        self.title(self.APP_NAME)
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.bind("<Command-q>", self.on_closing)
        self.bind("<Command-w>", self.on_closing)
        self.bind("<Return>", self.search)

        self.menubar = tkinter.Menu(master=self)
        self.app_menu = tkinter.Menu(self.menubar, name='apple')
        self.menubar.add_cascade(menu=self.app_menu)
        self.app_menu.add_command(label='About ' + self.APP_NAME, command=self.about_dialog)
        self.app_menu.add_separator()
        self.config(menu=self.menubar)
        self.createcommand('tk::mac::Quit', self.on_closing)

        self.search_bar = tkinter.Entry(self, width=60)
        self.search_bar.place(x=10, y=25, anchor=tkinter.W)
        self.search_bar.focus()

        self.search_bar_button = customtkinter.CTkButton(master=self, width=100, height=25, text="Search", command=self.search)
        self.search_bar_button.place(x=573, y=25, anchor=tkinter.W)

        self.search_bar_clear = customtkinter.CTkButton(master=self, width=100, height=25, text="Clear", command=self.clear)
        self.search_bar_clear.place(x=688, y=25, anchor=tkinter.W)

        self.map_widget = TkinterMapWidget(width=self.WIDTH, height=600, corner_radius=0)
        self.map_widget.place(x=0, y=50, anchor=tkinter.NW)

        self.marker_list_box = tkinter.Listbox(self, width=55, height=7)
        self.marker_list_box.place(x=292, y=660)

        self.marker_list = []
        self.marker_path = None

        self.save_marker_button = customtkinter.CTkButton(master=self, width=250, height=25, text="save current marker",
                                                          command=self.save_marker)
        self.save_marker_button.place(x=20, y=665, anchor=tkinter.NW)

        self.clear_marker_button = customtkinter.CTkButton(master=self, width=250, height=25, text="clear marker list",
                                                          command=self.clear_marker_list)
        self.clear_marker_button.place(x=20, y=705, anchor=tkinter.NW)

        self.connect_marker_button = customtkinter.CTkButton(master=self, width=250, height=25, text="connect marker with path",
                                                             command=self.connect_marker)
        self.connect_marker_button.place(x=20, y=745, anchor=tkinter.NW)

        self.map_widget.set_address("Siegessäule")
        self.map_widget.set_zoom(17)

        self.search_marker = None
        self.search_in_progress = False

    def search(self, event=None):
        if not self.search_in_progress:
            self.search_in_progress = True
            if self.search_marker not in self.marker_list:
                self.map_widget.delete(self.search_marker)

            address = self.search_bar.get()
            self.search_marker = self.map_widget.set_address(address, marker=True)
            if self.search_marker is False:
                # address was invalid (return value is False)
                self.search_marker = None
            self.search_in_progress = False

    def save_marker(self):
        if self.search_marker is not None:
            self.marker_list_box.insert(tkinter.END, f" {len(self.marker_list)}. {self.search_marker.text} ")
            self.marker_list_box.see(tkinter.END)
            self.marker_list.append(self.search_marker)

    def clear_marker_list(self):
        for marker in self.marker_list:
            self.map_widget.delete(marker)

        self.marker_list_box.delete(0, tkinter.END)
        self.marker_list.clear()
        self.connect_marker()

    def connect_marker(self):
        print(self.marker_list)
        position_list = []

        for marker in self.marker_list:
            position_list.append(marker.position)

        if self.marker_path is not None:
            self.map_widget.delete(self.marker_path)

        if len(position_list) > 0:
            self.marker_path = self.map_widget.set_path(position_list)

    def clear(self):
        self.search_bar.delete(0, last=tkinter.END)
        self.map_widget.delete(self.search_marker)

    def about_dialog(self):
        tkinter.messagebox.showinfo(title=self.APP_NAME,
                                    message=self.ABOUT_TEXT)

    def on_closing(self, event=0):
        customtkinter.disable_macos_darkmode()
        exit()

    def start(self):
        self.mainloop()


if __name__ == "__main__":
    app = App()
    app.start()
