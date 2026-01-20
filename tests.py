from view import timedelta_to_str, calc_total_work_time, get_nth_prev_month
from datetime import timedelta

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


test_calc_total_work_time()
test_get_nth_prev_month()
print("If nothing was printed above, all tests succeeded")