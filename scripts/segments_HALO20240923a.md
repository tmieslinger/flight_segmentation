---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.14.5
  kernelspec:
    display_name: flight_segment
    language: python
    name: flight_segment
---

# Flight segmentation HALO-20240923a

```python
import fsspec
import xarray as xr
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import hvplot.xarray

from navdata import get_navdata_HALO
from orcestra import bco
from orcestra.flightplan import geod
```

```python
flight_id = "HALO-20240923a"
```

## Get HALO position and attitude

```python
ds = get_navdata_HALO(flight_id)
```

## Get dropsonde data

```python
def get_sondes_l1(flight_id):
    root = "ipns://latest.orcestra-campaign.org/products/HALO/dropsondes/Level_1"
    day_folder = root + "/" + flight_id
    fs = fsspec.filesystem(day_folder.split(":")[0])
    filenames = fs.ls(day_folder, detail=False)
    datasets = [xr.open_dataset(fsspec.open_local("simplecache::ipns://" + filename), engine="netcdf4")
                for filename in filenames]
    return np.array([d["launch_time"].values for d in datasets])
```

Reduce navigation dataset to dropsonde times

```python
drops = get_sondes_l1(flight_id)
ds_drops = ds.sel(time=drops, method="nearest")
```

## Interactive plots

```python
ds["alt"].hvplot()
```

```python
ds["roll"].hvplot()
```

### Defining takeoff and landing
Find the maximum altitude above WGS84 related to BCO airport:

```python
max(ds["alt"].sel(time=slice(None,"2024-09-23T11:13:20")).max().values,
    ds["alt"].sel(time=slice("2024-09-23T20:06:30",None)).max().values)
```

Let's define everything above 10m altitude to belong to the flight time

```python
if ds.time[0].values > np.datetime64("2024-09-07T00:00:00"):
    airport_wgs84 = 9
else:
    airport_wgs84 = 90
```

```python
takeoff = ds["time"].where(ds.alt > airport_wgs84, drop=True)[0].values
landing = ds["time"].where(ds.alt > airport_wgs84, drop=True)[-1].values
duration = (landing - takeoff).astype("timedelta64[m]").astype(int)
print("take-off: ", takeoff)
print("landing: ", landing)
print(f"flight duration: {int(duration / 60)}:{int(duration % 60)}")
```

```python
fotos = [
    "2023-09-23T11:23:58",
    "2023-09-23T11:34:10",
    "2023-09-23T12:00:10",
    ]
```

### Plot flight track and dropsondes

```python
foto = True

plt.plot(ds.lon.sel(time=slice(takeoff, landing)), ds.lat.sel(time=slice(takeoff, landing)))
plt.scatter(ds_drops.lon, ds_drops.lat, s=10, c="k")

if foto:
    for i in fotos:
        da_foto = ds.sel(time=i, method="nearest")
        plt.scatter(da_foto.lon, da_foto.lat, color='C1', marker='o', s = 10, zorder=100)
```

## Segments

defined as a tuple object of time slice, segment kind, name, and irregularities

**in case of irregularities within a circle, 1 sec before the first and after the last sonde are chosen as start and end times**

