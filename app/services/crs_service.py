import math

class CRSService:
    @staticmethod
    def get_local_utm_epsg(gdf) -> str:
        """
        Calculates the appropriate local UTM EPSG code based on the geographic centroid 
        of the GeoDataFrame to ensure metric accuracy.
        """
        # Ensure data is in EPSG:4326 to compute centroid longitude/latitude reliably
        if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
            gdf_latlon = gdf.to_crs(epsg=4326)
        else:
            gdf_latlon = gdf

        # Calculate bounding box / centroid
        bounds = gdf_latlon.total_bounds  # [xmin, ymin, xmax, ymax]
        center_lon = (bounds[0] + bounds[2]) / 2.0
        center_lat = (bounds[1] + bounds[3]) / 2.0

        # Determine UTM zone number (1 to 60)
        utm_zone = int(math.floor((center_lon + 180) / 6) + 1)
        utm_zone = max(1, min(utm_zone, 60))

        # Determine Northern or Southern hemisphere
        if center_lat >= 0:
            epsg_code = 32600 + utm_zone  # UTM North
        else:
            epsg_code = 32700 + utm_zone  # UTM South

        return f"EPSG:{epsg_code}"