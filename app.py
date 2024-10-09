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

import sys
import logging

# setup logging
file_handler = logging.FileHandler(filename="app.log")
stdout_handler = logging.StreamHandler(stream=sys.stdout)
logging.basicConfig(handlers=[file_handler, stdout_handler], level=logging.ERROR)
logger = logging.getLogger(__name__)

# setup flask
app = Flask(__name__)


class ShapeFileError(Exception):
    def __init__(self, ):
        self.message = "Internal Data Error"
        self.response_code = 500
        super().__init__()


class TimeService:
    def __init__(self, path: str = "world/tz_world.shp"):
        self.path = path
        self.timezones = None
        self.gdf = None

    def _parse_shapefile(self) -> None:
        try:
            self.gdf = gpd.read_file(self.path)
        except Exception as e:
            # catching "Exception" is bad, but geopandas does not raise the standard IOError here
            logger.error(f"Could not read the input file: {self.path}. Exception: {e}")
            raise ShapeFileError()

        self.timezones = list(set(self.gdf["TZID"]))
        self.timezones.sort()

    def timezones_list(self) -> [dict[str, list[str]], (dict[str, str], int)]:
        """
        Delivers all available timezones

        :return: All available timezones as a sorted list
        """
        if self.timezones is None:
            try:
                self._parse_shapefile()
            except ShapeFileError as e:
                return {"error": e.message}, e.response_code
        return {"timezones": self.timezones}

    def timezone_at_coordinate(self, lat: float, lon: float) -> [dict[str, str], (dict[str, str], int)]:
        """
        Delivers the timezone for a specified coordinate given geographic latitude/longitude in EPSG:4326 coordinate reference system

        :param lat: Geographic latitude
        :param lon: Geographic longitude
        :return: The timezone for specified coordinate
        """
        if self.gdf is None:
            try:
                self._parse_shapefile()
            except ShapeFileError as e:
                return {"error": e.message}, e.response_code

        logger.info(f"timezones with args: lat: {lat} lon: {lon}")

        # get the index of the polygon in the shapefile that contains the lat & long point
        containing_polygon_index = np.where(self.gdf.contains(Point(lon, lat)))[0]
        logger.debug(f"containing_polygon_index: {containing_polygon_index}")

        if containing_polygon_index.size == 0:  # point is inside no polygons, i.e. in the sea
            requested_timezone = self._calculate_utc_approximation(lon)

        elif containing_polygon_index.size >= 1:  # point is inside at least one polygon
            if containing_polygon_index.size > 1:  # point is inside multiple polygons
                # This can only happen if polygons overlap.
                # There is no "correct" polygon to choose, so pick the first one
                logger.info("Point is inside multiple polygons, picking the first one")
                containing_polygon_index = containing_polygon_index[0]

            # point is inside 1 polygon
            requested_timezone = self.gdf.iloc[containing_polygon_index]["TZID"].item()

        else:  # point is inside < 0 polygons, this should be impossible
            logger.error(f"Point is inside < 0 polygons. size: {containing_polygon_index.size}")
            return {"error": "Impossible Geometry"}, 500

        # "The endpoint shall return a meaningful timezones for uninhabited zones."
        if requested_timezone == "uninhabited":
            requested_timezone = self._calculate_utc_approximation(lon)

        return {"timezone": requested_timezone}

    @staticmethod
    def _calculate_utc_approximation(lon: float) -> str:
        # step 1: calculate offset
        if lon > 172.5:
            offset = 12
        elif lon < -172.5:
            offset = -12
        else:
            offset = int(lon / 15)

        # step 2: create UTC string
        if offset > 0:
            utc_string = f"UTC+{offset}"
        elif offset < 0:
            utc_string = f"UTC{offset}"
        else:  # offset == 0
            utc_string = "UTC"
        return utc_string


time_service = TimeService()


@app.route("/timezones")
def timezones():
    logger.info(f"received args: {request.args}")

    if len(request.args) == 2 and "lat" in request.args.keys() and "lon" in request.args.keys():
        lat = request.args.get("lat")
        lon = request.args.get("lon")

        try:
            sanitized_lat = float(lat)
            sanitized_lon = float(lon)
            if sanitized_lon > 180 or sanitized_lon < -180 or sanitized_lat > 90 or sanitized_lat < -90:
                raise ValueError

        except ValueError:
            logger.error(f"received invalid lat or lon. lat: {lat} lon: {lon}")
            return {"error": "Please provide valid latitude and longitude."}, 400

        return time_service.timezone_at_coordinate(sanitized_lat, sanitized_lon)

    elif len(request.args) == 0:
        return time_service.timezones_list()

    else:
        return {"error": "Please either provide no arguments, or latitude and longitude."}, 400


if __name__ == "__main__":
    app.run()
