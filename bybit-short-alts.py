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
    return heikin_ashi_df

def fuck_alts(coin):
    direction = heikin_ashi(get_klines(coin, "1h"))
    # print(direction)

    if direction['close'].iloc[-1] < direction['close'].iloc[-2] and direction['low'].iloc[-1] < direction['low'].iloc[-2]:
        print(colored("💥 TIME TO SHORT 💥 " + coin, "red"))
        telegram_bot_sendtext("💥 TIME TO SHORT 💥 " + coin + " on BYBIT")
        exit()

    else: print("🐺 WAIT 🐺 " + coin)
    print("Last action executed @ " + datetime.now().strftime("%H:%M:%S") + "\n")

try:
    while True:
        try:
            fuck_alts("BTC")

            time.sleep(1)
        except Exception as e:
            print(e)

except KeyboardInterrupt: print("\n\nAborted.\n")
