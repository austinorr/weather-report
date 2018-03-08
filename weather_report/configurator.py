import os
from configparser import ConfigParser


def _clean_path(path):
    return path.replace("\\", os.sep)


def _clean_email(email, remove='<>;:(){}'):
    if "@" in email:
        return "".join(c for c in email if c not in remove)
    else:
        e = "invalid email address {}".format(email)
        raise ValueError(e)


def _clean_string(string, remove=["[", "]", "'", '"', "{", "}"]):
    return "".join(c for c in string if c not in remove)


def _convert_to_list(string, list_delim=[",", ";"]):
    string = _clean_string(string)
    for char in list_delim:
        string = string.replace(char, ",")
    return [i.strip() for i in string.split(",") if i]


class WeatherParser(ConfigParser):

    def __init__(self, filename=None):
        super().__init__(inline_comment_prefixes='#')

        self.optionxform = str
        if filename is not None:
            self.filename = os.path.realpath(_clean_path(filename))
            self.read(self.filename, encoding='utf-8-sig')

        self._directory = None

        self._dict = {}
        for sect in self.sections():
            self._dict[sect] = {}
            for opt in self.options(sect):
                self._dict[sect][opt] = self._parse_opt(sect, opt)

    @property
    def dict(self):
        return self._dict

    @property
    def directory(self):
        if self._directory is None:
            self._directory = os.path.realpath(
                os.path.dirname(_clean_path(self.filename)))
        return self._directory

    def _parse_opt(self, section, option):

        raw = self.get(section, option)

        if raw.lower() in ["''", '""', 'none', None, ""]:

            if '_list' in option:
                return []
            return

        if '_bool' in option:
            return self.getboolean(section, option, fallback=True)

        if '_email' in option:
            if '_list' in option:
                emails = []
                for email in _convert_to_list(raw):
                    emails.append(_clean_email(email))
                return emails
            return _clean_email(raw)

        if '_path' in option:
            val = _clean_string(raw)
            path = _clean_path(val)
            if '_list' in opt:
                path = [os.path.realpath(s.strip())
                        for s in _convert_to_list(path)]
            else:
                path = os.path.realpath(path)
            return path

        if '_list' in option:
            return _convert_to_list(raw)

        if '_url' in option:
            return _clean_string(raw)

        else:
            return raw
