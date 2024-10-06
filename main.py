import matplotlib.pyplot as plt
import geopandas as gpd
import numpy as np
from shapely import Point

gdf = gpd.read_file("world/tz_world.shp")
# gdf["convex_hull"] = gdf.convex_hull
# gdf.plot()

# ax = gdf["convex_hull"].plot(alpha=0.5)
# passing the first plot and setting linewidth to 0.5

# # vienna
# lat = 48.2081
# lon = 16.3713

# null island
lat = 0
lon = 0

# print([a for a in gdf.contains(point) if a is True])

point = Point(lon, lat)

containing_polygon_index = np.where(gdf.contains(point))[0]
print(f"containing_polygon_index {containing_polygon_index}")
print(f"gdf.iloc[containing_polygon_index] {gdf.iloc[containing_polygon_index]}")

requested_timezone = ""
final_index = 0

gdf.set_crs('EPSG:4326', inplace=True)
gdf = gdf.to_crs("epsg:32633")

# The endpoint shall return a meaningful timezones for uninhabited zones.
if containing_polygon_index.size == 0: # point is inside no polygons
    # meaningful options: easiest: the closest polygon
    #                     more elaborate: the poly that is closes vertically

    final_index = gdf.distance(point).idxmin()

elif containing_polygon_index.size > 1: # point is inside multiple polygons
    print("ERROR! TBD") #TODO
    pass
else: # point is inside 1 polygon
    final_index = containing_polygon_index

print(f"final_index {final_index}")

print(gdf.iloc[final_index]["TZID"])

# gdf.iloc[final_index].plot()

# target_poly = gdf.iloc[gdf.sindex.query(point, predicate="contains")]
# target_poly.plot()

# gdf.iloc[gdf.contains(point)[gdf.contains(point)].index].plot()

# gdf.cx[:, :50].plot(legend=True)
# gdf.plot(ax=ax, color="white", linewidth=0.5)


plt.show()




# idea: step 1. iterate the convex hulls and select the ones where the point is inside
#               -> quickly reduces search space, ought to have low runtime
#       step 2. iterate the selected polygons and exactly calc if inside
#               -> prob. more expensive, high runtime