```python
# Meteor coordinates
latm = 13.162109
lonm = -59.413086

# segment at roughly 930m altitude, but with two different roll angles -> maybe name it just "leg" and specify irreg?
seg1 = (slice("2024-09-23T11:15:02", "2024-09-23T11:19:28"),
        ["leg"],
        "heading towards Meteor",
        ["segment at roughly 930m altitude, but with two different roll angles"],
       )

meteor1 = (slice("2024-09-23T11:18:36", "2024-09-23T11:18:36"),
          ["meteor_overpass"],
          "Meteor overpass 1",
          ["386m distance"])

# climbing circle (with Meteor overpass)
seg2 = (slice("2024-09-23T11:21:42", "2024-09-23T11:54:32"),
        ["ascent"],
        "climbing circle",
        ["35nm circle to climb up to FL410"],
       )
# Meteor measurement circle (with Meteor overpass) on FL410
seg3 = (slice("2024-09-23T11:54:32", "2024-09-23T12:26:35"),
        ["circle", "c_atr"],
        "Meteor circle",
        ["roll angle deviations at start and end until 11:56:20 and at the end starting at 11:25:54 due to deep convection"],
       )

# heading to c_mid
seg4a = (slice("2024-09-23T12:31:33", "2024-09-23T12:40:20"),
        ["straight_leg"],
        "leg towards c_mid",
       )
seg4b = (slice("2024-09-23T12:40:20", "2024-09-23T12:44:10"),
        ["straight_leg", "ascent"],
        "climb to FL430",
       )
seg4c = (slice("2024-09-23T12:44:10", "2024-09-23T13:08:51"),
        ["straight_leg"],
        "leg towards c_mid",
       )

seg6 = (slice("2024-09-23T13:12:20", "2024-09-23T14:07:30"),
        ["circle", "c_mid"],
        "circle mid",
        ["deviation in roll angle between 13:21:57 - 13:31:10 due to deep convection"],
       )

seg7 = (slice("2024-09-23T14:11:01", "2024-09-23T14:26:28"),
        ["straight_leg"],
        "leg crossing circle c_mid",
       )
seg8 = (slice("2024-09-23T14:26:28", "2024-09-23T14:31:32"),
         ["straight_leg", "ascent"],
         "climb towards FL450"
       )
# fl change 14:26:29 - 14:31:29 and again 14:35:43 - 14:37:34
# straight_leg and circle start still with FL change

seg9 = (slice("2024-09-23T14:37:34", "2024-09-23T15:32:20"),
        ["circle", "c_ec"],
        "circle on EC track",
        ["late start due to FL change, on circle roughly since 14:32:30"]
       )

seg10 = (slice("2024-09-23T15:36:28", "2024-09-23T15:57:14"),
         ["straight_leg"],
         "leg crossing c_ec",
         ["peak in rool to -5.65deg between 15:42:23-15:42:36"]
        )

seg11 = (slice("2024-09-23T16:00:47", "2024-09-23T16:55:23"),
         ["circle", "c_south"],
         "circle south",
         ["deep convection in southern half at 16:15:30 - 16:18:30 and again in the north starting 16:47:06 and until the segment ends"]
        )

seg12 = (slice("2024-09-23T16:57:01", "2024-09-23T17:12:15"),
         ["straight_leg"],
         "leg towards EC south",
        )

seg13 = (slice("2024-09-23T17:15:25", "2024-09-23T17:23:46"),
         ["straight_leg", "ec_track", "ec_track_northward"],
         "EC track northward",
         ["due to very deep convection in the south and north the EC track is very short"]
        )

# heavy deviations to navigate through deep concevtion towards next circle
#seg14 = (slice("2024-09-23T17:23:47", "2024-09-23T17:54:38"),)

seg14 = (slice("2024-09-23T17:54:38", "2024-09-23T17:57:27"),
        ["straight_leg"],
        "leg 1 towards circle west",
        )
seg15 = (slice("2024-09-23T17:57:27", "2024-09-23T18:03:16"),
        ["straight_leg", "ascent"],
        "climb to FL470")
seg16 = (slice("2024-09-23T18:03:17", "2024-09-23T18:12:36"),
        ["straight_leg"],
        "leg 2 towards circle west",
        )

seg17 = (slice("2024-09-23T18:15:51", "2024-09-23T19:10:36"),
        ["circle", "c_west"],
        "circle west",
        )

seg18 = (slice("2024-09-23T19:12:57", "2024-09-23T19:16:45"),
        ["straight_leg"],
        )
seg19 = (slice("2024-09-23T19:16:59", "2024-09-23T19:18:09"),
        ["radar_calibration_wiggle"],
        "radar calibration wiggle within c_west",
         ["pattern within circle west with 12 sondes"],
        )

# straight leg crossing c_west
seg20 = (slice("2024-09-23T19:21:24", "2024-09-23T19:26:39"),
        ["straight_leg"],
        "straight leg crossing c_west")

# FL change down to ~2km consisting of 3 straight legs
#seg21 = (slice("2024-09-23T19:26:40", "2024-09-23T19:46:55"),)
# FL change leg 1
seg21a = (slice("2024-09-23T19:26:40", "2024-09-23T19:32:04"),
         ["straight_leg", "descent"],
          "straight leg on descent towards Meteor",
         )
# FL change leg 2
seg21b = (slice("2024-09-23T19:34:08", "2024-09-23T19:41:36"),
          ["straight_leg", "descent"],
          "straight leg on descent towards Meteor",
         )
# FL change leg 3
seg21c = (slice("2024-09-23T19:42:37", "2024-09-23T19:46:56"),
          ["straight_leg", "descent"],
          "straight leg on descent towards Meteor",
         )

# straight leg overpassing Meteor at 2km height
seg22 = (slice("2024-09-23T19:46:56", "2024-09-23T19:53:45"),
         ["straight_leg"],
         "straight leg overpassing Meteor at 2km height"
        )
# again FL change
#seg23 = (slice("2024-09-23T19:53:44", "2024-09-23T19:56:41"),)

# straight_leg passing by BCO at ~900m height at 19:56:57
seg24 = (slice("2024-09-23T19:56:50", "2024-09-23T19:58:11"),
        ["straight_leg"],
         "straight leg overpassing BCO at 900m height"
        )

# landing
#seg25 = (slice("2024-09-23T19:58:12", "2024-09-23T20:09:49"),)


segments = [meteor1, seg2, seg3, seg4a, seg4b, seg4c, seg6, seg7, seg8, seg9, seg10,
            seg11, seg12, seg13, seg14, seg15, seg16, seg17, seg18, seg19, seg20,
            seg21a, seg21b, seg21c, seg22, seg24]
```

Quick plot for working my way through the segments

```python
fig, ax = plt.subplots()
for seg in segments:
    if seg[1][0]=="straight_leg":
        print(
        )
    ax.plot(ds.lon.sel(time=seg[0]), ds.lat.sel(time=seg[0]))
```

