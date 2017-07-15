from   aslib import py
from   cron import *
from   pathlib import Path
import re

from   .job import Job
from   .program import ShellCommandProgram

#-------------------------------------------------------------------------------

MONTH_NAMES = {
    "jan":  1, "feb":  2, "mar":  3, "apr":  4, "may":  5, "jun":  6,
    "jul":  7, "aug":  8, "sep":  9, "oct": 10, "nov": 11, "dec": 12,
}

WEEKDAY_NAMES = {
    "sun": 0, "mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6,
}

def _parse(string, min, max, names={}):
    for part in string.split(","):
        try:
            part, step = part.split("/", 1)
        except ValueError:
            step    = 1
        else:
            step    = int(step)
        if part == "*":
            start   = min
            end     = max
        else:
            try:
                start, end = part.split("-", 1)
            except ValueError:
                start   = int(names.get(part.lower(), part))
                end     = start
            else:
                start   = int(names.get(start.lower(), start))
                end     = int(names.get(end.lower(), end))
        yield start, end + 1, step


def _check(val, spec):
    return any(
        start <= val < stop
        and (val - start) % step == 0
        for start, stop, step in spec
    )


class Fields:

    def __init__(self, minute="*", hour="*", day="*", month="*", weekday="*"):
        self.minute     = minute
        self.hour       = hour
        self.day        = day
        self.month      = month
        self.weekday    = weekday
        self.__parsed   = (
            tuple(_parse(minute , 0, 59)),
            tuple(_parse(hour   , 0, 23)),
            tuple(_parse(day    , 1, 31)),
            tuple(_parse(month  , 1, 12, MONTH_NAMES)),
            tuple(_parse(weekday, 0,  6, WEEKDAY_NAMES)),
        )
        

    def __repr__(self):
        return py.format_ctor(
            self, self.minute, self.hour, self.day, self.month, self.weekday)


    def __str__(self):
        return " ".join(
            (self.minute, self.hour, self.day, self.month, self.weekday))


    def match(self, minute, hour, day, month, weekday):
        m, h, d, n, w = self.__parsed
        return (
                _check(minute, m)
            and _check(hour  , h)
            and _check(month , n)
            and (
                # FIXME: This is wrong.
                   _check(day, d)
                or _check((weekday - Sun + 7) % 7, w)
            )
        )        


    def __contains__(self, time):
        time = Time(time)
        # Advance to the next round minute.
        # FIXME: Add this to cron.
        off = (Time.MIN + 60).offset - Time.MIN.offset
        time = Time.from_offset((time.offset + off - 1) // off * off)

        return self.match(
            time.minute, time.hour, time.day, time.month, time.weekday)




#-------------------------------------------------------------------------------

class CrontabSchedule:
    # FIXME: This could be made much more efficient.
    # FIXME: Crontab accepts 0 = 7 = Sunday, but we only accept 0.

    def __init__(self, tz, fields):
        self.tz     = TimeZone(tz)
        self.fields = fields


    def __repr__(self):
        return py.format_ctor(self, tz, fields)


    def __str__(self):
        return "crontab: {} @ {}".format(self.fields, self.tz)


    def to_jso(self):
        # FIXME: All wrong.
        return {
            "tz"        : str(self.tz),
            "fields"    : str(self.fields),
        }


    def __call__(self, start):
        time = Time(start)
        # Advance to the next round minute.
        # FIXME: Add this to cron.
        off = (Time.MIN + 60).offset - Time.MIN.offset
        time = Time.from_offset((Time(start).offset + off - 1) // off * off)

        while True:
            date, daytime = time @ self.tz
            if self.fields.match(
                    daytime.minute, daytime.hour,
                    date.day, date.month, date.weekday):
                yield time
            time += 60



#-------------------------------------------------------------------------------

class CrontabSyntaxError(Exception):
    pass


ENVIRONMENT_REGEX = re.compile(r"([A-Za-z_]+)\s*=\s*(.*)$")

def parse_command(line):
    try:
        minute, hour, day, month, weekday, command = line.split(None, 5)
    except ValueError:
        raise CrontabSyntaxError(line)

    # FIXME!
    tz = "US/Eastern"

    return (
        CrontabSchedule(tz, Fields(minute, hour, day, month, weekday)), 
        command
    )
                    

def choose_params(fields):
    is_single = lambda val: (
            val != "*" 
        and len(val) == 1
        and val[0][1] == val[0][0] + 1
        and val[0][2] == 1
    )
    m, h, *_ = fields._Fields__parsed
    # FIXME: Return "hour" or "minute" or "month"?
    return "date" if is_single(m) and is_single(h) else "time"


def parse_crontab(id, lines):
    lines = ( l.strip() for l in lines )
    lines = ( l for l in lines if len(l) > 0 and l[0] != "#" )

    environment = {}
    jobs = []
    for line in lines:
        match = re.match(ENVIRONMENT_REGEX, line)
        if match is not None:
            environment[match.group(1)] = match.group(2)
        else:
            schedule, command = parse_command(line)
            jobs.append(Job(
                job_id      ="{}-{}".format(id, len(jobs)),
                params      =choose_params(schedule.fields),
                schedule    =schedule,
                program     =ShellCommandProgram(command),
            ))

    return environment, jobs


def read_crontab_file(path):
    path = Path(path)
    with open(path, "rt") as file:
        return parse_crontab(path.name, file)


