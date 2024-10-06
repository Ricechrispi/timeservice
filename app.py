from flask import Flask, request

import matplotlib.pyplot as plt
import geopandas as gpd
import numpy as np
from shapely import Point

app = Flask(__name__)

class TimeService:
    def __init__(self, path: str = "world/tz_world.shp"):
        self.path = path
        self.timezones = None
        self.gdf = None

    def _parse_shapefile(self):
        self.gdf = gpd.read_file(self.path)
        # print(self.gdf.columns)
        # print(self.gdf.head())
        self.timezones = list(set(self.gdf["TZID"]))
        self.timezones.sort()

    def timezones_list(self) -> str:
        """
        Delivers all available timezones

        :return: All available timezones
        """
        if self.timezones is None:
            self._parse_shapefile()
        return self.timezones

    def timezone_at_coordinate(self, lat: float, lon: float) -> str:
        """
        Deliver timezone for specified coordinate given a geographic latitude/longitude in EPSG:4326 coordinate reference system

        :param lat: Geographic latitude
        :param lon: Geographic longitude
        :return: The timezone for specified coordinate
        """
        if self.gdf is None:
            self._parse_shapefile()

        print(f"timezones with args: {lat} & {lon}")

        containing_polygon_index = np.where(self.gdf.contains(Point(lon, lat)))[0]
        print(containing_polygon_index)
        print(self.gdf.iloc[containing_polygon_index])

        requested_timezone = ""

        # The endpoint shall return a meaningful timezones for uninhabited zones.
        if containing_polygon_index.size == 0: # point is inside no polygons
            # meaningful options: easiest: the closest polygon
            #                     more elaborate: the poly that is closest vertically
            #                     hybrid: if close to a polygon (i.e. 370 km from coast) then the closest one
            #                               otherwise calc international waters:
            # Timezones at sea
            # The tz database says: “A ship within the territorial waters of any nation uses that nation's time.
            # In international waters, time zone boundaries are meridians 15° apart, except that UTC−12 and UTC+12 are each 7.5°
            # wide and are separated by the 180° meridian (not by the International Date Line, which is for land and territorial waters only).
            # A captain can change ship's clocks any time after entering a new time zone; midnight changes are common.”
            #
            # While the boundaries in international waters are not difficult to construct, the boundaries of territorial
            # waters are a completely different story, and are similar to the boundaries between countries.
            # Unfortunately, VMAP0 does not provide geometries for the territorial waters. As a consequence,
            # the shapefiles presented here do not cover seas and oceans.
            # def international_time(lon):
            #       at 0: UTC
            #       at 15: UTC+1
            #       at -15: UTC-1
            #       at 165: UTC+11
            #       at -165: UTC-11
            #       at 180/-180
            #       at 172.5
            #       at -172.5




            pass
        elif containing_polygon_index.size > 1: # point is inside multiple polygons
            print("ERROR! TBD") #TODO
            pass
        else: # point is inside 1 polygon
            requested_timezone = self.gdf.iloc[containing_polygon_index]["TZID"].item()

        return requested_timezone


#TODO rethink if class is necessary, currently used to make everything lazy
time_service = TimeService()

@app.route('/timezones')
def timezones():

    print(request.args)
    lat = None
    lon = None

    if len(request.args) == 2 and "lat" in request.args.keys() and "lon" in request.args.keys():
        lat = request.args.get("lat")
        lon = request.args.get("lon")

    if lat and lon:
        # todo sanitize input
        return time_service.timezone_at_coordinate(float(lat), float(lon))
    else:
        return time_service.timezones_list()

if __name__ == '__main__':
    app.run()


# Create a microservice that has the following endpoint
#
# /timezones
# ** Delivers all available timezones
# /timezones?lat=y&lon=x
# ** Deliver timezone for specified coordinate given a geographic latitude/longitude in EPSG:4326 coordinate reference system
#  EPSG:4326 / WGS 84:
#       WGS84 Bounds: -180.0, -90.0, 180.0, 90.0
#       UoM: degree
#       EPSG:4326 is defined as longitude-latitude.


# As a data source the timezone world shapefile from http://efele.net/maps/tz/world/ should be used.
# The endpoint shall return a meaningful timezones for uninhabited zones.
# The microservice shall be developed in python and be install/runnable on ubuntu 22.04, ideally containerized.
# You can use any frameworks/libraries you desire.
