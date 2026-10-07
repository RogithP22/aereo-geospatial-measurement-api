import geopandas as gpd

class MeasurementService:
    @staticmethod
    def process_features(gdf: gpd.GeoDataFrame) -> list:
        """Alias for calculate_measurements to support existing caller expectations."""
        return MeasurementService.calculate_measurements(gdf)

    @staticmethod
    def calculate_measurements(gdf: gpd.GeoDataFrame) -> list:
        measurements = []
        for idx, row in gdf.iterrows():
            geom = row.geometry
            if geom is None or geom.is_empty:
                continue
            
            geom_type = geom.geom_type
            props = row.drop('geometry', errors='ignore').to_dict()
            props = {str(k): (v if v is not None else "") for k, v in props.items()}

            if geom_type in ["Polygon", "MultiPolygon"]:
                area = geom.area
                measurements.append({
                    "feature_index": int(idx),
                    "geometry_type": geom_type,
                    "properties": props,
                    "measurement_type": "area",
                    "measurement_value": float(area),
                    "measurement_unit": "square_meters"
                })
            elif geom_type in ["LineString", "MultiLineString"]:
                length = geom.length
                measurements.append({
                    "feature_index": int(idx),
                    "geometry_type": geom_type,
                    "properties": props,
                    "measurement_type": "length",
                    "measurement_value": float(length),
                    "measurement_unit": "meters"
                })
            elif geom_type in ["Point", "MultiPoint"]:
                continue
            else:
                continue
        return measurements