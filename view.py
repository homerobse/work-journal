#!/home/homero/software/miniconda3/bin/python
import os
from os import path
from os.path import dirname, abspath, join
import sys
import re
import calendar

import numpy as np
from numpy import array, where, logical_or
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.ticker import MultipleLocator
matplotlib.use( 'tkagg')
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
TIME_FORMAT_HM = "%H:%M"
# Use the research list to test if activity is research
RESEARCH_TAGS = ['ucsd_mattarlab_seqs', 'ucsd_mattarlab_proj','ucsd_proj', 'ucsd_reading-proj',
        'ucsd_jerniganlab_mixture', 'ucsd_cmiglab_abcd', 'ucsd_jerniganlab_proj',
        'ucsd_sejnowskilab_recirculation', 'ucsd_sejnowskilab_esn', 'ucsd_sejnowskilab_proj',
        'ucsd_sejnowskilab_reading', 'ucsd_rotation',
        'ucsd_course_cogs205_proj',
        'ucsd_mattarlab_mouse-maze', 'ucsd_mattarlab_maze', 'ucsd_mouse-maze',
        'ucsd_mattarlab_ti', 'oxford_ti', 'oxford_ti-draft', 'oxford_proj', 'oxford_paper',
        'ucsd_neuromllab_metrics', 'ucsd_neuromllab_dim',
        'funding', 'dissertation',  'ucsd_advancement', 'ucsd_research', 'thesis',
        'phd-applications', 'applications', 'ucsd_mattarlab_peer-review']
READING_GROUP_TAGS = ["ucsd_dayanabbott-rg", "ucsd_planning-rg", "planning-rg", "ucsd_book-club", "ucsd_yu-jc",
                      "ucsd_neurotheory-jc", "jotun-rg", "jotun-jc", "ucsd_tem-rg", "bishop-rg", "ucsd_hpc-rg",
                      "ucsd_rl-book", "reading_neuronal-dynamics", "journal-club", "ucsd_journal-club",
                      "ucsd_jc", "bookclub", "ucsd_jerniganlab_journal-club"]
# TODO: should I add "reading"? check what are the reading TAGS that exist and if they are about reading group or general study. 
# Also, will it be a problem that reading_neuronal-dynamics is a subtag of reading?
STUDY_TAGS = READING_GROUP_TAGS + ['ucsd_class', 'ucsd_course', 'literature_scan',
                'literature_reading', 'literature_meeting',
                'talk', 'ufrn_talk', 'ucsd_talk',
                'ucsd_reading',
                'sideways-investigation', 'ucsd_sideways-investigation', 'sideways-investigation',
                'ucsd_mattarlab_lab-meeting', 'ucsd_jerniganlab_lab-meeting', 'ucsd_lab-meeting',
                'ucsd_neuromllab_lab-meeting',
                'ucsd_bazhenovlab_lab-meeting', 'ucsd_mattarlab_meeting', 'ucsd_mattarlab_luke', 
                'ucsd_sejnowskilab_lab-meeting', 'conference_sfn', 'ucsd_writinghub',
                'ucsd_sejnowskilab_meeting', 'ucsd_jerniganlab_meeting']
# 'ucsd_mattarlab': not sure how to cover a tag that is a parent tag for another one (ucsd_mattarlab_seqs) that I already count elsewhere]
ADMIN_TAGS = ["ucsd_admin", "ucsd_email", "oxford_paperwork", "oxford_email", "admin", 
                "ucsd_paperwork", "organization", "ucsd_visa", "msg"]
TAGS = RESEARCH_TAGS + STUDY_TAGS + ADMIN_TAGS + ["ucsd_ta", "ucsd_tech",
          "rest", "personal", "procrastination", "maiseducacao", "trustedcrowd"]  # non-work related
# Anything not included in the TAGS list will be listed together as "Other". Check code that separate worked time into categories

def read_txt_file_and_exclude_comments(filename):
    with open(filename, "r") as f:
        linelist = f.read().splitlines()
        linelist_wo_comments = []
        for line in linelist:
            if line.startswith("#"):
                pass
            elif "#" in line:  # ignores everything after # symbol
                linelist_wo_comments.append(line.split("#")[0].strip())
            else:
                linelist_wo_comments.append(line.strip())
    return linelist_wo_comments

try:
    VACATIONS = read_txt_file_and_exclude_comments(join(WJ_FOLDER, "vacations.txt"))
except FileNotFoundError as e:
    print("Please create a vacations text file.")
    exit()
