#!/usr/bin/env python3

import json
import signal
import sys

from pymetar import ReportFetcher, ReportParser

ICON_MAP = {
    "cloud": "☁️",
    "fog": "🌫️",
    "rain": "🌧️",
    "snow": "🌨️",
    "storm": "🌩️",
    "sun": "☀️",
    "suncloud": "🌤️",
}
ICON_UNKNOWN = "🌡️"


class TimeoutError(Exception):
    pass


class Timeout:
    def __init__(self, seconds=3, error_message="timed out"):
        self.seconds = seconds
        self.error_message = error_message

    def handle_timeout(self, signum, frame):
        raise TimeoutError(self.error_message)

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)

    def __exit__(self, type, value, traceback):
        signal.alarm(0)


class WeatherReportEncoder(json.JSONEncoder):
    REPORT_FIELDS = frozenset(
        {
            "valid",
            "givenstationid",
            "temp",
            "tempf",
            "windspeed",
            "windspeedmph",
            "winddir",
            "vis",
            "dewp",
            "dewpf",
            "humid",
            "press",
            "pressmmHg",
            "code",
            "weather",
            "sky",
            "fulln",
            "cycle",
            "windcomp",
            "rtime",
            "pixmap",
            "latitude",
            "longitude",
            "altitude",
            "stat_city",
            "stat_country",
            "reporturl",
            "latf",
            "longf",
            "cloudinfo",
            "conditions",
            "w_chill",
            "w_chillf",
            "cloudtype",
        }
    )

    def default(self, o):
        return {k: getattr(o, k, None) for k in self.REPORT_FIELDS}


class WeatherReportError(Exception):
    pass


def get_report_string(p, mode):
    if mode == "plain":
        return f"{p.weather.lower()}, {round(p.tempf)}°"
    elif mode == "raw":
        return json.dumps(p, cls=WeatherReportEncoder, indent=2, sort_keys=True)
    else:
        icon = ICON_MAP.get(p.pixmap, ICON_UNKNOWN)
        return f"{icon} {round(p.tempf)}°"


def main():
    metar_id = sys.argv[1]
    output_format = sys.argv[2].lower() if len(sys.argv) > 2 else "default"
    for i in range(0, 5):
        try:
            with Timeout():
                r = ReportFetcher(metar_id).FetchReport()
                p = ReportParser(r).ParseReport()
            print(get_report_string(p, output_format))
            break
        except (IOError, TimeoutError) as e:
            if i < 5:
                print(
                    f"{e.__class__.__name__} fetching weather for {metar_id}, retrying ({i + 1}/5)",
                    file=sys.stderr,
                )
                continue
            raise WeatherReportError(f"could not fetch weather after {i + 1} attempts")


if __name__ == "__main__":
    main()
