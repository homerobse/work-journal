#!/home/homero/miniconda3/bin/python
import datetime
from dateutil.relativedelta import relativedelta
import sys

def is_negative(rd: relativedelta) -> bool:
    """Check whether a relativedelta object is negative"""
    try:
        datetime.datetime.min + rd
        return False
    except OverflowError:
        return True


def calc_time_diff(a,b):
    start = datetime.datetime.strptime(a, '%H:%M')
    end = datetime.datetime.strptime(b, '%H:%M')
    
    diff = relativedelta(end, start)
    if is_negative(diff):
        end = end + relativedelta(days=1)
        diff = relativedelta(end, start)

    # print(a,b, "The difference is %d hours %d minutes" % (diff.hours, diff.minutes))
    return diff

def test_calc_time_diff(a,b, ref_result_str):
    result = calc_time_diff(a,b)
    ref_result = relativedelta(hours=int(ref_result_str.split(':')[0]), minutes=int(ref_result_str.split(':')[1]))
    assert result==ref_result, 'Error! %s - %s should be %s, not %s' % (a, b, ref_result_str, '%d:%d'% (result.hours, result.minutes))

# example calculation with times
#  calc_time_diff('10:25', '11:45')+calc_time_diff('12:50', '17:30')+calc_time_diff('18:45', '21:40')-relativedelta(hours=5, minutes=50)


def test_several_cases():
    a = '23:00'
    b = '23:55'
    ref_result_str = '0:55'
    test_calc_time_diff(a,b,ref_result_str)

    a = '23:30'
    b = '1:58'
    ref_result_str = '2:28'
    test_calc_time_diff(a,b,ref_result_str)

    a = '23:00'
    b = '3:15'
    ref_result_str = '4:15'
    test_calc_time_diff(a,b,ref_result_str)

    a = '13:00'
    b = '12:15'
    ref_result_str = '23:15'
    test_calc_time_diff(a,b,ref_result_str)

    a = '23:00'
    b = '00:15'
    ref_result_str = '1:15'
    test_calc_time_diff(a,b,ref_result_str)

    a = '22:00'
    b = '00:00'
    ref_result_str = '2:00'
    test_calc_time_diff(a,b,ref_result_str)

    a = '22:01'
    b = '00:00'
    ref_result_str = '1:59'
    test_calc_time_diff(a,b,ref_result_str)

test_several_cases()

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("""Insufficient parameters. Please adopt the following usage: ./time_calc.py <time_start> <time_end>""")
        exit()
    result = calc_time_diff(sys.argv[1], sys.argv[2])
    # print(result)
    print("The difference is %d hours %d minutes" % (result.hours, result.minutes))


