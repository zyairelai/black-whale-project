#!/bin/python3

import ccxt, math, pandas, requests, time, os, sys
from datetime import datetime

def telegram_bot_sendtext(bot_message):
    bot_token = os.environ.get('TELEGRAM_WHOLENUMBER')
    chat_id = "@wholenumbergame"
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + chat_id + '&parse_mode=html&text=' + bot_message
    response = requests.get(send_text)
    return response.json()

def get_klines(coin, interval):
    pair = coin + "/USDT"
    tohlcv_colume = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    return pandas.DataFrame(ccxt.bybit().fetch_ohlcv(pair, interval , limit=3), columns=tohlcv_colume)

def whole_number(coin, upper, lower):
    one_minute = get_klines(coin, "1m")
    # print(one_minute)

    if one_minute['close'].iloc[-1] >= upper:
        print(str(coin) + " Price touches " + str(upper))
        telegram_bot_sendtext(str(coin) + " Price touches " + str(upper))
        exit()

    elif one_minute['close'].iloc[-1] <= lower:
        print(str(coin) + " Price touches " + str(lower))
        telegram_bot_sendtext(str(coin) + " Price touches " + str(lower))
        exit()

    else:
        print("Current price is at " + str(one_minute["close"].iloc[-1]))
    print("Last action executed @ " + datetime.now().strftime("%H:%M:%S") + "\n")


if len(sys.argv) > 1: grid = int(sys.argv[1])
else: grid = 1000

coin = "BTC"
initializedPrice = int(get_klines(coin, "1m")['close'].iloc[-1])
lower_grid = math.floor(initializedPrice / grid) * grid
upper_grid = math.ceil(initializedPrice / grid) * grid
upper_alert = upper_grid - (grid * 0.1)
lower_alert = lower_grid + (grid * 0.1)

print("\nWhole Number Game started for " + coin)
print(str(coin + " Current Price: " + str(initializedPrice)))
print("Set Upper Grid: " + str(upper_grid))
print("Set Lower Grid: " + str(lower_grid))
print("Grid: " + str(grid) + "\n")

try:
    while True:
        try:
            whole_number(coin, upper_grid, lower_grid)
            time.sleep(1)

        except Exception as e:
            print(e)

except KeyboardInterrupt: print("\n\nAborted.\n")
