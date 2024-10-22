# some untility functions for defining segments

__all__ = [
    "get_sondes_l1",
    "get_overpass_info",
    "plot_overpass",
    "to_dt",
    "get_takeoff_landing",
    "segment_hash",
    "event_hash",
    "parse_segment",
    "to_yaml",
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
    from orcestra.flightplan import geod
    _, _, dist = geod.inv(ds.sel(time=seg).lon.values,
                          ds.sel(time=seg).lat.values,
                          np.full_like(ds.sel(time=seg).lon.values, target_lon),
                          np.full_like(ds.sel(time=seg).lon.values, target_lat),
                         )
    i = np.argmin(dist)
    return dist[i], ds.time.sel(time=seg).isel(time=i).values
    
def plot_overpass(seg, ds, target_lat, target_lon):
    import matplotlib.pyplot as plt
    d, t = get_overpass_info(seg, ds, target_lat, target_lon)
    plt.plot(ds.lon.sel(time=seg), ds.lat.sel(time=seg))
    plt.scatter(ds.lon.sel(time=seg.start), ds.lat.sel(time=seg.start))
    plt.scatter(target_lon, target_lat, c="C1")    
    plt.plot([ds.lon.sel(time=t), target_lon], [ds.lat.sel(time=t), target_lat], color="C1")
    print(f"{d:.0f}m @ {t}")
    plt.show()


def fit_circle(lat, lon):
    """
    Given a sequence of WGS84-Coordinates (lat and lon) on points along a circular path,
    this function determines the center and radius of that circle.
    """
    from orcestra.flightplan import geod
    from scipy.optimize import minimize
    import numpy as np

    lat = np.asarray(lat)
    lon = np.asarray(lon)

    clat = np.mean(lat)
    clon = np.mean(lon)

    def cost(x):
        clat, clon = x
        _, _, d = geod.inv(lon, lat, np.full_like(lon, clon), np.full_like(lat, clat))
        return np.std(d)

    res = minimize(cost, [clat, clon], method="Nelder-Mead")
    clat, clon = res.x
    _, _, d = geod.inv(lon, lat, np.full_like(lon, clon), np.full_like(lat, clat))
    return float(clat), float(clon), float(np.mean(d))

def ransac_fit_circle(lat, lon, distance_range=1e3, n=100):
    """
    Given a sequence of WGS84-Coordinates (lat and lon) on points along a circular path,
    this function determines the center and radius of that circle.
    """
    import numpy as np
    from orcestra.flightplan import geod

    lat = np.asarray(lat)
    lon = np.asarray(lon)

    samples = []
    for _ in range(n):
        idxs = np.random.choice(len(lat), 3, replace=False)

        clat, clon, radius = fit_circle(lat[idxs], lon[idxs])

        _, _, d = geod.inv(lon, lat, np.full_like(lon, clon), np.full_like(lat, clat))
        n_in = np.sum(np.abs(radius - d) <= distance_range)

        samples.append((n_in, clat, clon, radius))

    n_in_good, clat, clon, radius = sorted(samples)[-1]
    _, _, d = geod.inv(lon, lat, np.full_like(lon, clon), np.full_like(lat, clat))
    good = np.abs(radius - d) <= distance_range
    return fit_circle(lat[good], lon[good])


def _attach_circle_fit(segment, ds):
    if "circle" not in segment["kinds"]:
        return segment

    cdata = ds.sel(time=segment["slice"])
    clat, clon, radius = ransac_fit_circle(cdata.lat.values, cdata.lon.values)
    return {
        **segment,
        "clat": clat,
        "clon": clon,
        "radius": radius,
    }


def attach_circle_fit(segments, ds):
    return [_attach_circle_fit(s, ds) for s in segments]


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

def event_hash(event):
    import hashlib
    return hashlib.sha256(f"{event["time"]}".encode("ascii")).hexdigest()[-4:]

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
            seg["remarks"] = segment[3]
    elif isinstance(segment, dict):
        return segment
    else:
        seg = {"slice": segment}
    return seg

def to_yaml(platform, flight_id, ds, segments, events):
    segments = attach_circle_fit([parse_segment(s) for s in segments], ds)
    takeoff, landing, _ = get_takeoff_landing(flight_id, ds)
    return {"mission": "ORCESTRA",
            "platform": platform,
            "flight_id": flight_id,
            "takeoff": to_dt(takeoff),
            "landing": to_dt(landing),
            "events": [{"event_id": f"{flight_id}_{event_hash(e)}",
                        "name": None,
                        "time": to_dt(e["time"]),
                        "kinds": [],
                        "remarks": [],
                        **{k: v for k, v in e.items() if k not in ["event_id", "time"]},
                        } for e in events],
            "segments": [{"segment_id": f"{flight_id}_{segment_hash(s["slice"])}",
                          "name": None,
                          "start": to_dt(s["slice"].start),
                          "end": to_dt(s["slice"].stop),
                          "kinds": [],
                          "remarks": [],
                          **{k: v for k, v in s.items() if k not in ["segment_id", "start", "end", "slice"]},
                         } for s in segments]
           }