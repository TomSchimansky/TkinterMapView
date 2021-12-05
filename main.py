import tkinter
import tkinter.messagebox
import os
import customtkinter
from map_widget import CTkMapWidget

MAIN_PATH = os.path.dirname(__file__)


class App(tkinter.Tk):
    APP_NAME = "OSM map widget"
    ABOUT_TEXT = ""
    WIDTH = 800
    HEIGHT = 600

    def __init__(self, *args, **kwargs):
        customtkinter.enable_macos_darkmode()
        tkinter.Tk.__init__(self, *args, **kwargs)

        self.minsize(self.WIDTH, self.HEIGHT)
        self.maxsize(self.WIDTH, self.HEIGHT)
        self.resizable(True, True)
        self.title(self.APP_NAME)
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.bind("<Command-q>", self.on_closing)
        self.bind("<Command-w>", self.on_closing)

        self.menubar = tkinter.Menu(master=self)
        self.app_menu = tkinter.Menu(self.menubar, name='apple')
        self.menubar.add_cascade(menu=self.app_menu)
        self.app_menu.add_command(label='About ' + self.APP_NAME, command=self.about_dialog)
        self.app_menu.add_separator()
        self.config(menu=self.menubar)
        self.createcommand('tk::mac::Quit', self.on_closing)

        self.map_widget = CTkMapWidget(width=self.WIDTH, height=self.HEIGHT)
        self.map_widget.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

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
