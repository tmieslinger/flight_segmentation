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

    bahamas_cids = {
        "HALO-20240809b": "QmahYozz3StbbeJxXn7zPycdZYz6mLVNYszEU28XqxSMGc",
        "HALO-20240811a": "QmbmtXr3pSGexuteUAcasgAzSHHpfKNXk9r5JfZXKqa2d5",
        "HALO-20240813a": "QmcFHpX6zNcG7kFjUNff8BEUkoYomwpnTJUAjhXq9KACtg",
        "HALO-20240816a": "QmTCph5sHoq9pcXLHyHix2qAVmSCBjvLmbPCfx2QgVs13a",
        "HALO-20240818a": "QmSjsEFDywceEDLxs2zHfcj1GuRATDosgw9fwsFT5bAX8x",
        "HALO-20240821a": "QmXnuuipS3xFE3mX7ZGRti55NapwSRVsBMPDfvnTMkSLoj",
        "HALO-20240822a": "QmethFGpJ5jg8ASnS3kcQPDN6bct4g85DBh2HWQQqj7DXb",
    }

    ds = xr.open_dataset(f"ipfs://{bahamas_cids[flight]}", engine="zarr").pipe(orcestra.postprocess.level0.bahamas)
    print(ds)
    return xr.Dataset({
        "time": ds.time,
        "lat": ds.IRS_LAT,
        "lon": ds.IRS_LON,
        "alt": ds.IRS_ALT,
        "roll": ds.IRS_PHI,
        "pitch": ds.IRS_THE,
        "heading": ds.IRS_HDG,
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
