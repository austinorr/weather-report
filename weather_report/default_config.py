defaults = '''# This is the Weather Report Initialization File
#
#
# Program Description
# -------------------
# This program will save local copies of NOAA weather report each time it is run.
# There are many options for configuring the behavior to support continuous
# weather checking, including email alerts, pdf attachments, and detailed
# control of the notification system frequency.
#
#
# Setup Instructions
# ------------------
#   1. Copy this information into its own file on your computer. You may
#       use the file extension '.dat' or '.ini', either one will work.
#   2. Populate the file with the necessary information, midifying default
#       as you see fit for your project.
#   3. If there is an error, please review the log file that is saved in
#       the same directory as the file you saved in Step 1.
#
#
# Initialization Conventions
# --------------------------
# 1. Both whole-line and inline comments are allowed with a '#' character.
# 2. Keys (words left of a '=' character) contain clues
#   - _path is a filepath
#   - _list can be a comma separated list or a semi-colon separated list
#   - _email should be a valid email address containing an '@' character.
#       Where combined with '_list' the program will support a list of emails.
#       This field will ignore the following characters: '<>;:(){}'
#   - _bool should be 'true' or 'yes' or 'false' or 'no'
#
#

[project_info]
# --- BEGIN Required Information --- #

# This should be the infor for the person configuring this file (you)
primary_contact_name = Your Name
primary_contact_email = you@domain.com

# Site and Project Information
site_description = CGP IGP Site sampling and ongoing monitoring
site_short_name = CGP IGP Site
project_number = WW1234

#################################################################################################################################
#                                                                                                                               #
#   MANDATORY: `site_map_click_url` 1 MUST BE "7-day Weather Forcast from NOAA"                                                 #
#   For Example: https://forecast.weather.gov/MapClick.php?lon=-122.2727902900182&lat=37.8027201762995#.WqBjeejwaUk             #
#   This will tell the program where your project is located and allow it to find the other default weather report pages.       #
#                                                                                                                               #
#################################################################################################################################

site_map_click_url = https://forecast.weather.gov/MapClick.php?lon=-122.2727902900182&lat=37.8027201762995#.WqBjeejwaUk

# --- END Required Information --- #

pdf_threshold_value = 0
pdf_save_interval_hours = 24

# HH:MM or HH in military time
pdf_save_interval_start_time = 6:00

pdf_email_list = <you@domain.com> , other_staff@domain.com
attach_pdf_bool = true
local_pdf_folder = Forecasts

alert_threshold_value = 0
alert_email_list = <you@domain.com> , other_staff@domain.com
attach_alert_pdf_bool = false
alert_resend_interval_hours = 12


[options]
# built-in pages are as follows:
# 1 printable_mapclick
# 2 tabular
# 3 graphical
# you may control the order of these pages by modifying the
# `pdf_content_order_list` parameter below.

pdf_content_order_list = 1,2,3
silent_mode_bool = false

# List additional urls to append to the report separated by a comma.
# New lines must break at commas and be indented by at least one space.
# These will be appended at the end of the pdf in order.
additional_urls_list =


[gmail]
# --- REQUIRED if sending email --- #
user =
pwd =
'''
