import geocoder
import math
import os
import re
import sys
from typing import Union

from . import __version__


def default_user_agent() -> str:
    """ returns a User-Agent with the name of the running app, like "my_app (TkinterMapView/1.32)".
        OpenStreetMap blocks requests whose User-Agent doesn't identify the app:
        https://operations.osmfoundation.org/policies/tiles/ """

    app_name = os.path.splitext(os.path.basename(sys.argv[0]))[0] if sys.argv and sys.argv[0] else ""
    app_name = re.sub(r"[^A-Za-z0-9._-]", "", app_name).lstrip("-.")  # HTTP headers only allow some characters

    if app_name:
        return f"{app_name} (TkinterMapView/{__version__})"
    else:
        return f"TkinterMapView/{__version__}"


def decimal_to_osm(lat_deg: float, lon_deg: float, zoom: int) -> tuple:
    """ converts decimal coordinates to internal OSM coordinates"""

    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = (lon_deg + 180.0) / 360.0 * n
    ytile = (1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n
    return xtile, ytile


def osm_to_decimal(tile_x: Union[int, float], tile_y: Union[int, float], zoom: int) -> tuple:
    """ converts internal OSM coordinates to decimal coordinates """

    n = 2.0 ** zoom
    lon_deg = tile_x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * tile_y / n)))
    lat_deg = math.degrees(lat_rad)
    return lat_deg, lon_deg


def convert_coordinates_to_address(deg_x: float, deg_y: float) -> geocoder.osm_reverse.OsmReverse:
    """ returns address object with the following attributes:
        street, housenumber, postal, city, state, country, latlng
        Geocoder docs: https://geocoder.readthedocs.io/api.html#reverse-geocoding """

    result = geocoder.osm([deg_x, deg_y], method="reverse")
    return result


def convert_coordinates_to_city(deg_x: float, deg_y: float) -> str:
    """ returns city name """
    return geocoder.osm([deg_x, deg_y], method="reverse").city


def convert_coordinates_to_country(deg_x: float, deg_y: float) -> str:
    """ returns country name """
    return geocoder.osm([deg_x, deg_y], method="reverse").country
