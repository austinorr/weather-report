
import os
from datetime import datetime, timedelta
import pandas
import pdfkit
import logging

from .configurator import WeatherParser
from .helper import _write_timestamp, _read_timestamp
from .email_handler import send_msg


def _find_weather_data(tables):
    """`tables` is a list of dataframes returned by `pandas.read_html`"""
    for i, raw in enumerate(tables):
        if len(raw) > 16:
            return raw


def _get_nan_indices(table):
    idxs = list(pandas.isnull(table[0]).nonzero()[0])
    idxs.append(len(table))
    return idxs


def _cleanup_table(table, nan_indices):
    dfs = []
    i = 0
    for ix in nan_indices:
        df = table.iloc[i:ix, :].T.reindex()
        df.columns = df.iloc[0]
        df = df.reindex(df.index.drop(0))
        if len(df.T) > 0:
            dfs.append(df)
        i = ix + 1
    return pandas.concat(dfs).reset_index(drop=True)


def _coerce_float(clean, col_strs):
    float_cols = []
    for c in clean.columns:
        for col in col_strs:
            if col in c.lower():
                float_cols.append(c)
    clean[float_cols] = clean[float_cols].astype(float)
    return clean


def _cleanup_date(clean, date):
    clean[date] = clean[date].fillna(method='ffill')
    for c in clean.columns:
        if 'hour' in c.lower():
            hour_col = c
    clean[date] = str(datetime.now().year) + " " + \
        clean[date] + " " + clean[hour_col].astype(str)
    clean[date] = pandas.to_datetime(clean[date], format='%Y %m/%d %H.%M')
    return clean


def _process_html(url):
    tables = pandas.read_html(url)
    table = _find_weather_data(tables)
    nan_indices = _get_nan_indices(table)

    clean = (table
             .pipe(_cleanup_table, nan_indices)
             .pipe(_coerce_float, ['dewpoint', 'gust', 'hour', 'humidity', 'mph', 'temperature', '%'])
             .pipe(_cleanup_date, 'Date')
             )
    return clean


def _get_precip_col(df):
    for c in df.columns:
        if all([i in c.lower() for i in ['precip', 'potential']]):
            return c


def _get_greater_than(df, col, threshold=0, pct_threshold=25):
    return df[(df[col].values >= threshold - (threshold * (pct_threshold / 100)))]


def _to_list(val):
    if val is None:
        return []
    elif isinstance(val, str):
        val = [val]
    try:
        assert isinstance(val, list)
    except:
        raise TypeError('Pass {} as a list.'.format(val))

    return val


def _get_lat_long(url):
    queries = url.split("#")[0].split('?')[-1].split("&")
    out = {}
    for i in queries:
        if 'lat' in i.lower():
            out['lat'] = i.split("=")[-1]
        if 'lon' in i.lower():
            out['lon'] = i.split("=")[-1]
    return out


def _replace_query(url, dct):
    domain, query = url.split('?')
    queries = query.split("&")

    out = []
    for i in queries:
        k, v = i.split("=")
        if k in dct:
            out.append("=".join([k, dct[k]]))
        else:
            out.append(i)
    out = "&".join(out)

    return "?".join([domain, out])


def _build_default_url_list(url):
    urls = []
#     urls.append(url)
    click_coords = _get_lat_long(url)

    printable = "https://forecast.weather.gov/MapClick.php?lat=000&lon=000&unit=0&lg=english&FcstType=text&TextType=2"
    tabular = "https://forecast.weather.gov/MapClick.php?lat=000&lon=000&unit=0&lg=english&FcstType=digital"
    graphical = "https://forecast.weather.gov/MapClick.php?lat=000&lon=000&unit=0&lg=english&FcstType=graphical"

    for site in [printable, tabular, graphical]:
        new_url = _replace_query(site, click_coords)
        urls.append(new_url)
    return urls


def _parse_time(string):
    '''string must be in HH:MM format. returns tuple'''
    ts = string.split(":")
    m = 0
    if len(ts) == 1:
        h = int(ts[0])
    elif len(ts) == 2:
        h, m = tuple(map(int, ts))
    else:
        raise ValueError('Time entry is invalid.')
    return h, m


