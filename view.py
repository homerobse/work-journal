#!/home/homero/software/miniconda3/bin/python
import os
from os import path
from os.path import dirname, abspath, join
import sys
import re
import calendar

import numpy as np
from numpy import array, where
import matplotlib.pyplot as plt
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
TAGS = ["ucsd_mattarlab_mouse-maze", "ucsd_sejnowskilab", "ucsd_mattarlab_proj", "ucsd_proj", # research
          "ucsd_class", "ucsd_course", "ucsd_talk",  # courses
          "ucsd_dayanabbott-rg", "ucsd_planning-rg", "ucsd_book-club", "ucsd_yu-jc", # reading group
          "ucsd_admin", "ucsd_email", "ucsd_ta", "ucsd_tech",  # bureaucracy
          "sideways-investigation",
          "rest", "personal", "procrastination", "maiseducacao", "trustedcrowd"]  # non-productive
# Anything not included in the TAGS list will be listed together
#TODO: create a structure that accounts for the different types of work, i.e. has in it some separation like I did in the comments

def read_txt_file_and_exclude_comments(filename):
    with open(filename, "r") as f:
        linelist = f.read().splitlines()
        linelist_wo_comments = []
        for line in linelist:
            if line.startswith("#"):
                pass
            elif "#" in line:
                linelist_wo_comments.append(line.split("#")[0].strip())
            else:
                linelist_wo_comments.append(line.strip())
    return linelist_wo_comments

try:
    VACATIONS = read_txt_file_and_exclude_comments(join(WJ_FOLDER, "vacations"))
except FileNotFoundError as e:
    print("Please create a vacations text file.")
    exit()
try:
    HOLIDAYS = read_txt_file_and_exclude_comments(join(WJ_FOLDER, "holidays"))
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
    ^Ttrustedcrowd=1:00

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


def consolidate_attributions_and_durations_lists(attributions_lists, durations_lists):
    """Consolidates several attributions lists and their corresponding duration 
    lists into a single attribution list and its corresponding duration list
    """
    all_attributions = []
    all_durations = []

    for att_l_idx, att_list in enumerate(attributions_lists):  # att_l_idx indexes the day corresponding to the attribution list
        for it_idx, it in enumerate(att_list):  # for each item in that attribution list
            try:  # if the current item (it) is already in the all_attribution list
                idx = all_attributions.index(it)
                it_dur = durations_lists[att_l_idx][it_idx]
                all_durations[idx] += str_to_timedelta(it_dur)
#                 print("try", all_attributions, all_durations)
            except ValueError:  #  else
                all_attributions.append(it)
                it_dur = durations_lists[att_l_idx][it_idx]
                all_durations.append(str_to_timedelta(it_dur))
#                 print("except", all_attributions, all_durations)

    return all_attributions, all_durations


def get_week_range(day):
    """Get all days in a week. Starting from Monday, ending in Sunday
    :param (datetime.date) day
    :return: list of datetime.dates"""
    str_input_date = day.strftime(DATE_FORMAT_YMD)

    input_date = datetime.datetime.strptime(str_input_date, DATE_FORMAT_YMD).date()
    weeks = 1

    one_day = timedelta(days=1)
    last_monday = input_date + timedelta(days=-input_date.weekday())  # takes the monday before the given date
    for w in range(weeks):
        wk_monday = last_monday + timedelta(days=-7*w)
#         print("Mon", wk_monday, "- Sun", wk_monday+timedelta(days=+6))
        wk_range = [(wk_monday + i*one_day) for i in range(7)] 
    return wk_range


def get_attributions_and_durations(strdate):
    """
    Get attributions and their durations for the given strdate
    strdate: date of the day from which to get the attributions and their durations
    return: attributions list, and a durations list
    """
    try:
        with open(join(JOURNALS_FOLDER, strdate+TXT_FORMAT), 'r', encoding=UTF8_ENCODING) as f:
            daily_journal = f.read().strip()
    except FileNotFoundError as e:
        # if file is not found, return empty lists
        return [],[]

    duration_attribution_list = re.findall('\^T([a-zA-Z0-9_-]+)=(\d?\d:\d\d)', daily_journal)  #TODO: include format 2.5 (for 2.5 hours = 2:30)

    attributions = []
    durations = []                                                                                                                                                                                      
    for item in duration_attribution_list:
        attributions.append(item[0])
        durations.append(item[1])
    
    return attributions, durations


def get_attributions_and_durations_from_range(strdate_range):
    """
    Get week for which day `dt` (datetime.date) belongs and return consolidated attributions and corresponding durations
    :param strdate_range: list of dates
    :return: atts: list of attributions 
             durs_in_h (list of float): duration in hours
    """
    attributions_lists = []
    durations_lists = []
    for day in str_wk_range:
        attributions, durations = get_attributions_and_durations(day)
        attributions_lists.append(attributions)
        durations_lists.append(durations)
    atts, durs = consolidate_attributions_and_durations_lists(attributions_lists, durations_lists)
    durs_in_h = array([dur.seconds/3600 for dur in durs])
    return atts, durs_in_h

    
