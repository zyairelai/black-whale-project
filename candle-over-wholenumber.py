#!/bin/python3

import ccxt, pandas, requests, time, os
from datetime import datetime, timedelta, timezone
from termcolor import colored

def telegram_bot_sendtext(bot_message):
    bot_token = os.environ.get('TELEGRAM_WHOLENUMBER')
    chat_id = "@wholenumbergame"
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + chat_id + '&parse_mode=html&text=' + bot_message
    response = requests.get(send_text)
    return response.json()

# telegram_bot_sendtext("Telegram is working!")

def sleep_until_next_hour():
    current_utc_time = datetime.now(timezone.utc)
    next_target = (current_utc_time + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    sleep_duration = (next_target - current_utc_time).total_seconds()
    print(f"Sleeping until {next_target}")
    time.sleep(sleep_duration)

def get_klines(pair, interval):
    tohlcv_colume = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    return pandas.DataFrame(ccxt.binance().fetch_ohlcv(pair, interval , limit=10), columns=tohlcv_colume)

def heikin_ashi(klines):
    heikin_ashi_df = pandas.DataFrame(index=klines.index.values, columns=['open', 'high', 'low', 'close'])
    heikin_ashi_df['close'] = (klines['open'] + klines['high'] + klines['low'] + klines['close']) / 4

    for i in range(len(klines)):
        if i == 0: heikin_ashi_df.iat[0, 0] = klines['open'].iloc[0]
        else: heikin_ashi_df.iat[i, 0] = (heikin_ashi_df.iat[i-1, 0] + heikin_ashi_df.iat[i-1, 3]) / 2

    heikin_ashi_df.insert(0,'timestamp', klines['timestamp'])
    heikin_ashi_df['high'] = heikin_ashi_df.loc[:, ['open', 'close']].join(klines['high']).max(axis=1)
    heikin_ashi_df['low']  = heikin_ashi_df.loc[:, ['open', 'close']].join(klines['low']).min(axis=1)
    heikin_ashi_df["color"] = heikin_ashi_df.apply(color, axis=1)
    heikin_ashi_df["volume"] = klines["volume"]
    heikin_ashi_df["body"]  = abs(heikin_ashi_df['open'] - heikin_ashi_df['close'])
    heikin_ashi_df['midpoint'] = (heikin_ashi_df['open'] + heikin_ashi_df['close']) / 2
    # heikin_ashi_df['william'] = williams_alligator(heikin_ashi_df)
    return heikin_ashi_df

def williams_alligator(HA):
    william_df = pandas.DataFrame(index=HA.index)
    william_df['close'] = HA['close']
    william_df['Jaw'] = william_df['close'].rolling(window=13).mean().shift(8)
    william_df['Teeth'] = william_df['close'].rolling(window=8).mean().shift(5)
    william_df['Lips'] = william_df['close'].rolling(window=5).mean().shift(3)
    if william_df['Jaw'].iloc[-1] > william_df['Teeth'].iloc[-1] > william_df['Lips'].iloc[-1]: return 'GREEN'
    elif william_df['Jaw'].iloc[-1] < william_df['Teeth'].iloc[-1] < william_df['Lips'].iloc[-1]: return 'RED'
    else: return '-'

def color(HA):
    if HA['open'] < HA['close']: return "GREEN"
    elif HA['open'] > HA['close']: return "RED"
    else: return "INDECISIVE"

def nearest_whole_number(markPrice):
    grid = 1000
    return round(markPrice / grid) * grid

def check_trend(coin):
    pair = coin + "USDT"
    direction = heikin_ashi(get_klines(pair, "3m"))
    # print(direction)

    whole_number = nearest_whole_number(direction['close'].iloc[-1])
    # print(whole_number)

    if direction['color'].iloc[-1] == "GREEN" and \
        direction['open'].iloc[-1] < whole_number and direction['close'].iloc[-1] > whole_number:
        print(colored(str(coin) + " 🥦 BREAKOUT 🥦", "green"))
        telegram_bot_sendtext(str(coin) + " 🥦 BREAKOUT 🥦")
        sleep_until_next_hour()

    elif direction['color'].iloc[-1] == "RED" and \
        direction['open'].iloc[-1] > whole_number and direction['close'].iloc[-1] < whole_number:
        print(colored(str(coin) + " 💥 GRAVITY 💥", "red"))
        telegram_bot_sendtext(str(coin) + " 💥 GRAVITY 💥")
        sleep_until_next_hour()

    else: print("🐺 WAIT 🐺")
    print("Last action executed @ " + datetime.now().strftime("%H:%M:%S") + "\n")

coin = "BTC"
print("\nMonitoring started for " + coin + "\n")

while True:
    check_trend(coin)
    time.sleep(1)