def _get_current_hour_minute():
    return datetime.now().hour, datetime.now().minute


class WeatherReport(object):

    def __init__(self,
                 user=None,
                 pwd=None,
                 primary_contact_name=None,
                 primary_contact_email=None,
                 site_description=None,
                 site_short_name=None,
                 project_number=None,
                 site_map_click_url=None,
                 pdf_threshold_value=None,
                 pdf_email_list=None,
                 attach_pdf_bool=None,
                 pdf_save_interval_hours=None,
                 pdf_save_interval_start_time=None,
                 local_pdf_folder=None,
                 alert_threshold_value=None,
                 alert_email_list=None,
                 attach_alert_pdf_bool=None,
                 alert_resend_interval_hours=None,
                 pdf_content_order_list=None,
                 additional_urls_list=None,
                 silent_mode_bool=None,
                 **kwargs,
                 ):
        self.user = user
        self.pwd = pwd
        self.primary_contact_name = primary_contact_name
        self.primary_contact_email = primary_contact_email
        self.site_description = site_description
        self.site_short_name = site_short_name
        self.project_number = project_number
        self.site_map_click_url = site_map_click_url

        if pdf_threshold_value is None:
            pdf_threshold_value = 0
        self.pdf_threshold_value = float(pdf_threshold_value)

        self.pdf_email_list = _to_list(pdf_email_list)

        if attach_pdf_bool is None:
            attach_pdf_bool = True
        self.attach_pdf_bool = attach_pdf_bool

        if pdf_save_interval_hours is None:
            pdf_save_interval_hours = 0
        self.pdf_save_interval_hours = float(pdf_save_interval_hours)

        if pdf_save_interval_start_time is None:
            pdf_save_interval_start_time = '0'
        self.pdf_save_interval_start_time = _parse_time(
            pdf_save_interval_start_time)

        if local_pdf_folder is None:
            local_pdf_folder = 'Forecasts'
        self.local_pdf_folder = local_pdf_folder

        if alert_threshold_value is None:
            alert_threshold_value = 0
        self.alert_threshold_value = float(alert_threshold_value)

        self.alert_email_list = _to_list(alert_email_list)

        if attach_alert_pdf_bool is None:
            attach_alert_pdf_bool = True
        self.attach_alert_pdf_bool = attach_alert_pdf_bool

        if alert_resend_interval_hours is None:
            alert_resend_interval_hours = 0
        self.alert_resend_interval_hours = float(alert_resend_interval_hours)

        if pdf_content_order_list is None:
            pdf_content_order_list = [1, 2, 3]
        self.pdf_content_order_list = pdf_content_order_list

        self.additional_urls_list = _to_list(additional_urls_list)

        if silent_mode_bool is None:
            silent_mode_bool = False
        self.silent_mode_bool = silent_mode_bool

        self.unused_args = kwargs

        required = ['primary_contact_name', 'primary_contact_email',
                    'site_description', 'site_short_name', 'site_map_click_url',
                    'project_number']

        for i in required:
            if getattr(self, i) is None:
                e = "{} is a required argument".format(i)
                raise TypeError(e)

        if self.pdf_email_list or self.alert_email_list:
            for i in ['user', 'pwd']:
                if getattr(self, i) is None:
                    e = "{} is a required argument for sending emails".format(
                        i)
                    raise TypeError(e)

        self.pdf_fname = ".pdf_last_saved"
        self.pdf_tsnote = "pdf saved at: "

        self.alert_fname = ".alert_last_sent"
        self.alert_tsnote = "email alert sent at: "

        # properties
        self._urls = None
        self._config = None
        self._save_dir = None
        self._pdf_path = None
        self._noaa_tabular = None
        self._precip_column = None
        self._precip_table = None
        self._logger = None

    @classmethod
    def from_input_file(cls, input_file):
        config = WeatherParser(input_file)
        options = config.dict
        w = cls(**options['project_info'], **options['options'], **options['gmail'])
        w._config = config
        return w

    @property
    def config(self):
        return self._config

    @property
    def logger(self):
        if self._logger is None:
            directory = os.getcwd()
            if self.config is not None:
                directory = self.config.directory
            logfile = self.site_short_name + ".log"

            logging.basicConfig(filename=os.path.join(directory, logfile),
                                format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                                level=logging.INFO,
                                )
            self._logger = logging.getLogger(__name__)
        return self._logger

    @property
    def noaa_tabular(self):
        if self._noaa_tabular is None:
            try:
                self._noaa_tabular = _process_html(self.urls[1])
            except Exception as e:
                self.logger.exception(e)
                if not self.silent_mode_bool:
                    raise(e)
        return self._noaa_tabular

    @property
    def precip_column(self):
        if self._precip_column is None:
            self._precip_column = _get_precip_col(self.noaa_tabular)
        return self._precip_column

    @property
    def precip_table(self):
        if self._precip_table is None:
            self._precip_table = (
                self.noaa_tabular.loc[:, ('Date', self.precip_column)]
                .pipe(_get_greater_than, self.precip_column, self.alert_threshold_value, pct_threshold=25)
            )
        return self._precip_table

    @property
    def precip_max(self):
        if len(self.precip_table) > 0:
            return self.precip_table[self.precip_column].values.max()
        return 0

    @property
    def needs_alert(self):
        over_thresh = self.precip_max >= self.alert_threshold_value

        try:
            last_alert_time = self._read_last_alert_file()
            tolerance = timedelta(minutes=5)
            interval = timedelta(hours=float(
                self.alert_resend_interval_hours)) - tolerance
            out_of_date = datetime.utcnow() - interval > last_alert_time

        except FileNotFoundError as e:
            out_of_date = True

        return over_thresh and out_of_date

    def _read_last_alert_file(self):
        directory = os.getcwd()
        if self.config is not None:
            directory = self.config.directory
        fpath = os.path.join(directory, self.alert_fname)
        return _read_timestamp(fpath, note=self.alert_tsnote)

    def _write_last_alert_file(self):

        directory = os.getcwd()
        if self.config is not None:
            directory = self.config.directory
        fpath = os.path.join(directory, self.alert_fname)
        _write_timestamp(fpath, note=self.alert_tsnote)

    @property
    def needs_new_pdf(self):
        over_thresh = self.precip_max >= self.pdf_threshold_value

        try:
            last_pdf_time = self._read_last_pdf_file()
            tolerance = timedelta(minutes=5)
            interval = timedelta(hours=float(
                self.pdf_save_interval_hours)) - tolerance
            out_of_date = datetime.utcnow() - interval > last_pdf_time

        except FileNotFoundError as e:
            out_of_date = True

        return over_thresh and out_of_date

    def _read_last_pdf_file(self):
        directory = os.getcwd()
        if self.config is not None:
            directory = self.config.directory
        fpath = os.path.join(directory, self.pdf_fname)
        return _read_timestamp(fpath, note=self.pdf_tsnote)

    def _write_last_pdf_file(self):

        directory = os.getcwd()
        if self.config is not None:
            directory = self.config.directory
        fpath = os.path.join(directory, self.pdf_fname)
        _write_timestamp(fpath, note=self.pdf_tsnote)

    @property
    def save_dir(self):
        if self._save_dir is None:
            if self.config is None:
                if not os.path.exists(self.local_pdf_folder):
                    os.makedirs(self.local_pdf_folder)
                self.save_dir = self.local_pdf_folder
            else:
                path = os.path.join(self.config.directory,
                                    self.local_pdf_folder)
                if not os.path.exists(path):
                    os.makedirs(path)
                self._save_dir = path
        return self._save_dir

    @property
    def urls(self):
        if self._urls is None:
            self._urls = _build_default_url_list(self.site_map_click_url)
        return self._urls

    @property
    def pdf_path(self):
        return self._pdf_path

    def send_pdf_email(self):

        _email_subject = 'NOAA Forecast for {}.'.format(
            self.site_short_name
        )

        _email_body = '''
                <p><TT>
                This is an automated message sent
                from the Water and Natural
                Resources Group in Oakland, CA.</TT>

                <p><TT>
                A project near {} expects a {}%
                chance of rain in the next 48 hrs.
                The forecast is shown below:</TT>

                <p><TT>{}</TT>
                <p><TT>Source: {}</TT>
                <hr>
                <p><TT>
                To remove yourself from this list
                contact {}.
                </TT>
                '''.format(self.site_short_name , self.precip_max,
                           self.precip_table.to_html(index=False),
                           self.urls[1], self.primary_contact_name
                           )
        attachments = []
        if self.attach_pdf_bool:
            attachments.append(self.pdf_path)

        try:
            send_msg(self.user, self.pwd, self.pdf_email_list, _email_subject,
                     _email_body, attachments=attachments, verbose=False)
            self.logger.info(
                "PDF Email Sent to: {}".format(self.pdf_email_list))
        except Exception as e:
            self.logger.exception(e)
            if not self.silent_mode_bool:
                raise(e)

    def send_alert_email(self):
        _email_subject = 'ALERT: NOAA Forecast expects greater than {}% chance of rain in next 48 hours at {}.'.format(
            self.alert_threshold_value, self.site_short_name
        )

        _email_body = '''
                <p><TT>
                This is an automated message sent
                from the Water and Natural
                Resources Group in Oakland, CA.</TT>

                <p><TT>
                A project near {} expects a {}%
                chance of rain in the next 48 hrs.
                The forecast is shown below:</TT>

                <p><TT>{}</TT>
                <p><TT>Source: {}</TT>
                <hr>
                <p><TT>
                To remove yourself from this list
                contact {}.
                </TT>
                '''.format(self.site_short_name , self.precip_max,
                           self.precip_table.to_html(index=False),
                           self.urls[1], self.primary_contact_name
                           )

        attachments = []
        if self.attach_alert_pdf_bool:
            self.save_pdf()
            attachments.append(self.pdf_path)

        try:
            send_msg(self.user, self.pwd, self.alert_email_list, _email_subject,
                     _email_body, attachments=attachments, verbose=False)
            self.logger.info(
                "Alert Email Sent to: {}".format(self.alert_email_list))

        except Exception as e:
            self.logger.exception(e)
            if not self.silent_mode_bool:
                raise(e)

    def save_pdf(self):

        # for debugging: ("%Y-%m-%d %H%M%S.%f")[:-3]
        tstamp = datetime.now().strftime("%Y-%m-%d %H%M")
        pdfname = tstamp + ' ' + self.site_short_name + '.pdf'
        pdf_path = os.path.join(self.save_dir, pdfname)

        self._pdf_path = pdf_path

        # for pdfkit, suppress cmd output
        pdfoptions = {
            'quiet': '',
        }

        urls = [self.urls[
            int(i) - 1] for i in self.pdf_content_order_list] + self.additional_urls_list

        try:
            pdfkit.from_url(urls,  self.pdf_path, options=pdfoptions)

        except OSError as e:
            try:
                pdfkit.from_url(urls,  self.pdf_path, options={})

            except OSError as e:
                error_str = "".join(e.args)
                if "HostNotFoundError" in error_str and all([_ in error_str.lower() for _ in ['printing pages', 'done']]):
                    if not self.silent_mode_bool:
                        print('Host Error Encountered.', error_str)
                        print('PDF saved anyway.')
                else:
                    self.logger.exception(e)
                    if not self.silent_mode_bool:
                        print(
                            'Save Process Unsuccessful. Check Input File and URL Paths.')
                        raise(e)

        except Exception as e:
            self.logger.exception(e)
            if not self.silent_mode_bool:
                raise(e)

        self.logger.info("Saved PDF: {}".format(self.pdf_path))

    def run(self):
        try:
            if self.needs_new_pdf and _get_current_hour_minute() >= self.pdf_save_interval_start_time:
                self.save_pdf()
                self._write_last_pdf_file()
                if self.pdf_email_list:
                    self.send_pdf_email()

            if self.needs_alert:
                if self.alert_email_list:
                    self.send_alert_email()
                    self._write_last_alert_file()

        except Exception as e:
            self.logger.exception(e)
            if not self.silent_mode_bool:
                raise(e)
