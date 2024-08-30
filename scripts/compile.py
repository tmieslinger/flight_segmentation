import sys
import yaml
from collections import defaultdict


flight_key_priority = [
    "flight_id",
    "name",
    "nickname",
    "date",
    "platform",
    "mission",
    "takeoff",
    "landing",
    "flight_report",
    "contacts",
    "remarks",
]

segment_key_priority = [
    "segment_id",
    "name",
    "start",
    "end",
    "kinds",
    "irregularities",
]


def sort_keys(d, priority=None):
    # this requires python >= 3.7 as it relies on dictionary order
    if priority is None:
        priority = []
    ordered_keys = [k for k in priority if k in d] + \
                   [k for k in sorted(d.keys()) if k not in priority]
    return dict([(k, d[k]) for k in ordered_keys])


def _main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("infiles", type=str, nargs="+")
    parser.add_argument("-o", "--outfile", type=str)

    args = parser.parse_args()

    all_flights = defaultdict(dict)

    for filename in args.infiles:
        with open(filename) as f:
            flight = yaml.load(f, Loader=yaml.SafeLoader)
        all_flights[flight["platform"]][flight["flight_id"]] = sort_keys(
                {**flight, "segments": list(sorted((sort_keys(seg, segment_key_priority) for seg in flight["segments"]),
                                                   key=lambda seg: seg["start"]))},
                flight_key_priority)

    if args.outfile:
        outfile = open(args.outfile, "w")
    else:
        outfile = sys.stdout

    yaml.dump(sort_keys(dict(all_flights.items())), outfile, allow_unicode=True, sort_keys=False)

    return 0


if __name__ == "__main__":
    exit(_main())
