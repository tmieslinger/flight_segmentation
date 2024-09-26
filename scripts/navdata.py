# the individual loaders should import dependencies within the function
# that way it is possible to run the code for one platform if dependencies
# for another platform are not met

_catalog_cache = {}

def get_navdata_HALO(flight):
    """
    :param flight: flight id
    """
    import xarray as xr
    from intake import open_catalog
    import orcestra.postprocess.level0

    root = "ipns://latest.orcestra-campaign.org"
    #ds = xr.open_dataset(f"{root}/products/HALO/position_attitude/{flight}.zarr", engine="zarr")#.pipe(orcestra.postprocess.level0.bahamas)
    ds = xr.open_dataset(f"{root}/products/HALO/position_attitude/{flight}.zarr", engine="zarr")

    return xr.Dataset({
        "time": ds.time,
        "lat": ds.lat,
        "lon": ds.lon,
        "alt": ds.alt,
        "roll": ds["roll"],
        "pitch": ds.pitch,
        "heading": ds.heading,
    })

NAVDATA_GETTERS = {
    "HALO": get_navdata_HALO,
}

def get_navdata(platform, flight):
    """
    :param platform: platform id
    :param flight: flight id
    """
    return NAVDATA_GETTERS[platform](flight)

__all__ = ["get_navdata"]
