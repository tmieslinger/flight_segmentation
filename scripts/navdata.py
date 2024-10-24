# the individual loaders should import dependencies within the function
# that way it is possible to run the code for one platform if dependencies
# for another platform are not met

_catalog_cache = {}

def get_navdata_HALO(flight, hres=False):
    """
    :param flight: flight id
    """
    import xarray as xr

    #root = "ipns://latest.orcestra-campaign.org/products/HALO/position_attitude"
    root = "ipfs://QmP1ragFLB3jbjBj9tU3piitkADPqBUjqgydhcFjFGXrii"
    if hres:
        ds = xr.open_dataset(f"{root}/{flight}.zarr", engine="zarr").reset_coords()
    else:
        ds = xr.open_dataset(f"{root}/{flight}.zarr", engine="zarr").reset_coords().resample(time="1s").mean()
    return ds

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
