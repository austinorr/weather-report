import sys

from .weather_report import WeatherReport
from .default_config import defaults


def main():

    args = sys.argv[1:]

    if any(i in args for i in ["--project-file"]):
        print(defaults)
    else:
        for i in args:
            f = WeatherReport.from_input_file(i)
            f.run()
