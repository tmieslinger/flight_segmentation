import numpy as np


def kinds_is_circle(kinds):
    return any(k in kinds for k in ["circle", "circling"])


def has_irregularity(irregularities, irregularity_tag):
    return any(i.startswith(irregularity_tag) for i in irregularities)


class FlightChecker:
    def __init__(self, flight):
        self.used_segment_ids = set()
        self.flight_id = flight.get("flight_id", "")

    def check_flight(self, flight):
        if "flight_id" not in flight:
            yield "flight_id is missing"

        if "platform" not in flight:
            yield "platform is missing"

    def check_segment(self, seg, navdata, sondes_by_flag):
        if "segment_id" in seg:
            segment_id = seg["segment_id"]
            if not segment_id.startswith(self.flight_id):
                yield "segment_id does not start with flight_id"
            if segment_id in self.used_segment_ids:
                yield "segment_id \"{}\" is duplicated".format(segment_id)
            self.used_segment_ids.add(segment_id)
        else:
            yield "segment_id is missing"

        if "kinds" in seg:
            kinds = seg["kinds"]
            if not isinstance(kinds, list):
                yield "kinds is not a list"
                del seg["kinds"]
            elif len(kinds) == 0:
                yield "segment has no kinds"
        else:
            yield "segment has no kinds attribute"
            kinds = []

        if seg["end"] <= seg["start"]:
            yield "segment ends before it starts"

        if "irregularities" in seg:
            irregularities = seg["irregularities"]
            if not isinstance(irregularities, list):
                yield "irregularities is not a list"
                del seg["irregularities"]
                irregularities = []
            else:
                if not all(isinstance(i, str) for i in irregularities):
                    yield "irregularities is not a list of str"
                    del seg["irregularities"]
                    irregularities = []
        else:
            yield "segment has no irregularities attribute"
            irregularities = []

        good_dropsondes = 0
        if "good_dropsondes" in seg:
            yield "good_dropsondes attribute is deprecated. uses dropsondes instead"
            good_dropsondes = seg["good_dropsondes"]

        if "dropsondes" not in seg:
            yield "dropsondes attribute is missing"
        elif not isinstance(seg["dropsondes"], dict):
            yield "dropsondes is not a mapping"
        else:
            for flag, sonde_ids in seg["dropsondes"].items():
                if not isinstance(sonde_ids, list):
                    yield "dropsondes with flag {} are not a list".format(flag)
            good_dropsondes = len(seg["dropsondes"].get("GOOD", []))

            dropsondes_from_info = {f: [s["sonde_id"] for s in sondes]
                                    for f, sondes in sondes_by_flag.items()}
            dropsondes_from_segment = {f: s
                                       for f, s in seg["dropsondes"].items()
                                       if len(s) > 0}
            if dropsondes_from_segment != dropsondes_from_info and not has_irregularity(irregularities, "SAM"):
                yield "dropsondes in segment file are different from sondes in sondes.yaml and no SAM irregularity is recorded"

        sonde_times = list(sorted([s["launch_time"]
                                   for sondes in sondes_by_flag.values()
                                   for s in sondes]))

        if good_dropsondes != len(sondes_by_flag.get("GOOD", [])) and not has_irregularity(irregularities, "SAM"):
            yield "inconsistent number of good sondes between segment file and sondes.yaml and no SAM irregularity is recorded"

        t_start = np.datetime64(seg["start"])
        if "circle" in kinds and len(sonde_times) > 0:
            seconds_to_first_sonde = (np.datetime64(sonde_times[0]) - t_start) \
                                   / np.timedelta64(1, "s")
            if abs(seconds_to_first_sonde - 60.) > .75 and not has_irregularity(irregularities, "TTFS"):
                # use a little bit more that .5 sec offset to cover rounding errors
                yield "time to first sonde is not 1 minute and no TTFS irregularities are recorded"
