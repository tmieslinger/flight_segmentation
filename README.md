## Segmentation of flights during ORCESTRA

The Research Flights (RFs) during ORCESTRA can be divided into different segments.
For example circles and straight legs were purposefully conducted maneuvers during which
a distinct sampling behaviour of the various instruments can be assumed. For future analyses
based on specific kinds of flight segments (e.g. only based on circles) it is desired to use a
common set of start- and end-times to assure consistency between the studies. This repository
provides files listing the start- and end-times of  flight segments for selected platforms and 
for each flight. Further information on the respective flight can be found in the
[flight reports](https://github.com/orcestra-campaign/book/tree/main/orcestra_book/reports).

Flight segments need not be unique or complete: a given time during a flight may belong to
any number of segments or none at all. Segments may overlap (i.e. a segment of kind `straight_leg`
may include a segments of kind `ec_underpass`). This allows flights to be segmented
in multiple ways and at multiple levels of granulatiry.

The segmentation copies and adapts many ideas from the [flight segmentation](https://github.com/eurec4a/flight-phase-separation) conducted for the EUREC4A field campaign.

### Common vocabulary - broad sampling strategy
Following are names of segments assembled from a range of platforms describing broad sampling strategies. Many will contain subsets
e.g. `cloud` segments will likely contain `subcloud layer` and `cloud layer` segments.
Data providers are encouraged to use these names, especially those in the first, where applicable.
Feel free to add the the list (e.g. with a Github pull request) if needed.
* ground
* transit
* circle
* cloud
* calibration
* profile
* axbt
* rectangle
* sawtooth
* racetrack

### Common vocabulary - subsets/refinements and super-sets
* upward: primarily ascending, could be used as further detail for `profile` segments
* downward: primarily descending, could be used as further detail for `profile` segments

### Platform-specific subsets
Platforms are free to adopt other conventions exploiting the ability for a segment to have more than one kind associated with it.

* [HALO specific segmentation](HALO-segmentation-notes.md)

## Conventions
Flight segmentation is designed to be flexible and unstructured, but we propose that data providers follow the convention that
_a time or time window may not belong to more than one segment of the same kind_

## Handling of time ranges

Time ranges are defined as semi-open intervals. So the start time is part of the time range while the end time is excluded from the range. This way, it is possible to define exactly consecutive segments without any ambiguities regarding the instance in between.

## Segment irregularities

If some irregularities are found within a segment (i.e. a diversion from the planned route, starting time of a circle not one minute before a sonde), these should be recorded in the `irregularities` field. In general, this field is meant to be a free text field, such that people using the dataset get a proper explanation. However, for automatic checking it may also be useful to have some standardized *irregularity tags* which can be interpreted by a script. These tags should be prepended to the explanatory string of the irregularity.

## Reading the files

The flight segmentation data is provided in YAML files. YAML is a text based
human readable data format that uses python-like indentation for structuring its contents. It is often used for configuration
files and due to its great human readability very suited for version control, which is one reason we wanted to use it here.
For python users, the module [PyYAML](https://pyyaml.org) (included in Anaconda)
offers an easy to use way to read the data from the yaml files into plane python objects like lists and dictionaries.
Here is an example to read a file and print the circle start and end times from that file:

```
import yaml
flightinfo = yaml.load(open("HALO_20240813a.yaml"))
print([(c["start"], c["end"]) for c in flightinfo["segments"] if "circle" in c["kinds"]])
```
