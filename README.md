
# What is it
This script find calendar invites and cross references them against the spam folder. If it finds one it deletes it.

# How it works

I use the gmail api and the calendar api. The credentials for those are not included so you will need to get your credentials.

# How to run it

:shrug: After getting credentials run `python start.py`. It should open a browser/give you a link to authenticate and generate the token.pickle file.

# Why

I get email spam that has calendar invites which then show up in my calendar. Now I can run this as a cron job and avoid dealing with it.
