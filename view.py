#!/home/homero/software/miniconda3/bin/python
import os
from os import path
from os.path import dirname, abspath, join
import sys
import re
import calendar

import numpy as np
import natsort
import argparse
import datetime
from datetime import timedelta

WJ_FOLDER = dirname(abspath(__file__))  # Work-Journal project folder
JOURNALS_FOLDER = dirname(WJ_FOLDER)  # parent folder where daily journals are stored in .txt format
TXT_FORMAT = '.txt'
UTF8_ENCODING = "utf-8"
# iso_encoding = "ISO-8859-1"
DATE_FORMAT_YMD = "%Y-%m-%d"
DATE_FORMAT_MD = "%m-%d"

try:
    with open(join(WJ_FOLDER, "vacations"), "r") as f:
        VACATIONS = f.read().splitlines()
except FileNotFoundError as e:
    print("Please create a vacations text file.")
    exit()
try:
    with open(join(WJ_FOLDER, "holidays"), "r") as f:
        HOLIDAYS = f.read().splitlines()
except FileNotFoundError as e:
    print("Please create a holidays text file.")
    exit()


EXAMPLE_JOURNAL = """
    * write down reward modulated learning rule and include sketch figure
    * generate plot showing result of reward modulated learning for all layers
    * finish neurodynamics chapter 3 -> partially done, read just section 3.3

    done:
    * testing markdown desktop editor vnote
    * read neurodynamics section 3.3
    * improve Cell class to get cell id using cell_session_id and folder name (fname)s
    * trying to understand why the position tracking from mat doesn't match the whl file. And the starting value for the plot isn't matching the one intended

    ^Tprocrastination=0:30
    ^Treading=5:20
    ^Tufrn=3:05
    ^Tpersonal=0:10
    ^Tmaiseducacao=0:15

    ^A10:25^L11:45
    ^A12:50^E17:30
    ^S18:45^L22:15
    """


def check_worktimes(text):  # not used yet
    arrivals = re.findall('\^A(\d?\d:\d\d)', text)
    leavings = re.findall('\^L(\d?\d:\d\d)', text)
    starts = re.findall('\^S(\d?\d:\d\d)', text)
    ends = re.findall('\^E(\d?\d:\d\d)', text)
    return arrivals, leavings, starts, ends


def str_to_timedelta(time_str):
    """
    Convert time from string format to timedelta
    :param time_str: time string in format hours:minutes. E.g. 198:55, or 4:32
    :return: timedelta object
    """
    return timedelta(seconds=int(time_str.split(":")[0]) * 3600 + int(time_str.split(":")[1]) * 60)


