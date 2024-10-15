# some untility functions for defining segments

__all__ = [
    "get_sondes_l1",
    "get_overpass_info",
    "plot_overpass",
    "to_dt",
    "segment_hash",
    "parse_segment",
    "seg2yaml",
]

def get_sondes_l1(flight_id):
    import fsspec
    import xarray as xr
    import numpy as np
    root = "ipns://latest.orcestra-campaign.org/products/HALO/dropsondes/Level_1"
    day_folder = root + "/" + flight_id
    fs = fsspec.filesystem(day_folder.split(":")[0])
    filenames = fs.ls(day_folder, detail=False)
    datasets = [xr.open_dataset(fsspec.open_local("simplecache::ipns://" + filename), engine="netcdf4")
                for filename in filenames]
    return np.array([d["launch_time"].values for d in datasets])

def get_overpass_info(seg, ds, target_lat, target_lon):
    import numpy as np
    _, _, dist = geod.inv(ds.sel(time=seg).lon.values,
                          ds.sel(time=seg).lat.values,
                          np.full_like(ds.sel(time=seg).lon.values, target_lon),
                          np.full_like(ds.sel(time=seg).lon.values, target_lat),
                         )
    i = np.argmin(dist)
    return dist[i], ds.time.sel(time=seg).isel(time=i).values
    
def plot_overpass(seg, ds, target_lat, target_lon):
    d, t = get_overpass_info(seg, ds, target_lat, target_lon)
    plt.plot(ds.lon.sel(time=seg), ds.lat.sel(time=seg))
    plt.scatter(ds.lon.sel(time=seg.start), ds.lat.sel(time=seg.start))
    plt.scatter(target_lon, target_lat, c="C1")    
    plt.plot([ds.lon.sel(time=t), target_lon], [ds.lat.sel(time=t), target_lat], color="C1")
    print(f"{d:.0f}m @ {t}")
    plt.show()

def to_dt(dt64):
    import pandas as pd
    return pd.Timestamp(dt64).to_pydatetime(warn=False)

def get_takeoff_landing(flight_id, ds):
    """
    Detect take-off and landing for the airport on Sal and Barbados
    which are located at about 89m and 8m above WGS84 respectively.
    """
    import numpy as np
    if ds.time[0].values > np.datetime64("2024-09-07T00:00:00"):
        airport_wgs84 = 9
    else:
        airport_wgs84 = 90
    takeoff = ds["time"].where(ds.alt > airport_wgs84, drop=True)[0].values
    landing = ds["time"].where(ds.alt > airport_wgs84, drop=True)[-1].values
    duration = (landing - takeoff).astype("timedelta64[m]").astype(int)
    return takeoff, landing, duration

def segment_hash(segment):
    import hashlib
    return hashlib.sha256(f"{segment.start}+{segment.stop}".encode("ascii")).hexdigest()[-4:]

def parse_segment(segment):
    if isinstance(segment, tuple):
        seg = {
            "slice": segment[0],
        }
        if len(segment) >= 2:
            seg["kinds"] = segment[1]
        if len(segment) >= 3:
            seg["name"] = segment[2]
        if len(segment) >= 4:
            seg["irregularities"] = segment[3]
    elif isinstance(segment, dict):
        return segment
    else:
        seg = {"slice": segment}
    return seg

def seg2yaml(flight_id, ds, segments):
    segments = [parse_segment(s) for s in segments]
    takeoff, landing, _ = get_takeoff_landing(flight_id, ds)
    return {"flight_id": flight_id,
            "takeoff": to_dt(takeoff),
            "landing": to_dt(landing),
            "segments": [{"kinds": s.get("kinds", []),
                          "name": s.get("name", None),
                          "segment_id": f"{flight_id}_{segment_hash(s["slice"])}",
                          "start": to_dt(s["slice"].start),
                          "end": to_dt(s["slice"].stop),
                          "irregularities": s.get("irregularities", []),
                          "comments": s.get("comments", []),
                         } for s in segments]
           }