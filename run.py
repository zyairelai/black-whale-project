#!/bin/python3

import ccxt, pandas, requests, time, os
from datetime import datetime
from pybit.unified_trading import HTTP 

live_trade = True

coin = "BTC"
leverage = 100
trade_qty = 0.001

def telegram_bot_sendtext(bot_message):
    bot_token = os.environ.get('TELEGRAM_LIVERMORE')
    chat_id = "@swinglivermore"
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + chat_id + '&parse_mode=html&text=' + bot_message
    response = requests.get(send_text)
    return response.json()

exchange = ccxt.bybit()
client = HTTP(testnet=False, api_key=os.environ.get('BYBIT_KEY'), api_secret=os.environ.get('BYBIT_SECRET'))

def position_information(pair):
    response = client.get_positions(category='linear', symbol=pair)
    position = response['result']['list'][0] if response['result']['list'] else None
    return position

def set_leverage(pair, leverage, response):
    current_leverage = int(response['leverage'])
    if current_leverage and int(current_leverage) != leverage:
        client.set_leverage(symbol=pair, category='linear', buyLeverage=str(leverage), sellLeverage=str(leverage))
        print(f"Leverage set to {leverage} for {pair}.")

def market_open_long(pair, trade_qty):
    if live_trade: client.place_order(category="linear", symbol=pair, side='Buy', qty=trade_qty, order_type='Market')
    print("🚀 GO_LONG 🚀")

def market_open_short(pair, trade_qty):
    if live_trade: client.place_order(category="linear", symbol=pair, side='Sell', qty=trade_qty, order_type='Market')
    print("💥 GO_SHORT 💥")

def market_close_long(pair):
    if live_trade: client.place_order(symbol=pair, side='Sell', order_type='Market', qty=0, reduce_only=True, category='linear', position_idx=0)
    print("💰 CLOSED_LONG 💰")

def market_close_short(pair):
    if live_trade: client.place_order(symbol=pair, side='Buy', order_type='Market', qty=0, reduce_only=True, category='linear', position_idx=0)
    print("💰 CLOSED_SHORT 💰")

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
    heikin_ashi_df["body"] = abs(heikin_ashi_df['open'] - heikin_ashi_df['close'])
    heikin_ashi_df["upper_wick"] = heikin_ashi_df.apply(upper_wick, axis=1)
    heikin_ashi_df["lower_wick"] = heikin_ashi_df.apply(lower_wick, axis=1)
    heikin_ashi_df["indecisive"] = heikin_ashi_df.apply(is_indecisive, axis=1)
    heikin_ashi_df["candle"] = heikin_ashi_df.apply(valid_candle, axis=1)

    previous_candles = 2
    heikin_ashi_df['bigger'] = heikin_ashi_df['body'] > heikin_ashi_df['body'].rolling(window=previous_candles).max().shift(1)
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
    if HA['upper_wick'] > HA['body'] and HA['lower_wick'] > HA['body']: return True
    else: return False

def valid_candle(HA):
    if not HA['indecisive']:
        if HA['color'] == "GREEN": return "GREEN"
        elif HA['color'] == "RED": return "RED"
    else: return "INDECISIVE"

def long_short_signal(HA):
    if HA['candle'] == "GREEN" and HA['trend'] == "UPTREND" and HA['higher'] and HA['bigger']: return "LONG"
    elif HA['candle'] == "RED" and HA['trend'] == "DOWNTREND" and HA['lower'] and HA['bigger']: return "SHORT"
    else: return "-"

def bybit_livermore(coin):
    pair = coin + "USDT"
    response = position_information(pair)
    # print(response)

    direction = heikin_ashi(get_klines(coin, "1h"))
    support = heikin_ashi(get_klines(coin, "15m"))
    # print(direction)
    # print(support)

    if response['size'] > '0':
        if direction['close'].iloc[-1] < direction['close'].iloc[-1]: # or direction['upper_wick'].iloc[-1] > direction['body'].iloc[-1]:
            telegram_bot_sendtext(str(coin) + " 💰 CLOSED LONG 💰")
            market_close_long(pair)
        else: print(str(coin) + " HOLDING LONG ")

    elif response['size'] < '0':
        if direction['close'].iloc[-1] > direction['close'].iloc[-1]: # or direction['lower_wick'].iloc[-1] > direction['body'].iloc[-1]:
            telegram_bot_sendtext(str(coin) + " 💰 CLOSED LONG 💰")
            market_close_short(pair)
        else: print(str(coin) + " HOLDING SHORT ")

    else:
        if direction['signal'].iloc[-1] == "LONG" and support['signal'].iloc[-1] == "LONG":
            market_open_long(pair, trade_qty)
            telegram_bot_sendtext(str(coin) + " 🥦 PUMPING 🥦")

        elif direction['signal'].iloc[-1] == "SHORT" and support['signal'].iloc[-1] == "SHORT":
            market_open_short(pair, trade_qty)
            telegram_bot_sendtext(str(coin) + " 💥 GRAVITY 💥")

        else: print("🐺 WAIT 🐺")
    print("Last action executed @ " + datetime.now().strftime("%H:%M:%S") + "\n")

coin = "BTC"
print("\nMonitoring " + coin + "\n")

try:
    while True:
        try:
            bybit_livermore(coin)
            time.sleep(1)

        except Exception as e:
            print(e)

except KeyboardInterrupt: print("\n\nAborted.\n")