def timedelta_to_str(td):
    """
    Convert from timedelta to string of format hours:minutes
    :param td: timedelta
    :return: (str) hours:minutes
    """
    # the minutes are calculated by getting the quotient of how many total minutes there are, and then getting just the remainder in the division by
    # 60, because the hours are already accounted in the first term of the ordinate pair
    return "%d:%02d" % (td.days*24 + td.seconds//3600, ((td.seconds // 60) % 60))


def get_attribution_duration(attributions, durations, item):
    """
    Get the duration of an attribution item
    :param attributions: list of tags
    :param duration: list of str durations of each attribution
    :param (str) item: the specific attribution for which the duration should be extracted
    :return: (str) duration in format HH:MM
    """
    try:
        att_idx = attributions.index(item)
        duration = str_to_timedelta(durations[att_idx])
    except ValueError:
        duration = str_to_timedelta("0:00")
    return duration


def calc_total_work_time(daily_journal):
    """
    Calculates amount of worked hours in the day
    :param daily_journal: daily journal string containing text (todo's and done) and the time tags (e.g. ^Tuniversity_project=2:00, ^S8:30, ^E18:00, etc.)
    :return: timedelta of amount of worked hours
    """
    # TODO: include try/except for when the file does not contain the time tags below.
    duration_attribution_list = re.findall('\^T([a-zA-Z0-9_-]+)=(\d?\d:\d\d)', daily_journal)  #TODO: include format 2.5 (for 2.5 hours = 2:30)


    attributions = []
    durations = []
    for item in duration_attribution_list:
        attributions.append(item[0])
        durations.append(item[1])

    total_work = timedelta(seconds=0)
    for dur in durations:
        total_work += str_to_timedelta(dur)


    procrastination_dur = get_attribution_duration(attributions, durations, "procrastination")
    personal_dur = get_attribution_duration(attributions, durations, "personal")
    maiseducacao_dur = get_attribution_duration(attributions, durations, "maiseducacao")
    return total_work - procrastination_dur - personal_dur - maiseducacao_dur


def get_worked_time_for_strdate(strdate):
    """Extract total work time from given date
    :param strdate: data in string format YYYY-MM-DD
    :return (str) work_time (format HH:MM)
    """
    try:
        with open(join(JOURNALS_FOLDER, strdate+TXT_FORMAT), 'r', encoding=UTF8_ENCODING) as f:
            text = f.read().strip()
            work_time = timedelta_to_str(calc_total_work_time(text))
    except FileNotFoundError as e:
        work_time = "0:00"

    return work_time


def get_month_range(year, month):
    """Get list of all dates in a month
    :param (int) year: YYYY
    :param (int) month: MM
    :return (list of datetimes) month_dates
    """
    nb_days = calendar.monthrange(year, month)[1]
    return [datetime.date(year, month, day) for day in range(1, nb_days+1)]


def is_day_off(date):
    """ Check if given date is day off (i.e. weekend, holiday or vacation).
    :param (datetime.date) date
    :return (bool) True if it is a date of a day-off, False if not.
    """
    return date.strftime("%a") in ["Sat", "Sun"] or date.strftime(DATE_FORMAT_YMD) in VACATIONS or date.strftime(DATE_FORMAT_MD) in HOLIDAYS


def calc_worked_time_in_date_range(date_range):
    """
    Note: *27/Feb/2019 was when I first started taking note of the amount of hours dedicated to each activity
    * 14/Mar/2019 was when I first started taking note of the hours of start and end of work
    :param date_range: list of dates
    :return (total worked hours, average worked hours per working day,
        reference number of hours for 8h working days)
    """
    hours=[]
    off_days = 0
    one_day = timedelta(days=1)
    for dt in date_range:
        if is_day_off(dt):
            off_days+=1

        day = dt.strftime(DATE_FORMAT_YMD)
        worked_time = get_worked_time_for_strdate(day)
        hours.append(str_to_timedelta(worked_time))
        dt+=one_day
    n_working_days = len(date_range)-off_days
    if n_working_days == 0:
        n_working_days = 0.01
    return timedelta_to_str(np.sum(hours)), timedelta_to_str(np.sum(hours)/n_working_days), \
        n_working_days*8


def get_nth_prev_month(curr_yr, curr_mn, nb_mn):
    """Return `(year, month)` correspondent to `nb_mn` months before the `(curr_yr, curr_mn)` given
    :param curr_yr: current year
    :param curr_mn: current month
    :param nb_mn: number of months
    :return (year, month)
    """
    tmp_mn = curr_mn - nb_mn - 1
    q = tmp_mn // 12
    r = tmp_mn % 12
    mn = 1 + r
    yr = curr_yr
    if q < 0:
        yr = curr_yr + q
        mn = 1 + r
    return yr, mn

### tests

def test_get_nth_prev_month():
    curr_yr = 2020
    curr_mn = 6
    nb_mn = 2
    ref = (2020, 4)
    test = get_nth_prev_month(curr_yr, curr_mn, nb_mn)
    assert get_nth_prev_month(curr_yr, curr_mn, nb_mn) == ref, \
        f"Error. {nb_mn} months before ({curr_yr}, {curr_mn}) should be {ref} not {test}"

    curr_yr = 2020
    curr_mn = 6
    nb_mn = 6
    ref = (2019, 12)
    test = get_nth_prev_month(curr_yr, curr_mn, nb_mn)
    assert get_nth_prev_month(curr_yr, curr_mn, nb_mn) == ref, \
        f"Error. {nb_mn} months before ({curr_yr}, {curr_mn}) should be {ref} not {test}"

    curr_yr = 2020
    curr_mn = 6
    nb_mn = 19
    ref = (2018, 11)
    test = get_nth_prev_month(curr_yr, curr_mn, nb_mn)
    assert get_nth_prev_month(curr_yr, curr_mn, nb_mn) == ref, \
        f"Error. {nb_mn} months before ({curr_yr}, {curr_mn}) should be {ref} not {test}"


def test_calc_total_work_time():
    work_time=calc_total_work_time(EXAMPLE_JOURNAL)
    ref_work_time=timedelta(hours=8, minutes=25)
    assert work_time==ref_work_time, 'Error! The amount of hours worked in this day was %s, not %s' % \
                                        (timedelta_to_str(ref_work_time), timedelta_to_str(work_time))



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('n_files', type=int, nargs='?', help='number of days to be displayed')
    parser.add_argument('-c', '--count', type=int, help='print the number of hours worked in the last "c" days')
    parser.add_argument('-m', '--months', type=int, help='print the number of hours worked in the last "m" months')
    parser.add_argument('-w', '--weeks', type=int, help='print the number of hours worked in the last "w" weeks')
    parser.add_argument('-t', '--test', help='run application tests.', action='store_true')
    args = parser.parse_args()

    all_files = os.listdir(JOURNALS_FOLDER)

    if args.n_files is None:
        n_files = len(all_files)  # default is scanning all files
    else:
        n_files = args.n_files

    if args.test:
        test_calc_total_work_time()
        test_get_nth_prev_month()
        print("If nothing was printed above, all tests succeeded")
        exit()

    # all_files.remove('view.py')
    # all_files.remove('this week')
    # all_files.remove('worth-readings')
    # all_files.remove
    count=0
    ordered_files = natsort.humansorted(all_files, reverse=True)

    today = datetime.date.today()
    one_day = timedelta(days=1)
    if args.count:
        n_days = args.count
        dt = today - n_days * one_day + one_day # get datetime object for (n_days - 1) days ago
        hours = []
        off_days = 0
        for _ in range(n_days):
            day = dt.strftime(DATE_FORMAT_YMD)
            worked_time = get_worked_time_for_strdate(day)
            print(dt, dt.strftime('%a'), worked_time)  # YYYY-MM-DD Mon/Tue/... H:MM
            if is_day_off(dt):
                off_days+=1

            hours.append(str_to_timedelta(worked_time))
            dt+=one_day
        n_working_days = n_days-off_days  # TODO: this is imprecise/wrong, as there may be days I did not work when I should have done it. In this case, there would be no files for them, so `n_days` would be less than the number of working days.
        print("***\nAverage hours worked per working day: %s" % timedelta_to_str(np.sum(hours)/n_working_days))
        print("Total hours worked in these %d days: %s" % (n_days, timedelta_to_str(np.sum(hours))))

        # # get date from string
        # datetime.datetime.strptime("2020-01-05", date_format).date()
    elif args.weeks:
        n_weeks = args.weeks
        last_monday = today + timedelta(days=-today.weekday())
        for w in range(n_weeks):
            wk_monday = last_monday + timedelta(days=-7*w)
            print("Mon", wk_monday, "- Sun", wk_monday+timedelta(days=+6))
            wk_range = [(wk_monday + i*one_day) for i in range(7)]  # all days of the week from Monday to Sunday
            wrk_hrs, ref_hrs, avg_per_day = calc_worked_time_in_date_range(wk_range)
            print("%6s (ref %dh). Avg. work/day: %5s" % (wrk_hrs, avg_per_day, ref_hrs))

    elif args.months:
        n_months = args.months
        hours = []
        ref_hours = []
        for m in range(n_months):
            curr_yr_mn = get_nth_prev_month(today.year, today.month, n_months - m - 1)
            print("%d-%02d" % curr_yr_mn)
            month_range = get_month_range(*curr_yr_mn)
            res = calc_worked_time_in_date_range(month_range)

            print("%6s (ref %dh). Avg. work/day: %5s" % (res[0], res[2], res[1]))
            hours.append(str_to_timedelta(res[0]))
            ref_hours.append(res[2])

        print("***")
        print("Actual      ", timedelta_to_str(np.sum(hours)))
        print("REF (8h/day)", np.sum(ref_hours))

    else:
        cumulative_worked_time = timedelta(seconds=0)
        for filename in ordered_files:
            if re.match('.*\.txt$', filename):
                with open(join(JOURNALS_FOLDER, filename), 'r', encoding=UTF8_ENCODING) as f:
                # with open(filename, 'r') as f:
                    text = f.read().strip()
                    work_time = calc_total_work_time(text)
                    cumulative_worked_time += work_time
                    print('========================', filename, '- Time Worked -', timedelta_to_str(work_time), '========================\n')
                    print(text)
                    print('\n')
                count+=1
                if count>=n_files:
                    print('#### TOTAL ACCUMULATED TIME WORKED WAS',  timedelta_to_str(cumulative_worked_time))
                    break
