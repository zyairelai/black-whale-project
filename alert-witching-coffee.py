#!/bin/python3

import os, requests
from datetime import datetime, timezone

def telegram_bot_sendtext(bot_message):
    bot_token = os.environ.get('TELEGRAM_ALERT_WITCHING_COFFEE')
    chat_id = "@witching_coffee"
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + chat_id + '&parse_mode=html&text=' + bot_message
    response = requests.get(send_text)
    return response.json()

def check_time():
    utc_now = datetime.now(timezone.utc)
    hour = utc_now.hour
    minute = utc_now.minute

    if hour == 4 and 0 <= minute < 10:
        telegram_bot_sendtext("💥 Witching Hour Started 💥") # 4am UTC / 12pm Malaysia
    elif hour == 6 and 0 <= minute < 10:
        telegram_bot_sendtext("☕ Coffee Trade Check 1 ☕") # 6am UTC / 2pm Malaysia
    elif hour == 7 and 0 <= minute < 10:
        telegram_bot_sendtext("☕ Coffee Trade Check 2 ☕") # 7am UTC / 3pm Malaysia
    elif hour == 10 and 0 <= minute < 10:
        telegram_bot_sendtext("💰 Finish your coffee Check 1 💰") # 10am UTC / 6pm Malaysia
    elif hour == 10 and 30 <= minute < 40:
        telegram_bot_sendtext("💰 Finish your coffee Check 2 💰") # 10:30am UTC / 6:30pm Malaysia

    print(str(utc_now))
    print(str(hour) + ":" + str(minute))

check_time()

"""
0 4,6,7 * * * /usr/bin/python3 /home/ubuntu/black-whale-project/alert-witching-coffee.py
0 10 * * * /usr/bin/python3 /home/ubuntu/black-whale-project/alert-witching-coffee.py
30 10 * * * /usr/bin/python3 /home/ubuntu/black-whale-project/alert-witching-coffee.py
"""