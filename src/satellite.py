import datetime
import ee

def mask_s2_clouds(image):
    """
    Masks clouds using the Sentinel-2 QA60 band.
    QA60 band bits:
    - Bit 10 = opaque clouds
    - Bit 11 = cirrus clouds
    """
    qa = image.select('QA60')
    # Create bit masks for clouds
    cloud_bit_mask = 1 << 10
    cirrus_bit_mask = 1 << 11
    
    # Both bits should be zero for clear conditions
    mask = qa.bitwiseAnd(cloud_bit_mask).eq(0).And(qa.bitwiseAnd(cirrus_bit_mask).eq(0))
    
    return image.updateMask(mask).copyProperties(image, ["system:time_start"])

def get_sentinel_image(lat, lon, start_date, end_date, fallback_days=30):
    point = ee.Geometry.Point(lon, lat)
    
    def fetch_images(s_date, e_date):
        collection = (
            ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterBounds(point)
            .filterDate(s_date, e_date)
            .map(mask_s2_clouds)  # Apply cloud mask here
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 50))  # You can relax threshold now
            .sort('system:time_start', False)
        )
        return collection
    
    collection = fetch_images(start_date, end_date)
    size = collection.size().getInfo()
    
    if size > 0:
        print(f"✅ Found {size} Sentinel-2 image(s) between {start_date} and {end_date}")
        return collection.first()
    
    fallback_start = (datetime.datetime.strptime(start_date, "%Y-%m-%d") - datetime.timedelta(days=fallback_days)).strftime("%Y-%m-%d")
    print(f"⚠ No Sentinel-2 images found. Trying fallback range {fallback_start} to {end_date}...")
    
    fallback_collection = fetch_images(fallback_start, end_date)
    fallback_size = fallback_collection.size().getInfo()
    
    if fallback_size > 0:
        print(f"📅 Using fallback Sentinel-2 image ({fallback_size} found).")
        return fallback_collection.first()
    
    print("❌ No Sentinel-2 images found, even with fallback. Trying Landsat 8/9...")
    landsat_collection = (
        ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
        .filterBounds(point)
        .filterDate(fallback_start, end_date)
        .sort('system:time_start', False)
    )
    
    landsat_size = landsat_collection.size().getInfo()
    if landsat_size > 0:
        print(f"🌍 Using Landsat imagery ({landsat_size} found).")
        return landsat_collection.first()
    
    print("🚫 No suitable satellite imagery found.")
    return None

def fetch_ndvi_for_kebele(kebele_name, center_lon, center_lat, start_date, end_date):
    try:
        image = get_sentinel_image(center_lat, center_lon, start_date, end_date)
        if not image:
            return None
        
        ndvi_image = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
        point = ee.Geometry.Point([center_lon, center_lat])
        ndvi_value = ndvi_image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=point,
            scale=10
        ).get('NDVI').getInfo()
        
        print(f"{kebele_name} NDVI from {start_date} to {end_date}: {ndvi_value}")
        return ndvi_value
    except Exception as e:
        print(f"Error fetching NDVI for {kebele_name}: {e}")
        return None
