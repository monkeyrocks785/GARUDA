"""Configuration for the Raster Processing Engine."""


# Supported raster formats
SUPPORTED_FORMATS = {
    ".tif": "GeoTIFF",
    ".tiff": "GeoTIFF",
    ".geotiff": "GeoTIFF",
    ".jp2": "JPEG2000",
    ".j2k": "JPEG2000",
    ".png": "PNG",
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".dt0": "DTED",
    ".dt1": "DTED",
    ".dt2": "DTED",
    ".dem": "DEM",
    ".img": "ERDAS IMAGINE",
}

RASTER_EXTENSIONS = set(SUPPORTED_FORMATS.keys())

# Resampling methods
RESAMPLING_METHODS = {
    "nearest": "nearest",
    "bilinear": "bilinear",
    "cubic": "cubic",
    "cubic_spline": "cubic_spline",
    "lanczos": "lanczos",
    "average": "average",
    "mode": "mode",
    "max": "max",
    "min": "min",
    "median": "median",
    "sum": "sum",
}

# Common CRS definitions
CRS_DEFINITIONS = {
    "EPSG:4326": "WGS 84",
    "EPSG:3857": "Web Mercator",
    "EPSG:32601": "UTM Zone 1N",
    "EPSG:32602": "UTM Zone 2N",
    "EPSG:32603": "UTM Zone 3N",
    "EPSG:32604": "UTM Zone 4N",
    "EPSG:32605": "UTM Zone 5N",
    "EPSG:32606": "UTM Zone 6N",
    "EPSG:32607": "UTM Zone 7N",
    "EPSG:32608": "UTM Zone 8N",
    "EPSG:32609": "UTM Zone 9N",
    "EPSG:32610": "UTM Zone 10N",
    "EPSG:32611": "UTM Zone 11N",
    "EPSG:32612": "UTM Zone 12N",
    "EPSG:32613": "UTM Zone 13N",
    "EPSG:32614": "UTM Zone 14N",
    "EPSG:32615": "UTM Zone 15N",
    "EPSG:32616": "UTM Zone 16N",
    "EPSG:32617": "UTM Zone 17N",
    "EPSG:32618": "UTM Zone 18N",
    "EPSG:32619": "UTM Zone 19N",
    "EPSG:32620": "UTM Zone 20N",
    "EPSG:32621": "UTM Zone 21N",
    "EPSG:32622": "UTM Zone 22N",
    "EPSG:32623": "UTM Zone 23N",
    "EPSG:32624": "UTM Zone 24N",
    "EPSG:32625": "UTM Zone 25N",
    "EPSG:32626": "UTM Zone 26N",
    "EPSG:32627": "UTM Zone 27N",
    "EPSG:32628": "UTM Zone 28N",
    "EPSG:32629": "UTM Zone 29N",
    "EPSG:32630": "UTM Zone 30N",
    "EPSG:32631": "UTM Zone 31N",
    "EPSG:32632": "UTM Zone 32N",
    "EPSG:32633": "UTM Zone 33N",
    "EPSG:32634": "UTM Zone 34N",
    "EPSG:32635": "UTM Zone 35N",
    "EPSG:32636": "UTM Zone 36N",
    "EPSG:32637": "UTM Zone 37N",
    "EPSG:32638": "UTM Zone 38N",
    "EPSG:32639": "UTM Zone 39N",
    "EPSG:32640": "UTM Zone 40N",
    "EPSG:32641": "UTM Zone 41N",
    "EPSG:32642": "UTM Zone 42N",
    "EPSG:32643": "UTM Zone 43N",
    "EPSG:32644": "UTM Zone 44N",
    "EPSG:32645": "UTM Zone 45N",
    "EPSG:32646": "UTM Zone 46N",
    "EPSG:32647": "UTM Zone 47N",
    "EPSG:32648": "UTM Zone 48N",
    "EPSG:32649": "UTM Zone 49N",
    "EPSG:32650": "UTM Zone 50N",
    "EPSG:32651": "UTM Zone 51N",
    "EPSG:32652": "UTM Zone 52N",
    "EPSG:32653": "UTM Zone 53N",
    "EPSG:32654": "UTM Zone 54N",
    "EPSG:32655": "UTM Zone 55N",
    "EPSG:32656": "UTM Zone 56N",
    "EPSG:32657": "UTM Zone 57N",
    "EPSG:32658": "UTM Zone 58N",
    "EPSG:32659": "UTM Zone 59N",
    "EPSG:32660": "UTM Zone 60N",
}

# Default overview levels
DEFAULT_OVERVIEW_LEVELS = [2, 4, 8, 16]

# Tile sizes
DEFAULT_TILE_SIZE = 256

# Thumbnail dimensions
THUMBNAIL_WIDTH = 256
THUMBNAIL_HEIGHT = 256

# Storage paths (relative to project storage)
RASTER_DIR = "rasters"
THUMBNAILS_DIR = "thumbnails"
DERIVED_DIR = "derived"
