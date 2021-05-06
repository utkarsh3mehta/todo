# ToDo

This application is for companies with multiple teams and teams with multiple members to manage their tasks, to-dos or even shift handovers. I created this application when I was working in a 24x7 support team for my company. We had constant handovers and updates on them.

Do excuse the application if you see "Handover" here and there.

## Features

+ **Corporate scallable**
+ Bootstap based user interface
+ No action more than 2 clicks away
+ Training module for new users to get acquainted with
+ Easily comment on tasks
+ Easily attach files to tasks
+ Icons to show if any task has comments or attachments
+ Resolve any task with just one click
+ Attach multiple files to tasks in one go
+ Add comments to attachments
+ See resolved handovers in the "resolved" section
+ Search any word, phrase within task title, description or even comments

### W.I.P. Features

+ Update tasks and change its team
+ Show comments on display handover modal

### To report any issue, feel free to raise/create an issue on the issues section of this github repositories

## Steps to start the project on your local machine

### Use `py/python` according to your operating system. `py` for windows, `python` for Linux/Unix

1. `py manage.py migrate`
1. `py manage.py createsuperuser`
1. `py manage.py runserver`

+ Access /handover route to access the application
+ Access /admin route to access the admin dashboard for application. Use the account created with `createsuperuser` command
+ Access /handover/test to access a test route. This route can be used to template your custom pages
