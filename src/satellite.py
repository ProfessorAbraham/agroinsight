# satellite.py
import ee

def fetch_ndvi_for_kebele(kebele_name, center_lon, center_lat, start_date, end_date):
    try:
        point = ee.Geometry.Point([center_lon, center_lat])
        collection = (ee.ImageCollection('COPERNICUS/S2')
                      .filterDate(start_date, end_date)
                      .filterBounds(point)
                      .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                      .sort('CLOUDY_PIXEL_PERCENTAGE')
                      .first())
        if collection is None:
            print(f"No Sentinel-2 images found for {kebele_name} between {start_date} and {end_date}.")
            return None
        
        ndvi = collection.normalizedDifference(['B8', 'B4']).rename('NDVI')
        ndvi_value = ndvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=point,
            scale=10
        ).get('NDVI').getInfo()
        
        print(f"{kebele_name} NDVI from {start_date} to {end_date}: {ndvi_value}")
        return ndvi_value
    except Exception as e:
        print(f"Error fetching NDVI for {kebele_name}: {e}")
        return None
