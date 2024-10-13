#!/bin/python3

import ccxt, pandas, requests, time, os
from termcolor import colored
from datetime import datetime, timedelta, timezone

def telegram_bot_sendtext(bot_message):
    bot_token = os.environ.get('TELEGRAM_LIVERMORE')
    chat_id = "@swinglivermore"
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + chat_id + '&parse_mode=html&text=' + bot_message
    response = requests.get(send_text)
    return response.json()

def get_klines(coin, interval):
    pair = coin + "/USDT"
    tohlcv_colume = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    return pandas.DataFrame(ccxt.bybit().fetch_ohlcv(pair, interval , limit=31), columns=tohlcv_colume)

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
    heikin_ashi_df["body"]  = abs(heikin_ashi_df['open'] - heikin_ashi_df['close'])

    previous_candles = 2
    heikin_ashi_df['higher'] = heikin_ashi_df['close'] > heikin_ashi_df['close'].rolling(window=previous_candles).max().shift(1)
    heikin_ashi_df['lower'] = heikin_ashi_df['close'] < heikin_ashi_df['close'].rolling(window=previous_candles).min().shift(1)

    # Calculate 9 EMA and 21 EMA in one line
    heikin_ashi_df['ema_9'] = heikin_ashi_df['close'].ewm(span=9, adjust=False).mean()
    heikin_ashi_df['ema_21'] = heikin_ashi_df['close'].ewm(span=21, adjust=False).mean()
    heikin_ashi_df['trend'] = "-"
    heikin_ashi_df.loc[heikin_ashi_df['ema_9'] > heikin_ashi_df['ema_21'], 'trend'] = "UPTREND"
    heikin_ashi_df.loc[heikin_ashi_df['ema_9'] < heikin_ashi_df['ema_21'], 'trend'] = "DOWNTREND"

    return heikin_ashi_df

def color(HA):
    if HA['open'] < HA['close']: return "GREEN"
    elif HA['open'] > HA['close']: return "RED"
    else: return "INDECISIVE"

def sleep_three_minutes():
    current_utc_time = datetime.now(timezone.utc)
    next_target = (current_utc_time + timedelta(minutes=3)).replace(second=0, microsecond=0)
    next_target = next_target - timedelta(minutes=next_target.minute % 3)
    sleep_duration = (next_target - current_utc_time).total_seconds()
    print(f"Sleeping until {next_target.strftime('%H:%M:%S UTC')}")
    time.sleep(sleep_duration)

def ema_say_no_more(coin):
    main_1_hr = heikin_ashi(get_klines(coin, "1h"))
    direction = heikin_ashi(get_klines(coin, "3m"))
    # print(direction)

    if direction['trend'].iloc[-1] == "UPTREND" and direction['trend'].iloc[-2] == "DOWNTREND" and \
        main_1_hr['color'].iloc[-1] == "GREEN" and main_1_hr['close'].iloc[-1] > main_1_hr['close'].iloc[-2]:
        print(colored(str(coin) + " 🥦 CHANGING TO UPTREND 🥦 ", "green"))
        telegram_bot_sendtext(str(coin) + " 🥦 CHANGING TO UPTREND 🥦")
        sleep_three_minutes()

    if direction['trend'].iloc[-1] == "DOWNTREND" and direction['trend'].iloc[-2] == "UPTREND" and \
        main_1_hr['color'].iloc[-1] == "RED" and main_1_hr['close'].iloc[-1] < main_1_hr['close'].iloc[-2]:
        print(colored(str(coin) + " 💥 CHANGING TO DOWNTREND 💥", "red"))
        telegram_bot_sendtext(str(coin) + " 💥 CHANGING TO DOWNTREND 💥")
        sleep_three_minutes()

    else: print("🐺 WAIT 🐺")
    print("Last action executed @ " + datetime.now().strftime("%H:%M:%S") + "\n")

coin = "BTC"
print("\nMonitoring " + coin + "\n")

try:
    while True:
        try:
            ema_say_no_more(coin)
            time.sleep(1)

        except Exception as e:
            print(e)

except KeyboardInterrupt: print("\n\nAborted.\n")
