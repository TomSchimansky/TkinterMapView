import tkinter
import tkintermapview

# create tkinter window
root_tk = tkinter.Tk()
root_tk.geometry(f"{1000}x{700}")
root_tk.title("map_view_polygon_example.py")

# create map widget
map_widget = tkintermapview.TkinterMapView(root_tk, width=1000, height=700, corner_radius=0)
map_widget.pack(fill="both", expand=True)


def polygon_click(polygon):
    print(f"polygon clicked - text: {polygon.name}")


switzerland_marker = map_widget.set_address("Switzerland", marker=True, text="Switzerland")
map_widget.set_zoom(8)

polygon_1 = map_widget.set_polygon([(46.0732306, 6.0095215),
                                    (46.3393433, 6.2072754),
                                    (46.5890691, 6.1083984),
                                    (46.7624431, 6.4270020),
                                    (47.2717751, 7.0312500),
                                    (47.4726629, 6.9982910),
                                    (47.4057853, 7.3718262),
                                    (47.5468716, 7.9650879),
                                    (47.5691138, 8.4045410),
                                    (47.7540980, 8.6242676),
                                    (47.5691138, 9.4482422),
                                    (47.1897125, 9.5581055),
                                    (46.9352609, 9.8327637),
                                    (46.9727564, 10.4150391),
                                    (46.6418940, 10.4479980),
                                    (46.4605655, 10.0744629),
                                    (46.2786312, 10.1513672),
                                    (46.3469276, 9.5581055),
                                    (46.4454275, 9.3493652),
                                    (45.8211434, 8.9538574),
                                    (46.1037088, 8.6352539),
                                    (46.3696741, 8.3496094),
                                    (45.9740604, 7.9321289),
                                    (45.8900082, 7.0971680),
                                    (46.1417827, 6.8664551),
                                    (46.4151388, 6.7236328),
                                    (46.3772542, 6.4160156)],
                                   # fill_color=None,
                                   # outline_color="red",
                                   # border_width=12,
                                   command=polygon_click,
                                   name="switzerland_polygon")

# polygon_1.remove_position(46.3772542, 6.4160156)
# polygon_1.add_position(0, 0, index=5)
# polygon_1.delete()

root_tk.mainloop()
