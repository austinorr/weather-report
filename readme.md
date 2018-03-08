# Program Description

This program will save local copies of NOAA weather report each time it is run.
There are many options for configuring the behavior to support continuous
weather checking, including email alerts, pdf attachments, and detailed
control of the notification system frequency.

# Install Instructions

Python dependencies: `pandas`, `numpy`, `beautifulsoup4`, `html5lib`, `lxml`, `pdfkit`

Binary dependencies: `wkhtmltopdf`

If you're using `conda` the `Make_env.bat` file will setup your machine
with the necessary binary dependencies and conda environment. This script
will remove any environment named `weather_report` and create a new one for you. 

# Setup Instructions

On Windows:

1. run the `Make_env.bat`
2. clone this repo with `>git clone https://github.com/austinorr/weather-report.git`
3. `>cd weather-report`
4. `>activate weather_report`
5. `>pip install -e .`
6. `>weather_report --project-file`
7. follow instructions on setting up a project
7. profit