def plot_wk_all_activities(atts, durs_in_h, str_monday, str_sunday):
    plt.figure(figsize=(15,5))
    plt.bar(range(len(durs_in_h)), durs_in_h, tick_label=atts)
    plt.xticks(rotation=-45, ha="left");
    plt.ylabel("Hours")
    str_monday = str_wk_range[0]
    str_sunday = str_wk_range[-1]
    plt.title("Week Mon %s - Sun %s: %.1fh logged" % (str_monday, str_sunday, sum(durs_in_h)))
    plt.tight_layout()
    return plt.gcf(), plt.gca()


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
    trustedcrowd_dur = get_attribution_duration(attributions, durations, "trustedcrowd")
    return total_work - procrastination_dur - personal_dur - maiseducacao_dur - trustedcrowd_dur


def aggregate_att_hours_and_plot(tags, atts, durs_in_h):
    tag_durs = []
    for tag in tags:  # for each tag search for it in attributions, then sum the tag's duration
    #     print(tag)
        match_indices = []
        for i_att, att in enumerate(atts):  # TODO: rename atts to atts_in_date_range
            match_indices.append(i_att) if re.search(tag, att) else None
        match_indices = array(match_indices)
    #     print(match_indices)

        if len(match_indices)>0:
            tag_durs.append(sum(durs_in_h[match_indices]))  # sum all attribution durations of attributions matching current tag
        else:
            tag_durs.append(0)

    # others (any attributions not listed in tags)
    others = []
    others_durs = []
    for i_att, att in enumerate(atts):  # sum durations for all other tags
        no_matching_tag = True
        for tag in tags:  # check if there is a tag that matches the current attribution #TODO: this is not efficient, since the same search has been done above. Would be better to just use this order of loop (first on atts then on tags)
            if re.search(tag, att):
                no_matching_tag = False
        if no_matching_tag:
            others.append(att)
            others_durs.append(durs_in_h[i_att])

    # print(others)
    # print(others_durs)

    #  remove bars of items with zero hours
    non_zero_idxs = where(array(tag_durs)!=0)
    non_zero_tags = array(tags)[non_zero_idxs]
    non_zero_durs = array(tag_durs)[non_zero_idxs]

    # match_indices#, tag_durs
    plt.figure(figsize=(15,5))
    plt.bar(range(len(non_zero_tags)+1), list(non_zero_durs)+[sum(others_durs)], tick_label=list(non_zero_tags)+[str(others)])
    # plt.bar(range(len(tag_durs)+1), [dur for dur in tag_durs]+[sum(others_durs)], tick_label=TAGS+[str(others)])
    plt.xticks(rotation=-45, ha="left");
    plt.ylabel("Hours")
    str_monday = str_wk_range[0]
    str_sunday = str_wk_range[-1]
    # plt.title("Week Mon %s - Sun %s" % (str_monday, str_sunday))
    plt.title("Week Mon %s - Sun %s: %.1fh logged" % (str_monday, str_sunday, sum(durs_in_h)))
    plt.tight_layout()


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
    parser.add_argument('-p', '--plot', help='plot all activities of the current week.', action='store_true')
    parser.add_argument('-g', '--group', help='plot all activities of the current week grouped by tags.', action='store_true')
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
    elif args.group or args.plot:
        target_day = datetime.date.today()
        str_wk_range = [str(day) for day in get_week_range(target_day)]
        atts, durs_in_h = get_attributions_and_durations_from_range(str_wk_range)
        
        if args.group: aggregate_att_hours_and_plot(TAGS, atts, durs_in_h)
        else: plot_wk_all_activities(atts, durs_in_h, str_wk_range[0], str_wk_range[-1])
        plt.show()
    else:
        count=0
        cumulative_worked_time = timedelta(seconds=0)
        ordered_files = natsort.humansorted(all_files, reverse=True)
        for filename in ordered_files:
            if re.match('.*\.txt$', filename):
                with open(join(JOURNALS_FOLDER, filename), 'r', encoding=UTF8_ENCODING) as f:
                # with open(filename, 'r') as f:
                    text = f.read().strip()
                    work_time = calc_total_work_time(text)
                    cumulative_worked_time += work_time
                    str_date = filename.split(".")[0]
                    dt = datetime.datetime.strptime(str_date,"%Y-%m-%d").date()
                    print('========================', dt.strftime('%a'), str_date, '- Time Worked -', timedelta_to_str(work_time), '========================\n')
                    print(text)
                    print('\n')
                count+=1
                if count>=n_files:
                    print('#### TOTAL ACCUMULATED TIME WORKED WAS',  timedelta_to_str(cumulative_worked_time))
                    break