try:
    HOLIDAYS = read_txt_file_and_exclude_comments(join(WJ_FOLDER, "holidays.txt"))
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
#     arrivals = re.findall(r'\^A(\d?\d:\d\d)', text)
#     leavings = re.findall(r'\^L(\d?\d:\d\d)', text)
#     starts = re.findall(r'\^S(\d?\d:\d\d)', text)
#     ends = re.findall(r'\^E(\d?\d:\d\d)', text)
#     return arrivals, leavings, starts, ends
    starts = re.findall(r"\^[SA](\d?\d:\d\d)", text)
    ends = re.findall(r"\^[EL](\d?\d:\d\d)", text)
    return starts, ends


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


def timedelta_to_float_hours(td):
    return td.days*24 + td.seconds/3600


def get_attribution_duration(attributions, durations, item):
    """
    Get the duration of an attribution item
    :param attributions: list of tags
    :param durations: list of str durations of each attribution
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
        wk_range = [(wk_monday + i*one_day) for i in range(7)] # all days of the week from Monday to Sunday
    return wk_range


def get_attributions_and_durations(strdate):
    """
    Get attributions and their durations for the given strdate
    :param strdate: date of the day from which to get the attributions and their durations
    :return: attributions list, and a durations list
    """
    try:
        with open(join(JOURNALS_FOLDER, strdate+TXT_FORMAT), 'r', encoding=UTF8_ENCODING) as f:
            daily_journal = f.read().strip()
    except FileNotFoundError as e:
        # if file is not found, return empty lists
        return [],[]

    duration_attribution_list = re.findall(r'\^T([a-zA-Z0-9_-]+)=(\d?\d:\d\d)', daily_journal)  #TODO: include format 2.5 (for 2.5 hours = 2:30)

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
    for day in strdate_range:
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
    plt.title("Week Mon %s - Sun %s: %.1fh logged" % (str_monday, str_sunday, sum(durs_in_h)))
    plt.gca().yaxis.set_major_locator(MultipleLocator(1))
    plt.gca().yaxis.set_minor_locator(MultipleLocator(.25))
    plt.grid(axis="y")
    plt.gca().set_axisbelow(True)
    plt.tight_layout()
    return plt.gcf(), plt.gca()


def calc_total_work_time(daily_journal):
    """
    Calculates amount of worked hours in the day
    :param daily_journal: daily journal string containing text (todo's and done) and the time tags (e.g. ^Tuniversity_project=2:00, ^S8:30, ^E18:00, etc.)
    :return: timedelta of amount of worked hours
    """
    # TODO: include try/except for when the file does not contain the time tags below.
    duration_attribution_list = re.findall(r'\^T([a-zA-Z0-9_-]+)=(\d?\d:\d\d)', daily_journal)  #TODO: include format 2.5 (for 2.5 hours = 2:30)


    attributions = []
    durations = []
    for item in duration_attribution_list:
        attributions.append(item[0])
        durations.append(item[1])

    total_work = timedelta(seconds=0)
    for dur in durations:
        total_work += str_to_timedelta(dur)

    #todo: enable personal and procrastination subcategories despite not being counted
    procrastination_dur = get_attribution_duration(attributions, durations, "procrastination")
    personal_dur = get_attribution_duration(attributions, durations, "personal")
    maiseducacao_dur = get_attribution_duration(attributions, durations, "maiseducacao")
    trustedcrowd_dur = get_attribution_duration(attributions, durations, "trustedcrowd")
    return total_work - procrastination_dur - personal_dur - maiseducacao_dur - trustedcrowd_dur


def aggregate_att_hours(tags, atts_in_date_range, durs_in_h):
    """
    Args:
        tags: (list of str) list of categories
        atts_in_date_range: (list of str) attributions
        durs_in_h: (ndarray) durations worked on each of the attributions  #TODO: check if it is array or list
    Returns:
        all_tags (list of str),
        all_durs (list of float?),
        others (list of str)
    """
    others = []  # others (any attributions not listed in tags)
    others_durs = []
    tag_durs = np.zeros(len(tags))
    for i_att, att in enumerate(atts_in_date_range):  # sum durations for all other tags
        no_matching_tag = True
        for i_tag, tag in enumerate(tags):  # check if there is a tag that matches the current attribution #TODO: this is not efficient, since the same search has been done above. Would be better to just use this order of loop (first on atts then on tags)
            regex = "(%s)_|(%s)$" % (tag, tag)   # match if it is followed by an underscore or nothing else ($ represents the end of the string)
            if re.match(regex, att):
                no_matching_tag = False
                tag_durs[i_tag]+=durs_in_h[i_att]
                break

        if no_matching_tag:  # append to others if there's no match for the current att after checking all tags
            others.append(att)
            others_durs.append(durs_in_h[i_att])

    # print(others)
    # print(others_durs)

    #  remove bars of items with zero hours
    non_zero_idxs = where(array(tag_durs)!=0)
    non_zero_tags = array(tags)[non_zero_idxs]
    non_zero_durs = array(tag_durs)[non_zero_idxs]

    all_durs = list(non_zero_durs)+[sum(others_durs)]
    all_tags = list(non_zero_tags)+["Others"]

    return all_tags, all_durs, others


def plot_aggregate_att_hours(all_tags, all_durs, others_labels, figtitle):
    plt.figure(figsize=(15,5))
    positions = range(len(all_tags))
    plt.bar(positions, all_durs, tick_label=all_tags)
    # plt.bar(range(len(tag_durs)+1), [dur for dur in tag_durs]+[sum(others_durs)], tick_label=TAGS+[str(others)])
    plt.xticks(rotation=-45, ha="left")
    plt.xlabel("Others: %s" % str(others_labels))
    plt.ylabel("Hours")
    plt.title(figtitle)
    plt.gca().yaxis.set_major_locator(MultipleLocator(1))
    plt.gca().yaxis.set_minor_locator(MultipleLocator(.25))
    plt.grid(axis="y")
    plt.gca().set_axisbelow(True)
    plt.tight_layout()
    return plt.gcf(), plt.gca()


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
    """Check if given date is day off (i.e. weekend, holiday or vacation).
    :param (datetime.date) date
    :return (bool) True if it is a date of a day-off, False if not.
    """
    return date.strftime("%a") in ["Sat", "Sun"] or date.strftime(DATE_FORMAT_YMD) in VACATIONS or date.strftime(DATE_FORMAT_YMD) in HOLIDAYS


def calc_worked_time_in_date_range(date_range):
    """
    Note: *27/Feb/2019 was when I first started taking note of the amount of hours dedicated to each activity
    * 14/Mar/2019 was when I first started taking note of the times of the day in which I start and end work
    :param date_range: list of dates
    :return
        (total worked hours,
        average worked hours per working day,
        reference number of hours for 8h working days)
    """
    hours=[]
    off_days = 0
    one_day = timedelta(days=1)
    for dt in date_range:
        if is_day_off(dt):
            off_days+=1
            #print(dt, dt.strftime("%a"))

        day = dt.strftime(DATE_FORMAT_YMD)
        worked_time = get_worked_time_for_strdate(day)
        hours.append(str_to_timedelta(worked_time))
        dt+=one_day
    #print("off_days=", off_days)
    n_working_days = len(date_range)-off_days
    if n_working_days == 0:
        n_working_days = 0.01  # avoid division by zero

    # TODO: add research hours calculation
    # atts, durs_in_h = get_attributions_and_durations_from_range(str_period_range)
    # all_tags, all_durs, others_labels = aggregate_att_hours(TAGS, atts, durs_in_h, figtitle)

    return timedelta_to_str(np.sum(hours)), timedelta_to_str(np.sum(hours)/n_working_days), \
        n_working_days*8


def get_nth_prev_month(curr_yr, curr_month, n_months):
    """Return `int, int = (year, month)` correspondent to `n_months` months before the
    `(curr_yr, curr_month)` given.
    :param curr_yr: current year
    :param curr_month: current month
    :param n_months: number of months
    :return (year, month)
    """
    tmp_month = curr_month - n_months - 1
    q = tmp_month // 12  # quotient
    r = tmp_month % 12  # remainder
    month = 1 + r
    yr = curr_yr
    if q < 0:
        yr = curr_yr + q
    return yr, month

### tests

def test_get_nth_prev_month():
    curr_yr = 2020
    curr_month = 6
    n_months = 2
    ref = (2020, 4)
    test = get_nth_prev_month(curr_yr, curr_month, n_months)
    assert get_nth_prev_month(curr_yr, curr_month, n_months) == ref, \
        f"Error. {n_months} months before ({curr_yr}, {curr_month}) should be {ref} not {test}"

    curr_yr = 2020
    curr_month = 6
    n_months = 6
    ref = (2019, 12)
    test = get_nth_prev_month(curr_yr, curr_month, n_months)
    assert get_nth_prev_month(curr_yr, curr_month, n_months) == ref, \
        f"Error. {n_months} months before ({curr_yr}, {curr_month}) should be {ref} not {test}"

    curr_yr = 2020
    curr_month = 6
    n_months = 19
    ref = (2018, 11)
    test = get_nth_prev_month(curr_yr, curr_month, n_months)
    assert get_nth_prev_month(curr_yr, curr_month, n_months) == ref, \
        f"Error. {n_months} months before ({curr_yr}, {curr_month}) should be {ref} not {test}"


def test_calc_total_work_time():
    work_time=calc_total_work_time(EXAMPLE_JOURNAL)
    ref_work_time=timedelta(hours=8, minutes=25)
    assert work_time==ref_work_time, 'Error! The amount of hours worked in this day was %s, not %s' % \
                                        (timedelta_to_str(ref_work_time), timedelta_to_str(work_time))


def calc_research_hours(all_durs, all_tags):
    """
    :param all_durs: (ndarray)
    :param all_tags: (ndarray)
    :return
    """
    return all_durs[logical_or.reduce(array([all_tags == research_tag for research_tag in RESEARCH_TAGS]))].sum()

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
    print(f"Time now: {datetime.datetime.now().strftime(TIME_FORMAT_HM)}")
    one_day = timedelta(days=1)
    if args.count:
        n_days = args.count
        dt = today - (n_days-1) * one_day  # get datetime object for (n_days - 1) days ago (i.e. start from today and goes back in time)
        hours = []
        off_days = 0
        str_period_range = []
        period_range = []
        # get worked time for each day and set variables used for calculating average daily work
        for _ in range(n_days):
            day_str = dt.strftime(DATE_FORMAT_YMD)  # e.g. '2024-05-01'
            str_period_range.append(day_str)  # used for plotting below
            period_range.append(dt)  # used for plotting below
            worked_time = get_worked_time_for_strdate(day_str)
            print(dt, dt.strftime('%a'), worked_time)  # YYYY-MM-DD Mon/Tue/... H:MM
            if is_day_off(dt):
                off_days+=1

            hours.append(str_to_timedelta(worked_time))
            dt+=one_day
        n_working_days = n_days-off_days  # TODO: this is imprecise/wrong, as there may be days I did not work when I should have done it. In this case, there would be no files for them, so `n_days` would be less than the number of working days.
        print("***\nAverage hours worked per working day: %s" % timedelta_to_str(np.sum(hours)/n_working_days))
        print("Total hours worked in these %d days: %s" % (n_days, timedelta_to_str(np.sum(hours))))

        # and plot aggregate plot for the week
        atts, durs_in_h = get_attributions_and_durations_from_range(str_period_range)
        figtitle = "Period from %s %s to %s %s: %.1fh logged" % (period_range[0].strftime('%a'), 
            str_period_range[0], period_range[-1].strftime('%a'), str_period_range[-1], sum(durs_in_h))
        all_tags, all_durs, others_labels = aggregate_att_hours(TAGS, atts, durs_in_h)
        plot_aggregate_att_hours(all_tags, all_durs, others_labels, figtitle)

        h_research = calc_research_hours(array(all_durs), array(all_tags))

        pct_research = h_research/timedelta_to_float_hours(np.sum(hours))
        print(f"Research: {h_research:.1f}h | {100*pct_research:.0f}%")
        plt.show()

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
        for m in range(n_months):  # get each month starting from that oldest to the current one
            curr_yr_month = get_nth_prev_month(today.year, today.month, n_months - 1 - m)
            print("%d-%02d" % curr_yr_month)
            month_range = get_month_range(*curr_yr_month)
            res = calc_worked_time_in_date_range(month_range)

            print("%6s (ref %dh). Avg. work/day: %5s" % (res[0], res[2], res[1]))
            hours.append(str_to_timedelta(res[0]))
            ref_hours.append(res[2])

        print("***")
        print("Actual                   |", timedelta_to_str(np.sum(hours)))
        print("REF (8h per working day) |", np.sum(ref_hours))
    elif args.group or args.plot:
        target_day = datetime.date.today()
        str_wk_range = [str(day) for day in get_week_range(target_day)]
        atts, durs_in_h = get_attributions_and_durations_from_range(str_wk_range)

        figtitle = "Week Mon %s - Sun %s: %.1fh logged" % (str_wk_range[0], str_wk_range[-1], sum(durs_in_h))
        if args.group:
            all_tags, all_durs, others_labels = aggregate_att_hours(TAGS, atts, durs_in_h)
            plot_aggregate_att_hours(all_tags, all_durs, others_labels, figtitle)
        else: plot_wk_all_activities(atts, durs_in_h, str_wk_range[0], str_wk_range[-1])
        plt.show()
    else:
        count=0
        cumulative_worked_time = timedelta(seconds=0)
        ordered_files = natsort.humansorted(all_files, reverse=True)
        for filename in ordered_files:
            if re.match(r'.*\.txt$', filename):
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
