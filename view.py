#!/home/homero/miniconda3/bin/python
import os
import sys
import re
import numpy as np
import natsort
import argparse
from dateutil.relativedelta import relativedelta
import datetime
from datetime import date, timedelta

txt_format = '.txt'
utf8_encoding = "utf-8"
DATE_FORMAT = "%Y-%m-%d"
# iso_encoding = "ISO-8859-1"

def check_worktimes():  # not used yet
    with open('/home/homero/hd/Dropbox/oxford/journal/2019-5-13.txt', 'r') as f:
        text = f.read()
    arrivals = re.findall('\^A(\d?\d:\d\d)', text)
    leavings = re.findall('\^L(\d?\d:\d\d)', text)
    start = re.findall('\^S(\d?\d:\d\d)', text)
    end = re.findall('\^E(\d?\d:\d\d)', text)
    return arrivals, leavings, start, end

def str_to_relativedelta(str):
    return relativedelta(datetime.datetime.strptime(str, '%H:%M'), datetime.datetime.strptime('0:0', '%H:%M'))


def str_to_timedelta(str):
    tmp_dt = datetime.datetime.strptime(str, "%H:%M")
    return timedelta(hours=tmp_dt.hour, minutes=tmp_dt.minute)


def timedelta_to_str(td):
    return "%d:%02d" % (td.days*24 + td.seconds//3600, ((td.seconds // 60) % 60))


def relativedelta_to_str(relativedeltaobj):
    timeobj = relativedeltaobj+datetime.datetime.strptime('0:0', '%H:%M')
    return '%d:%02d' % (timeobj.hour, timeobj.minute)


def calc_total_work_time(daily_journal):
    """
    Calculates amount of worked hours in the day
    :param daily_journal: 
    :return: dateutil.relativedelta of amount of worked hours
    """
    duration_attribution_list = re.findall('\^T([a-zA-Z0-9_-]+)=(\d?\d:\d\d)', daily_journal)


    attributions = []
    durations = []
    for item in duration_attribution_list:
        attributions.append(item[0])
        durations.append(item[1])

    total_work = relativedelta(seconds=0)
    for dur in durations: 
        total_work += str_to_relativedelta(dur)

    try:
        procrastination_idx = attributions.index('procrastination')
        return total_work - str_to_relativedelta(durations[procrastination_idx])
    except ValueError:
        return total_work


def get_worked_time_for_strdate(strdate):
    """Extract total work time from given date
    :param strdate: data in string format YYYY-MM-DD
    :return work_time
    """
    try: 
        with open(strdate+txt_format, 'r', encoding="utf-8") as f:
            text = f.read().strip()
            work_time = relativedelta_to_str(calc_total_work_time(text))
    except FileNotFoundError as e: 
        work_time = "0:00"

    return work_time


def test_calc_total_work_time():
    text = """
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

    ^A10:25^L11:45
    ^A12:50^E17:30
    ^S18:45^L21:40
    """

    work_time=calc_total_work_time(text)
    ref_work_time=relativedelta(hours=8, minutes=25)
    assert work_time==ref_work_time, 'Error! The amount of hours worked in this day was %s, not %s' % \
                                        (relativedelta_to_str(ref_work_time), relativedelta_to_str(work_time))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('n_files', type=int, nargs='?', help='number of days to be displayed')
    parser.add_argument('-c', '--count', type=int, help='print the number of hours worked in the last "c" days')
    parser.add_argument('-w', '--week', help='show week times', action='store_true')
    parser.add_argument('-t', '--test', help='test application', action='store_true')
    args = parser.parse_args()
    
    all_files = os.listdir()
    
    if args.n_files is None:
        n_files = len(all_files)
    else:
        n_files = args.n_files
    
    if args.test:
        test_calc_total_work_time()
        exit()

    ## old parser begin ##
    # if len(sys.argv)==1:
    #    n_files = len(all_files)
    # elif len(sys.argv)==2:
    #    n_files = int(sys.argv[1])
    # else:
    #     MSG= """ERROR: Wrong number of parameters. Use either no parameters or just one integer as paramater: the number of files to print.
    # USAGE: ./view.py N_FILES)"""
    #     print(MSG)
    #     exit()
    ## old parser end ##

    # all_files.remove('view.py')
    # all_files.remove('this week')
    # all_files.remove('worth-readings')
    # all_files.remove
    count=0
    ordered_files = natsort.humansorted(all_files, reverse=True)

    if args.count:
        n_days = args.count
        today = date.today()
        one_day = timedelta(days=1)
        dt = today - n_days*one_day
        hours = []
        weekend_days = 0
        for i in range(n_days):
            day = dt.strftime(DATE_FORMAT)
            worked_time = get_worked_time_for_strdate(day)
            print(dt, dt.strftime('%a'), worked_time)
            if dt.strftime("%a") in ["Sat", "Sun"]:
                weekend_days+=1

            hours.append(str_to_timedelta(worked_time))
            dt+=one_day
        print("***\nAverage hours worked per working day: %s" % timedelta_to_str(np.sum(hours)/(n_days-weekend_days)))
        print("Total hours worked in these %d days: %s" % (n_days, timedelta_to_str(np.sum(hours))))

        # # example get all days since last monday
        # last_monday = today + timedelta(days=-today.weekday())
        # delta = today - last_monday
        # for i in range(delta.days+1):
        #    print(last_monday+timedelta(days=i))

        # # get date from string
        # datetime.datetime.strptime("2020-01-05", date_format).date()
        # # remove .txt suffix
        # date_file = filename.split('.')[0]
    else:
        for filename in ordered_files:
            if re.match('.*\.txt$', filename):
                with open(filename, 'r', encoding=utf8_encoding) as f:
                # with open(filename, 'r') as f:
                    text = f.read().strip()
                    work_time = relativedelta_to_str(calc_total_work_time(text))
                    print('========================', filename, '- Time Worked -', work_time, '========================\n')
                    print(text)
                    print('\n')
                count+=1
                if count>=n_files:
                    break
