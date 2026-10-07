import os
import zipfile
import tempfile
from pathlib import Path
import geopandas as gpd
from fastapi import HTTPException, status

class GeospatialService:
    @staticmethod
    def _validate_and_extract_shapefile_zip(zip_path: str) -> str:
        """
        Safely extracts a Shapefile ZIP archive with Zip Slip protection
        and validates mandatory companion files (.shp, .shx, .dbf).
        """
        temp_dir = tempfile.mkdtemp()
        target_path = Path(temp_dir).resolve()

        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                namelist = zf.namelist()
                
                # Zip Slip / Path Traversal Protection
                for member in namelist:
                    member_path = (target_path / member).resolve()
                    if target_path not in member_path.parents and member_path != target_path:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Security violation: Path traversal detected in ZIP archive member: {member}"
                        )
                
                # Validate mandatory companion files (.shp, .shx, .dbf)
                lower_namelist = [m.lower() for m in namelist]
                has_shp = any(m.endswith('.shp') for m in lower_namelist)
                has_shx = any(m.endswith('.shx') for m in lower_namelist)
                has_dbf = any(m.endswith('.dbf') for m in lower_namelist)

                missing = []
                if not has_shp: missing.append('.shp')
                if not has_shx: missing.append('.shx')
                if not has_dbf: missing.append('.dbf')

                if missing:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid Shapefile ZIP: missing mandatory companion file(s): {', '.join(missing)}"
                    )

                zf.extractall(target_path)
            
            return temp_dir
        except HTTPException as he:
            raise he
        except zipfile.BadZipFile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is not a valid or is a corrupted ZIP archive."
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to process Shapefile ZIP archive: {str(e)}"
            )

    @staticmethod
    def load_geospatial_file(file_type: str, file_path: str, shp_path: str | None = None) -> gpd.GeoDataFrame:
        try:
            if file_type == "kml":
                gdf = gpd.read_file(file_path, engine="pyogrio", driver="KML")
            elif file_type == "shapefile_zip":
                target_zip = shp_path if shp_path and zipfile.is_zipfile(shp_path) else file_path
                extract_dir = GeospatialService._validate_and_extract_shapefile_zip(target_zip)
                
                shp_files = list(Path(extract_dir).rglob("*.shp"))
                if not shp_files:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No .shp file found within the extracted Shapefile archive."
                    )
                
                gdf = gpd.read_file(str(shp_files[0]), engine="pyogrio")
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported file type for parsing: {file_type}"
                )

            if gdf.empty:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The uploaded geospatial file contains no valid features/geometries."
                )

            if gdf.crs is None:
                gdf.set_crs("EPSG:4326", inplace=True)

            return gdf

        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to parse geospatial file: {str(e)}"
            )