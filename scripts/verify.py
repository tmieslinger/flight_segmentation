import os
import logging
import traceback
import yaml
import numpy as np
from contextlib import closing


from navdata import get_navdata
from checkers import FlightChecker

def validate(segment_file, sonde_info):
    flightlogger = logging.getLogger("flight")
    segmentlogger = logging.getLogger("segment")

    flightdata = yaml.load(open(segment_file), Loader=yaml.SafeLoader)
    checker = FlightChecker(flightdata)
    sonde_info = [s for s in sonde_info if s["platform"] == flightdata["platform"]]

    flight_warnings = list(checker.check_flight(flightdata))
    for warning in flight_warnings:
        flightlogger.warning(warning)

    segment_warning_count = 0
    with closing(get_navdata(flightdata["platform"], flightdata["flight_id"]).load()) as navdata:
        for seg in flightdata["segments"]:
            t_start = np.datetime64(seg["start"])
            t_end = np.datetime64(seg["end"])
            seg_navdata = navdata.sel(time=slice(t_start, t_end))

            sondes_in_segment = [s
                                 for s in sonde_info
                                 if s["launch_time"] >= seg["start"]
                                 and s["launch_time"] < seg["end"]]
            sondes_by_flag = {f: [s for s in sondes_in_segment if s["flag"] == f]
                              for f in set(s["flag"] for s in sondes_in_segment)}

            warnings = list(checker.check_segment(seg, seg_navdata, sondes_by_flag))
            for warning in warnings:
                if "segment_id" in seg:
                    segmentlogger.warning(seg["segment_id"])
                segmentlogger.warning(warning)

            segment_warning_count += len(warnings)

    return len(flight_warnings), segment_warning_count


def _main():
    try:
        import coloredlogs
        coloredlogs.install(level='WARNING')
    except:
        logging.basicConfig(format='%(levelname)s %(name)s: %(message)s', level=logging.WARNING)
    mainlogger = logging.getLogger("main")

    basedir = os.path.abspath(os.path.dirname(__file__))

    import tqdm
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("infiles", type=str, nargs="+")
    parser.add_argument("-s", "--sonde_info", help="sonde info yaml file", default=os.path.join(basedir, "sondes.yaml"))
    args = parser.parse_args()

    sonde_info = yaml.load(open(args.sonde_info), Loader=yaml.SafeLoader)

    total_warnings = 0
    for filename in tqdm.tqdm(args.infiles):
        mainlogger.info("verifying %s", filename)
        try:
            flight_warning_count, segment_warning_count = validate(
                        filename, sonde_info)
            total_warnings += flight_warning_count + segment_warning_count
            mainlogger.info("%d flight warnings, %d segment warnings",
                            flight_warning_count,
                            segment_warning_count)
        except Exception as e:
            total_warnings += 1
            traceback.print_exc()
            mainlogger.error("exception while processing segment file %s: %s",
                             filename, e)


    if total_warnings == 0:
        return 0
    else:
        return 1

if __name__ == "__main__":
    exit(_main())
