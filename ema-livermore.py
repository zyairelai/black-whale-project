#!/bin/python3

import ccxt, pandas, requests, time, os
from datetime import datetime, timedelta, timezone
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
    heikin_ashi_df["upper"] = heikin_ashi_df.apply(upper_wick, axis=1)
    heikin_ashi_df["lower"] = heikin_ashi_df.apply(lower_wick, axis=1)
    heikin_ashi_df["body"] = abs(heikin_ashi_df['open'] - heikin_ashi_df['close'])
    heikin_ashi_df["indecisive"] = heikin_ashi_df.apply(is_indecisive, axis=1)
    heikin_ashi_df["candle"] = heikin_ashi_df.apply(valid_candle, axis=1)

    previous_candles = 2
    heikin_ashi_df['higher'] = heikin_ashi_df['close'] > heikin_ashi_df['close'].rolling(window=previous_candles).max().shift(1)
    heikin_ashi_df['lower'] = heikin_ashi_df['close'] < heikin_ashi_df['close'].rolling(window=previous_candles).min().shift(1)

    # Calculate 9 EMA and 21 EMA in one line
    heikin_ashi_df['ema_9'] = heikin_ashi_df['close'].ewm(span=9, adjust=False).mean()
    heikin_ashi_df['ema_21'] = heikin_ashi_df['close'].ewm(span=21, adjust=False).mean()
    heikin_ashi_df['trend'] = "-"
    heikin_ashi_df.loc[heikin_ashi_df['ema_9'] > heikin_ashi_df['ema_21'], 'trend'] = "UPTREND"
    heikin_ashi_df.loc[heikin_ashi_df['ema_9'] < heikin_ashi_df['ema_21'], 'trend'] = "DOWNTREND"
    heikin_ashi_df["signal"] = heikin_ashi_df.apply(long_short_signal, axis=1)

    return heikin_ashi_df

def color(HA):
    if HA['open'] < HA['close']: return "GREEN"
    elif HA['open'] > HA['close']: return "RED"
    else: return "INDECISIVE"

def upper_wick(HA):
    if HA['color'] == "GREEN": return HA['high'] - HA['close']
    elif HA['color'] == "RED": return HA['high'] - HA['open']
    else: return (HA['high'] - HA['open'] + HA['high'] - HA['close']) / 2

def lower_wick(HA):
    if HA['color'] == "GREEN": return  HA['open'] - HA['low']
    elif HA['color'] == "RED": return HA['close'] - HA['low']
    else: return (HA['open'] - HA['low'] + HA['close'] - HA['low']) / 2

def is_indecisive(HA):
    if HA['upper'] > HA['body'] and HA['lower'] > HA['body']: return True
    else: return False

def valid_candle(HA):
    if not HA['indecisive']:
        if HA['color'] == "GREEN": return "GREEN"
        elif HA['color'] == "RED": return "RED"
    else: return "INDECISIVE"

def long_short_signal(HA):
    if HA['candle'] == "GREEN" and HA['trend'] == "UPTREND" and HA['higher']: return "LONG"
    elif HA['candle'] == "RED" and HA['trend'] == "DOWNTREND" and HA['lower']: return "SHORT"
    else: return "-"

def sleep_until_next_hour():
    current_utc_time = datetime.now(timezone.utc)
    next_target = (current_utc_time + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    sleep_duration = (next_target - current_utc_time).total_seconds()
    print(f"Sleeping until {next_target}")
    time.sleep(sleep_duration)

def ema_livermore(coin):
    direction = heikin_ashi(get_klines(coin, "1h"))
    support = heikin_ashi(get_klines(coin, "15m"))
    # print(direction)
    # print(support)

    print("Current 1h Trend  : " + direction['trend'].iloc[-1])
    print("Current 15m Trend : " + support['trend'].iloc[-1])
    print("Current 1h candle : " + direction['candle'].iloc[-1])
    print("Current 15m candle: " + support['candle'].iloc[-1])

    if direction['signal'].iloc[-1] == "LONG" and support['signal'].iloc[-1] == "LONG":
        print(colored(str(coin) + " 🥦 PUMPING 🥦", "green"))
        telegram_bot_sendtext(str(coin) + " 🥦 PUMPING 🥦")
        sleep_until_next_hour()

    elif direction['signal'].iloc[-1] == "SHORT" and support['signal'].iloc[-1] == "SHORT":
        print(colored(str(coin) + " 💥 GRAVITY 💥", "red"))
        telegram_bot_sendtext(str(coin) + " 💥 GRAVITY 💥")
        sleep_until_next_hour()

    else: print("🐺 WAIT 🐺")
    print("Last action executed @ " + datetime.now().strftime("%H:%M:%S") + "\n")

coin = "BTC"
print("\nMonitoring " + coin + "\n")

try:
    while True:
        try:
            ema_livermore(coin)
            time.sleep(1)

        except Exception as e:
            print(e)

except KeyboardInterrupt: print("\n\nAborted.\n")
