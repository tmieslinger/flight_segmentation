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

        if seg["name"] is None:
            yield "this segment is missing a name"

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