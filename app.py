# Create a microservice that has the following endpoint
#
# /timezones
# ** Delivers all available timezones
# /timezones?lat=y&lon=x
# ** Deliver timezone for specified coordinate given a geographic latitude/longitude in EPSG:4326 coordinate reference system
#
#
# As a data source the timezone world shapefile from http://efele.net/maps/tz/world/ should be used.
# The endpoint shall return a meaningful timezones for uninhabited zones.
#
# The microservice shall be developed in python and be install/runnable on ubuntu 22.04, ideally containerized.
# You can use any frameworks/libraries you desire.

from flask import Flask, request
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

        # The endpoint shall return a meaningful timezone for uninhabited zones.
        if containing_polygon_index.size == 0: # point is inside no polygons
            # step 1: calc offset
            if lon > 172.5:
                offset = 12
            elif lon < -172.5:
                offset = -12
            else:
                offset = int(lon / 15)

            # step 2: create utc string
            if offset > 0:
                utc_string = f"UTC+{offset}"
            elif offset < 0:
                utc_string = f"UTC{offset}"
            else: # offset == 0
                utc_string = "UTC"

            return utc_string

        elif containing_polygon_index.size > 1: # point is inside multiple polygons
            # This can only happen if polygons overlap.
            # There is no "correct" polygon to choose, so pick the first one
            print("Point is inside multiple polygons, picking the first one")
            containing_polygon_index = containing_polygon_index[0]

        # point is inside 1 polygon
        requested_timezone = self.gdf.iloc[containing_polygon_index]["TZID"].item()
        return requested_timezone


time_service = TimeService()

@app.route('/timezones')
def timezones():

    print(request.args)
    lat = None
    lon = None

    if len(request.args) == 2 and "lat" in request.args.keys() and "lon" in request.args.keys():
        lat = request.args.get("lat")
        lon = request.args.get("lon")

    if lat is not None and lon is not None:
        try:
            sanitized_lat = float(lat)
            sanitized_lon = float(lon)
            if sanitized_lon > 180 or sanitized_lon < -180 or sanitized_lat > 90 or sanitized_lat < -90:
                raise ValueError

        except ValueError:
            return "Please provide valid latitude and longitude"

        return time_service.timezone_at_coordinate(sanitized_lat, sanitized_lon)
    else:
        return time_service.timezones_list()

if __name__ == '__main__':
    app.run()
