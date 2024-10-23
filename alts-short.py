#!/bin/python3

import ccxt, pandas, requests, os

def telegram_bot_sendtext(bot_message):
    bot_token = os.environ.get('TELEGRAM_LIVERMORE')
    chat_id = "@swinglivermore"
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + chat_id + '&parse_mode=html&text=' + bot_message
    response = requests.get(send_text)
    return response.json()

def get_klines(coin, interval):
    pair = coin + "USDT"
    tohlcv_colume = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    return pandas.DataFrame(ccxt.binance().fetch_ohlcv(pair, interval , limit=101), columns=tohlcv_colume)

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
    return heikin_ashi_df

def color(HA):
    if HA['open'] < HA['close']: return "GREEN"
    elif HA['open'] > HA['close']: return "RED"
    else: return "INDECISIVE"

def fuck_alts(coin):
    btc_direction = heikin_ashi(get_klines("BTC", "6h"))
    btc_is_red = btc_direction['color'].iloc[-1] == "RED"

    alt_direction = heikin_ashi(get_klines(coin, "6h"))
    alt_dumping = alt_direction['low'].iloc[-1] < alt_direction['low'].iloc[-2] 

    if btc_is_red and alt_dumping:
        print("💥 SHORT ALTS 💥 " + coin)
        telegram_bot_sendtext("💥 SHORT ALTS 💥 " + coin + " on Binance")
        exit()

    else: print("🐺 WAIT 🐺 " + coin)

try:
    while True:
        try:
            fuck_alts("ETH")

        except Exception as e:
            print(e)

except KeyboardInterrupt: print("\n\nAborted.\n")