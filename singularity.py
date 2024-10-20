#!/bin/python3

import ccxt, pandas, requests, time, os
from datetime import datetime
from termcolor import colored

def telegram_bot_sendtext(bot_message):
    bot_token = os.environ.get('TELEGRAM_LIVERMORE')
    chat_id = "@swinglivermore"
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + chat_id + '&parse_mode=html&text=' + bot_message
    response = requests.get(send_text)
    return response.json()

def get_klines(coin, interval):
    pair = coin + "/USDT"
    tohlcv_colume = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    return pandas.DataFrame(ccxt.bybit().fetch_ohlcv(pair, interval , limit=101), columns=tohlcv_colume)

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
    heikin_ashi_df['bigger'] = heikin_ashi_df['body'] > heikin_ashi_df['body'].rolling(window=previous_candles).max().shift(1)
    heikin_ashi_df['higher'] = heikin_ashi_df['close'] > heikin_ashi_df['close'].rolling(window=previous_candles).max().shift(1)
    heikin_ashi_df['lower'] = heikin_ashi_df['close'] < heikin_ashi_df['close'].rolling(window=previous_candles).min().shift(1)

    heikin_ashi_df['ema_9'] = heikin_ashi_df['close'].ewm(span=9, adjust=False).mean()
    heikin_ashi_df['ema_21'] = heikin_ashi_df['close'].ewm(span=21, adjust=False).mean()
    heikin_ashi_df['ema_50'] = heikin_ashi_df['close'].ewm(span=50, adjust=False).mean()
    heikin_ashi_df['trend'] = heikin_ashi_df.apply(check_trend, axis=1)

    return heikin_ashi_df

def color(HA):
    if HA['open'] < HA['close']: return "GREEN"
    elif HA['open'] > HA['close']: return "RED"
    else: return "INDECISIVE"

def check_trend(row):
    if row['ema_9'] > row['ema_21'] and row['ema_21'] > row['ema_50']: return "UPTREND"
    elif row['ema_9'] < row['ema_21'] and row['ema_21'] < row['ema_50']: return "DOWNTREND"
    else: return "-"

def ema_say_no_more(coin):
    six_hour = heikin_ashi(get_klines(coin, "6h"))
    one_hour = heikin_ashi(get_klines(coin, "1h"))
    direction = heikin_ashi(get_klines(coin, "3m"))
    # print(direction)

    if direction['trend'].iloc[-1] == "UPTREND" and direction['open'].iloc[-1] > direction['ema_21'].iloc[-1] and \
        six_hour['color'].iloc[-1] == "GREEN" and six_hour['higher'].iloc[-1] and six_hour['bigger'].iloc[-1] and \
        one_hour['color'].iloc[-1] == "GREEN" and one_hour['higher'].iloc[-1] and one_hour['bigger'].iloc[-1]:
        print(colored(str(coin) + " 🥦 PUMPING 🥦 ", "green"))
        telegram_bot_sendtext(str(coin) + " 🥦 PUMPING 🥦")
        exit()

    if direction['trend'].iloc[-1] == "DOWNTREND" and direction['open'].iloc[-1] < direction['ema_21'].iloc[-1] and \
        six_hour['color'].iloc[-1] == "RED" and six_hour['lower'].iloc[-1] and six_hour['bigger'].iloc[-1] and \
        one_hour['color'].iloc[-1] == "RED" and one_hour['lower'].iloc[-1] and one_hour['bigger'].iloc[-1]:
        print(colored(str(coin) + " 💥 GRAVITY 💥", "red"))
        telegram_bot_sendtext(str(coin) + " 💥 GRAVITY 💥")
        exit()

    else: print("🐺 WAIT 🐺")
    print("Last action executed @ " + datetime.now().strftime("%H:%M:%S") + "\n")

try:
    while True:
        try:
            ema_say_no_more("BTC")
            time.sleep(1)

        except Exception as e:
            print(e)

except KeyboardInterrupt: print("\n\nAborted.\n")
