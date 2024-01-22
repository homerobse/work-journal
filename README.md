# Work Journal

This is a command-line interface (CLI) tool written in Python to help visualize sequentially text files where I keep my work journals. They contain the goals for the day and which of them were executed. For the executed goals, I often include a description of what I did. 

Importantly, there are also functionalities to keep track of the time spent on different task categories. It is possible to see the total amount of hours worked per day, per week or per month. Whenever they are shown, they are compared to a reference of a 8h-workday.
It is also possible to add vacations and holidays in the corresponding `vacations` and `holidays` files. The days in these files will not be counted when calculating the reference of the amount of hours that should be worked to reach the 8h-workday (but the hours hours worked on those days *will* be counted towards meeting the reference).

## How to run

usage: view.py [-h] [-c COUNT] [-m MONTHS] [-w WEEKS] [-t] [-p] [-g] [n_files]

positional arguments:
  n_files               number of days to be displayed

optional arguments:
  -h, --help            show this help message and exit
  -c COUNT, --count COUNT
                        print the number of hours worked in the last "c" days
  -m MONTHS, --months MONTHS
                        print the number of hours worked in the last "m" months
  -w WEEKS, --weeks WEEKS
                        print the number of hours worked in the last "w" weeks
  -t, --test            run application tests.
  -p, --plot            plot all activities of the current week.
  -g, --group           plot all activities of the current week grouped by tags.

## Example runs
`$ python view.py -c 7`

Calculates worked hours for the last 7 days.

![](example-run-day-hours.png)

`$ python view.py -w 7`

Calculates worked hours for the last 7 weeks.

![](example-run-week-hours.png)

## TODO

* enable personal subcategories
* enable counting personal hours
