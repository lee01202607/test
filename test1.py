import enum
from re import I
import time
import pyupbit
import datetime
import requests
from requests.models import encode_multipart_formdata

access = "Phjc84bxC4V9SftyBFF2aF1angfhMyYX0qCarznx"
secret = "yBUfqVMAhknb1uWDg0fn6xShb946Yr7uTqMqTEuZ"
myToken = "xoxb-2158907142755-2151930923126-ebTTynh1XxcPtxQfUKbYIMn2"

def post_message(token, channel, text):
    """슬랙 메시지 전송"""
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_ma15(ticker):
    """15일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=15)
    ma15 = df['close'].rolling(15).mean().iloc[-1]
    return ma15

def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_buyPrice(ticker):
    """평단가 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['avg_buy_price'] is not None:
                return float(b['avg_buy_price'])
            else:
                return 0
    return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]


def change_tick(value):
    if value >= 1 and value < 10:
        return round(float(value),2)
    elif value >= 10 and value < 100:
        return round(float(value),1)
    elif value >= 100 and value < 1000:
        return int(value)
    elif value >= 1000 and value < 10000:
        return value - value % 5
    elif value >= 10000 and value < 100000:
        return value - value % 10
    elif value >= 100000 and value < 1000000:
        return value - value % 100
    elif value >= 1000000:
        return value - value % 1000
    return 0

"""
totalTickers = pyupbit.get_tickers()
tickers = []
for word in totalTickers:
    if 'KRW' in word:
        tickers.append(word)
"""

tickers = ["KRW-BTC","KRW-ETH","KRW-BCH","KRW-LTC","KRW-ETC","KRW-NEO","KRW-STRK","KRW-LINK","KRW-DOT","KRW-REP","KRW-WAVES","KRW-ATOM","KRW-QTUM","KRW-GAS","KRW-OMG","KRW-EOS","KRW-SRM","KRW-XTZ","KRW-LSK","KRW-ADA","KRW-ICX","KRW-ZRX","KRW-XRP","KRW-MANA","KRW-BAT","KRW-XLM","KRW-DOGE","KRW-CHZ","KRW-CVC","KRW-POWR","KRW-POLY","KRW-HBAR","KRW-TRX","KRW-ZIL","KRW-UPP","KRW-LOOM","KRW-CRO","KRW-VET"]
#tickers = ["KRW-BTC"]

hold_flags = []
target = []
ma15_coin = []
now_coins = []

for ticker in tickers:
    price = get_target_price(ticker, 0.5)
    ma = get_ma15(ticker)
    target.append(price)
    ma15_coin.append(ma)
    hold_flags.append(False)
    time.sleep(0.1)


# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")
# 시작 메세지 슬랙 전송
post_message(myToken,"#bitm", "autotrade start")

while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-BTC")
        end_time = start_time + datetime.timedelta(days=1)
        print("========================================")
        print(now)

        for coin in now_coins:
            print("now_coin : " + coin)
            print("count : ", get_balance(coin[4:]),", price :", get_buyPrice(coin[4:]), "       ratio : ", round((get_current_price(coin)*get_balance(coin[4:]))/(get_balance(coin[4:])*get_buyPrice(coin[4:])),3))
            print("buy_price : ", int(get_balance(coin[4:])*get_buyPrice(coin[4:])) ,", cur_price : ", int(get_current_price(coin)*get_balance(coin[4:])))
            if(get_current_price(coin)/get_buyPrice(coin[4:]) > 1.03):
                sell_result = upbit.sell_market_order(coin, get_balance(coin[4:])/2)
                post_message(myToken,"#bitm", coin +" sell : " +str(sell_result))

        if start_time < now < end_time - datetime.timedelta(seconds=50):
            print("waiting")
            for i,candi in enumerate(tickers):
                candi = str(candi)
                current_price = get_current_price(candi)
                
                if int(target[i]) < current_price and int(ma15_coin[i]) < current_price and hold_flags[i] == False:
                    print(candi + " buy : ")
                    now_coins.append(candi)
                    
                    krw = get_balance("KRW")
                    krw = 10000
                    if krw > 5000:
                        buy_result = upbit.buy_market_order(candi, krw*0.9995) # 시장가주문
                        buy_result = upbit.buy_limit_order(candi,change_tick(target[i]),(krw*0.9995)/change_tick(target[i])) # 지정가주문
                        post_message(myToken,"#bitm", candi + " buy : " + str(buy_result))  
                        hold_flags[i] = True
                        print(hold_flags)
                time.sleep(0.1)
   
        else:
            for i,candi in enumerate(tickers):
                if hold_flags[i] == True:
                    sellCandi = str(candi[4:])
                    print(sellCandi)
                    balance = get_balance(sellCandi)
                    candi = str(candi)

                    if balance > 0.0001:
                        print("ccc")
                        sell_result = upbit.sell_market_order(candi, balance*0.9995)
                        post_message(myToken,"#bitm", candi +" sell : " +str(sell_result))
                        hold_flags[i] = False

            ma15_coin = []
            target = []
            hold_flags = []
            now_coins = []

            for ticker in tickers:
                price = get_target_price(ticker, 0.5)
                ma = get_ma15(ticker)
                target.append(price)
                ma15_coin.append(ma)
                hold_flags.append(False)
                time.sleep(0.05)        
        time.sleep(1)
        
    except Exception as e:
        print(e)
        post_message(myToken,"#bitm", e)
        time.sleep(1)
