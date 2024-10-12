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
    return pandas.DataFrame(ccxt.bybit().fetch_ohlcv(pair, interval , limit=11), columns=tohlcv_colume)

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

def ema_say_no_more(coin):
    direction = heikin_ashi(get_klines(coin, "15m"))
    # print(direction)

    print("Current 15m Trend  : " + direction['trend'].iloc[-1])
    print("Current 15m candle : " + direction['color'].iloc[-1])

    if direction['trend'].iloc[-1] == "DOWNTREND" and \
        direction['color'].iloc[-1] == "GREEN" and \
        direction['close'].iloc[-1] > direction['ema_9'].iloc[-1]:
        print(colored(str(coin) + " ⚠️ REVERSAL ⚠️", "yellow"))
        telegram_bot_sendtext(str(coin) + " ⚠️ REVERSAL ⚠️")
        exit()

    if direction['trend'].iloc[-1] == "UPTREND" and \
        direction['color'].iloc[-1] == "RED" and \
        direction['close'].iloc[-1] < direction['ema_9'].iloc[-1]:
        print(colored(str(coin) + " ⚠️ REVERSAL ⚠️", "yellow"))
        telegram_bot_sendtext(str(coin) + " ⚠️ REVERSAL ⚠️")
        exit()

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
