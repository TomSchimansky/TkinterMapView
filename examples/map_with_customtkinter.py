import tkinter
import tkinter.messagebox
import customtkinter
from tkintermapview import TkinterMapView

customtkinter.set_appearance_mode("System")  # Other: "Light", "Dark"


class App(tkinter.Tk):

    APP_NAME = "TkinterMapView with CustomTkinter example"
    WIDTH = 700
    HEIGHT = 380

    def __init__(self, *args, **kwargs):
        customtkinter.enable_macos_darkmode()

        tkinter.Tk.__init__(self, *args, **kwargs)

        self.title(App.APP_NAME)
        self.geometry(str(App.WIDTH) + "x" + str(App.HEIGHT))
        self.minsize(App.WIDTH, App.HEIGHT)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.bind("<Command-q>", self.on_closing)
        self.bind("<Command-w>", self.on_closing)
        self.createcommand('tk::mac::Quit', self.on_closing)

        # ============ create two CTkFrames ============

        self.frame_left = customtkinter.CTkFrame(master=self,
                                                 width=150,
                                                 height=App.HEIGHT-40,
                                                 corner_radius=10)
        self.frame_left.place(x=20, rely=0.5, anchor=tkinter.W)

        self.frame_right = customtkinter.CTkFrame(master=self,
                                                  width=490,
                                                  height=App.HEIGHT-40,
                                                  corner_radius=10)
        self.frame_right.place(x=190, rely=0.5, anchor=tkinter.W)

        # ============ frame_left ============

        self.button_1 = customtkinter.CTkButton(master=self.frame_left,
                                                text="CTkButton",
                                                command=None,
                                                width=110, height=30,
                                                border_width=0,
                                                corner_radius=8)
        self.button_1.place(relx=0.5, y=40, anchor=tkinter.CENTER)

        self.button_2 = customtkinter.CTkButton(master=self.frame_left,
                                                text="CTkButton",
                                                command=None,
                                                width=110, height=30,
                                                border_width=0,
                                                corner_radius=8)
        self.button_2.place(relx=0.5, y=85, anchor=tkinter.CENTER)

        self.check_box_1 = customtkinter.CTkCheckBox(master=self.frame_left,
                                                     text="CheckBox")
        self.check_box_1.place(relx=0.5, y=130, anchor=tkinter.CENTER)

        # ============ frame_right -> map_widget ============

        self.map_widget = TkinterMapView(self.frame_right, width=450, height=250, corner_radius=10)
        self.map_widget.place(x=20, y=20, anchor=tkinter.NW)
        self.map_widget.set_address("Berlin")

        # ============ frame_right <- ============

        self.slider_1 = customtkinter.CTkSlider(master=self.frame_right,
                                                width=160,
                                                height=16,
                                                from_=0, to=19,
                                                border_width=5,
                                                command=self.slider_event)
        self.slider_1.place(x=310, y=295, anchor=tkinter.NW)
        self.slider_1.set(self.map_widget.zoom)

        self.entry = customtkinter.CTkEntry(master=self.frame_right,
                                            width=120,
                                            height=30,
                                            corner_radius=8)
        self.entry.place(x=20, y=290, anchor=tkinter.NW)
        self.entry.insert(0, "CTkEntry")

        self.button_5 = customtkinter.CTkButton(master=self.frame_right,
                                                height=30,
                                                text="Search",
                                                command=self.button_event,
                                                border_width=0,
                                                corner_radius=8)
        self.button_5.place(x=160, y=290, anchor=tkinter.NW)

    def button_event(self):
        self.map_widget.set_address(self.entry.get())
        self.slider_1.set(self.map_widget.zoom)

    def slider_event(self, value):
        self.map_widget.set_zoom(value)

    def on_closing(self, event=0):
        customtkinter.disable_macos_darkmode()
        self.destroy()

    def start(self):
        self.mainloop()


if __name__ == "__main__":
    app = App()
    app.start()
