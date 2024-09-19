## Methodology to determine flight segments for HALO

A flight segment is a period of some constant characteristics during a RF.
For example during a circle segment, the roll angle and the temporal change in aircraft heading can be assumed to roughly be constant.
The circles during ORCESTRA were especially associated with the regular launch of dropsondes, most of the time 12 per circle, every 30&deg; heading.
Such general characteristics of the various flight segments and a first idea about the flight patterns from the flight reports (available [here](https://github.com/orcestra-campaign/book/tree/main/orcestra_book/reports)) are used as a starting point to approach the flight phase segmentation.
The BAHAMAS datasets and the dropsonde launch times are then analysed to consistently determine the specific flight segment timestamps.

To precisely determine the periods of flight segments, a rather manual approach is taken where the flight reports and the altitude, as well as roll and pitch angles are used as first indicators to determine the segment periods.
The exact times are then found iteratively by the dataset creator with a set of standardized plots of the BAHAMAS data and after undergoing a set of tests that depend on the particular "kinds" of the flight segment.
Because of this simple procedure the only relevant place that denotes the segment times are the YAML segmentation files.
The reference or "true" segment times are defined to always be in these files!
Users of the YAML segmentation files are encouraged to use these files with any tool of their choice and may suggest adjustments or additions by simply uploading their new version of a YAML file via a Pull Request on GitHub, which may then be reviewed and accepted to work towards new versions of this dataset.
It is expected that users of different sub-communities may have different ideas of how segments are defined, so feel encouraged to bring up your suggestions!

The following flight segments are identified, where the names directly correspond to entries in segment "kinds" in the YAML files.
The criteria to determine the start- and end-times of the segments are noted below each flight segment as well as naming conventions for the `segement_id` and `name` attribute.
Start- and end-times of flight segments should be defined to the second.

#### circle:
- The circle period is defined by a constant roll angle of 2-3 degrees (plus or minus depending on turning clockwise or counter-clockwise) for the standard circle of about 200km diameter. The smaller ATR circle typically has a roll angle of 3-5 degree depending and varying with the wind speed and direction at the respective altitude.
- Segment ID: `<FLIGHT_ID>_c<XX>`, where `<XX>` marks the circle number. Example: `HALO-20240909a_c01`
- Naming: `outside_itcz_north`, `outside_itcz_south`, `inside_itcz`, `edge_itcz_north`, `edge_itcz_south`

#### straight_leg:
- Period with constant aircraft heading and close to 0&deg; roll angle (max. 3&deg; roll for short periods).
- Straight legs were flown with various purposes, which are more closely described by the straight leg
"name"-Parameter in the YAML files and is in some cases also expressed by additional entries in the segment "kinds" attribute.
- Segment ID: `<FLIGHT_ID>_sl<XX>`, where `<XX>` marks the straight leg number. Example: `HALO-20240909a_sl01`
- Naming convention: `ferry_ascent`, `ferry_descent`, `ferry_const_alt`, `from_<NAME1>_to_<NAME2>`, where `NAME1` and `NAME2` are the names of the start and end of that leg. Example `from_c01_to_c02`.

#### ec_underpass:
- Period with constant aircraft heading and close to 0&deg; roll angle (max. 3&deg; roll for short periods).
- Straight leg along the Earthcare track.
- Segment ID: `<FLIGHT_ID>_ecu<XX>`, where `<XX>` marks the number of the erathcare underpass. Example: `HALO-20240909a_ecu01`
- Naming convention: `EC_underpass_northward`, `EC_underpass_southward`.

#### lidar_calibration:
- Maneuver typically conducted during the final descent of most RFs in FL160.
- Defined as the period of the aircraft being in FL160.
- If roll angle was close to 0&deg; the whole time, the segment is also of kind "straight_leg".
- Segment ID: `<FLIGHT_ID>_lc<XX>`, where `<XX>` marks the lidar calibration maneuver number. Example: `HALO-20240909a_lc01`
- Naming convention: `lidar_calibration`

#### radar_calibration_wiggle:
- Maneuver typically conducted during straight legs, where the aircraft tilts to a roll angle of first -20&deg; and then +20&deg;.
- If conducted during a straight leg, the straight leg is split into three flight segments:
1.) straight_leg, 2.) radar_cal_wiggle, 3.) straight_leg.
- Segments start and end at about 0&deg; roll angle.
- Segment ID: `<FLIGHT_ID>_rcw<XX>`, where `<XX>` marks the radar calibration wiggle number. Example: `HALO-20240909a_rcw01`
- Naming convention: `radar_calibration_wiggle`

#### radar_calibration_tilted:
- Maneuver typically conducted at the end of a straight leg, where a narrow circle pattern with a constant 10&deg; bank is flown.
- A constant roll angle of about 10&deg; is used to define the period of a "radar_cal_tilted" segment.
- Segment ID: `<FLIGHT_ID>_rct<XX>`, where `<XX>` marks the tilted radar calibration maneuver number. Example: `HALO-20240909a_rct01`
- Naming convention: `radar_calibration_tilted`

#### baccardi_calibration:
- Defined by 4 turns indicated by roll angles of about 25&deg; (1 turn: -25&deg;, 3 turns: +25&deg;).
- Segment ID: `<FLIGHT_ID>_bc<XX>`, where `<XX>` marks the bacardi calibration maneuver number. Example: `HALO-20240909a_bc01`
- Naming convention: `bacardi_calibration`

#### ec_meeting_point:
- Defined as the time when the EARTHCARE satellite is closest to HALO
- Segment ID: `<FLIGHT_ID>_ec`. Example: `HALO-20240909a_ec`
- Naming convention: `ec_meeting_point`

#### pace_meeting_point:
- Defined as the time when the PACE satellite is closest to HALO
- Segment ID: `<FLIGHT_ID>_pace`. Example: `HALO-20240909a_pace`
- Naming convention: `pace_meeting_point`

## For developers
The following workflow for generating the flight segmentation YAML files is suggested:

1. Install the requirements noted [here](scripts/requirements.txt) as well as the [IPFS Desktop App](https://docs.ipfs.tech/install/ipfs-desktop/), e.g. on Mac via `brew install --cask ipfs`.
2. Use the ipython notebook `scripts/segmentation_template.ipynb` to do a rough segmentation by zooming into the bokeh plots of roll angle, altitude or other measures.
3. Create a YAML file for the respective flight and add the respective `start` and `end` times and segments to it. For an example, have a look at `flight_segment_files/HALO-20240813a.yaml`
4. test and check the YAML file using the `scripts/report.py`: `python3 scripts/report.py flight_segment_files/HALO-20240813a.yaml reports/HALO-20240813a.html`. This will create an HTML file that you can open in any browser and check the details of the flight segments.
5. If necessary, adjust the times and further info in the YAML file and redo step 4 until you are satisfied with the segments.
6. add your final YAML file to the repo by creating a pull request and assigning a reviewer. Don't add the `reports/*.html` files. THey will be generated automatically when you do the pull request and serve as a first check to validate the new YAML file.