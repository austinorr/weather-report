import datetime


def _write_timestamp(file, note=None):
    if note is None:
        note = ""
    with open(file, 'w') as f:
        ts = str(datetime.datetime.utcnow().timestamp())
        f.write(note + ts)


def _read_timestamp(file, note=None):
    if note is None:
        note = ""
    with open(file, 'r') as f:
        ts = float(f.read().replace(note, ''))
        return datetime.datetime.fromtimestamp(ts)
