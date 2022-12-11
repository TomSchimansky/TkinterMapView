__version__ = "1.18"

from .map_widget import TkinterMapView
from .offline_loading import OfflineLoader
from .utility_functions import convert_coordinates_to_address, convert_coordinates_to_country, convert_coordinates_to_city
from .utility_functions import convert_address_to_coordinates
from .utility_functions import decimal_to_osm, osm_to_decimal