```python
seg=seg22

fig = plt.figure(figsize=(12, 5))
gs = fig.add_gridspec(2,2)
ax1 = fig.add_subplot(gs[:, 0])

# extend the segment time period by 3min before and after to check outside dropsonde or roll angle conditions
seg_drops = slice(pd.Timestamp(seg[0].start) - pd.Timedelta("3min"), pd.Timestamp(seg[0].stop) + pd.Timedelta("3min"))
ax1.plot(ds.lon.sel(time=seg_drops), ds.lat.sel(time=seg_drops), "C0")

# plot the previous segment as well as the chosen one
if len(segments)>1:
    seg_before = segments[segments.index(seg) - 1]
    ax1.plot(ds.lon.sel(time=seg_before[0]), ds.lat.sel(time=seg_before[0]), color="grey")
ax1.plot(ds.lon.sel(time=seg[0]), ds.lat.sel(time=seg[0]), color="C1")

# plot dropsonde markers for extended segment period as well as for the actually defined period
ax1.scatter(ds_drops.lon.sel(time=seg_drops), ds_drops.lat.sel(time=seg_drops), c="C0")
ax1.scatter(ds_drops.lon.sel(time=seg[0]), ds_drops.lat.sel(time=seg[0]), c="C1")

# potentially also include markers for BCO or METEOR
#plt.scatter(lonm, latm, c="r")
#plt.scatter(bco.lon, bco.lat, c="orange")

ax2 = fig.add_subplot(gs[0, 1])
ds["alt"].sel(time=seg_drops).plot(ax=ax2, color="C0")
ds["alt"].sel(time=seg[0]).plot(ax=ax2, color="C1")

ax3 = fig.add_subplot(gs[1, 1])
ds["roll"].sel(time=seg_drops).plot(ax=ax3, color="C0")
ds["roll"].sel(time=seg[0]).plot(ax=ax3, color="C1")
```

Check dropsonde launch times compared to the segment start and end times

```python
print(f"Segment time: {seg[0].start} to {seg[0].stop}")
print(f"Dropsonde launch times: {ds_drops.time.sel(time=seg_drops).values}")
```

### Meteor and BCO coordination
How far was the Meteor/BCO away from the HALO track?
Possible overpasses within the first three segments and before landing.

```python
def get_overpass_info(seg, ds, target_lat, target_lon):
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
```

#### Plot Meteor overpasses

```python
for seg in [seg1[0], seg2[0], seg3[0], seg22[0]]:
    plot_overpass(seg, ds, latm, lonm)
```

#### Plot BCO overpasses

```python
for seg in [seg1[0], seg24[0]]:
    plot_overpass(seg, ds, bco.lat, bco.lon)
```

## Parse info to YAML file

```python
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


def segment_hash(segment):
    import hashlib
    return hashlib.sha256(f"{segment.start}+{segment.stop}".encode("ascii")).hexdigest()[-4:]

def to_dt(dt64):
    import pandas as pd
    return pd.Timestamp(dt64).to_pydatetime(warn=False)

def get_takeoff_landing(flight_id, ds):
    """
    Detect take-off and landing based on the airport on Sal
    or Barbados which are located at 89m and 8m above WGS84 respectively.
    """
    if ds.time[0].values > np.datetime64("2024-09-07T00:00:00"):
        airport_wgs84 = 9
    else:
        airport_wgs84 = 90
    takeoff = ds["time"].where(ds.alt > airport_wgs84, drop=True)[0].values
    landing = ds["time"].where(ds.alt > airport_wgs84, drop=True)[-1].values
    duration = (landing - takeoff).astype("timedelta64[m]").astype(int)
    return takeoff, landing, duration

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
                         } for s in segments]
           }
```

```python
takeoff, landing, _ = get_takeoff_landing(flight_id, ds)
takeoff
```

```python
header = {"nickname": "The pacman circles",
          "mission": "ORCESTRA",
          "platform": "HALO",
         }
```

```python
events = [{"name": "Meteor overpass 1",
            "time": to_dt("2024-09-23T11:18:36"),
            "remark": "386m distance"},
           {"name": "Meteor overpass 2",
            "time": to_dt("2024-09-23T11:54:01"),
            "remark": "440m distance"},
           {"name": "Meteor overpass 3",
            "time": to_dt("2024-09-23T12:26:11"),
            "remark": "936m distance"},
           {"name": "Meteor overpass 4",
            "time": to_dt("2024-09-23T19:52:13"),
            "remark": "380m distance"},
           {"name": "passing by BCO",
            "time": to_dt("2024-09-23T11:18:31"),
            "remark": "1225m distance"},
           {"name": "BCO overpass",
            "time": to_dt("2024-09-23T19:56:59"),
            "remark": "363m distance"},
           {"name": "EC meeting point",
            "time": None,
            "remark": "sharp turn away from EC track right after meeting point due to deep convection"},
           ]
```

```python
import yaml
yaml.dump(seg2yaml(flight_id, ds, segments), open(f"../flight_segment_files/{flight_id}.yaml", "w"), sort_keys=False)
```

```python

```
