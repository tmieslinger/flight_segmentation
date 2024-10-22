---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.16.4
  kernelspec:
    display_name: flight_segment
    language: python
    name: flight_segment
---

# Flight segmentation HALO-20240923a

```python
import matplotlib
import yaml
import hvplot.xarray
import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

#import os
#import sys
#module_path = os.path.abspath(os.path.join('../scripts'))
#if module_path not in sys.path:
#    sys.path.append(module_path)

from orcestra import bco
#from orcestra.flightplan import geod
from navdata import get_navdata_HALO
from utils import get_sondes_l1, to_yaml, get_takeoff_landing, plot_overpass, to_dt
```

```python
platform = "HALO"
flight_id = "HALO-20240923a"
location = "BARBADOS" #"BARBADOS" or "CAPE_VERDE"
```

## Get HALO position and attitude

```python
ds = get_navdata_HALO(flight_id)
```

## Get dropsonde launch times

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

On Barbads, the airport runway plus bumps make HALO move between 7.8-8m above WGS84, on Sal between 88.2-88.4m above WGS84. We therefore define the flight time such that altitude must be above 9m on Barbados and 90m on Sal.

```python
takeoff, landing, duration = get_takeoff_landing(flight_id, ds)
print("take-off: ", takeoff)
print("landing: ", landing)
print(f"flight duration (hh:mm): {int(duration / 60)}:{int(duration % 60)}")
```

### Get EC track

```python
import orcestra.sat
ec_fcst_time  = np.datetime_as_string(takeoff, unit='D')
ec_track = orcestra.sat.SattrackLoader("EARTHCARE", ec_fcst_time, kind="PRE",roi=location) \
    .get_track_for_day(ec_fcst_time)\
    .sel(time=slice(f"{ec_fcst_time} 14:00", None))
```

### Plot flight track and dropsondes

```python
fotos = [
    "2023-09-23T11:23:58",
    "2023-09-23T11:34:10",
    "2023-09-23T12:00:10",
    ]
```

```python
plt.plot(ds.lon.sel(time=slice(takeoff, landing)), ds.lat.sel(time=slice(takeoff, landing)), label="HALO track")
plt.scatter(ds_drops.lon, ds_drops.lat, s=10, c="k", label="dropsondes")
plt.plot(ec_track.lon, ec_track.lat, c='C1', ls='dotted', label="EC track")
plt.ylim([8, 15])
plt.xlabel("longitude / °")
plt.ylabel("latitude / °")
plt.legend();

foto = False
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

### Quick plot for working your way through the segments piece by piece
select the segment that you'd like to plot and optionally set the flag True for plotting the previous segment in your above specified list as well. The latter can be useful for the context if you have segments that are close or overlap in space, e.g. a leg crossing a circle.

```python
seg=seg22
add_previous_seg = False

###########################

fig = plt.figure(figsize=(12, 5))
gs = fig.add_gridspec(2,2)
ax1 = fig.add_subplot(gs[:, 0])

# extend the segment time period by 3min before and after to check outside dropsonde or roll angle conditions
seg_drops = slice(pd.Timestamp(seg[0].start) - pd.Timedelta("3min"), pd.Timestamp(seg[0].stop) + pd.Timedelta("3min"))
ax1.plot(ds.lon.sel(time=seg_drops), ds.lat.sel(time=seg_drops), "C0")

# plot the previous segment as well as the chosen one
if add_previous_seg:
    if segments.index(seg) > 0:
        seg_before = segments[segments.index(seg) - 1]
        ax1.plot(ds.lon.sel(time=seg_before[0]), ds.lat.sel(time=seg_before[0]), color="grey")
ax1.plot(ds.lon.sel(time=seg[0]), ds.lat.sel(time=seg[0]), color="C1")

# plot dropsonde markers for extended segment period as well as for the actually defined period
ax1.scatter(ds_drops.lon.sel(time=seg_drops), ds_drops.lat.sel(time=seg_drops), c="C0")
ax1.scatter(ds_drops.lon.sel(time=seg[0]), ds_drops.lat.sel(time=seg[0]), c="C1")

ax2 = fig.add_subplot(gs[0, 1])
ds["alt"].sel(time=seg_drops).plot(ax=ax2, color="C0")
ds["alt"].sel(time=seg[0]).plot(ax=ax2, color="C1")

ax3 = fig.add_subplot(gs[1, 1])
ds["roll"].sel(time=seg_drops).plot(ax=ax3, color="C0")
ds["roll"].sel(time=seg[0]).plot(ax=ax3, color="C1")

#Check dropsonde launch times compared to the segment start and end times
print(f"Segment time: {seg[0].start} to {seg[0].stop}")
print(f"Dropsonde launch times: {ds_drops.time.sel(time=seg_drops).values}")
```

### Meteor and BCO coordination
How far was the Meteor/BCO away from the HALO track?
Possible overpasses within the first three segments and before landing.


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

## Events
events are different from segments in having only **one** timestamp. Examples are the usual "EC meeting points" or station / ship overpasses. In general, events include a mandatory `event_id` and `time`, as well as optional statements on `name`, a list of `kinds` and a list of `remarks`. Possible `kinds`include:
- `ec_underpass`
- `meteor_overpass`
- `bco_overpass`
- `cvao_overpass`

Typical `remarks` can be one string, e.g. "distance: ??m". An `event_id` will be added when saving it to YAML.

```python
events = [{"name": "Meteor overpass 1",
           "time": "2024-09-23T11:18:36",
           "kinds": ["meteor_overpass"],
           "distance": 386,
          },
           {"name": "Meteor overpass 2",
            "time": "2024-09-23T11:54:01",
           "kinds": ["meteor_overpass"],
            "distance": 440,
           },
           {"name": "Meteor overpass 3",
            "time": "2024-09-23T12:26:11",
           "kinds": ["meteor_overpass"],
            "distance": 936,
           },
           {"name": "Meteor overpass 4",
            "time": "2024-09-23T19:52:13",
           "kinds": ["meteor_overpass"],
            "remarks": ["distance: 380m"]},
           {"name": "passing by BCO",
            "time": "2024-09-23T11:18:31",
           "kinds": ["bco_overpass"],
            "remarks": ["distance: 1225m"]},
           {"name": "BCO overpass",
            "time": "2024-09-23T19:56:59",
            "kinds": ["bco_overpass"],
            "remarks": ["distance: 363m"]},
           {"name": "EC meeting point",
            "time": "2024-09-23",
            "kinds": ["ec_underpass"],
            "remarks": ["sharp turn away from EC track right after meeting point due to deep convection"]},
           ]
```

## Parse info to YAML file

```python
header = {"nickname": "The pacman circles",
         }
```

```python
yaml.dump(to_yaml(platform, flight_id, ds, segments, events),
          open(f"../flight_segment_files/{flight_id}.yaml", "w"),
          sort_keys=False)
```

## Import YAML and test it

```python
import yaml
flightinfo = yaml.load(open("../flight_segment_files/HALO_20240813a.yaml"))
```

```python
fig, ax = plt.subplots()
for seg in segments:
    if seg[1][0]=="straight_leg":
        
        ax.plot(ds.lon.sel(time=seg[0]), ds.lat.sel(time=seg[0]), color="C0")
```

```python

```
