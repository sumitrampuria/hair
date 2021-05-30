import datetime
import os.path
import matplotlib.pyplot as plt
import pandas as pd
import time as t
from alice_blue import *
import warnings


# Config
username = '251196'
password = 'Sumi1712#'
api_secret = 'tN7Af1yOtWn6IRsg663Ojhebvb0vGwMlxtxYmuoYqstzJiyPubfHZpGDaMi3YvNy'
twoFA = 's'
EMA_CROSS_SCRIP = 'INFY'
# Config
ltp = 0
socket_opened = False
alice = None
col_names_active = ['symbol', 'timestamp', 'vol', 'ltp', 'bid', 'ask', 'readable_time', 'status', 'ce_limit_target', 'ce_limit_adjustment', 'pe_limit_target', 'pe_limit_adjustment']
col_names = ['symbol', 'timestamp', 'vol', 'vol_delta', 'ltp', 'bid', 'ask', 'readable_time', 'status', 'active_status', 'active_count', 'traded_ins', 'traded_price', 'traded_time_delta', 'misc']
col_names_candle = ['symbol', 'timestamp', 'vol', 'open', 'high', 'low', 'close']
oi_data = []
list_scripts = []
todays_date = ''
india_vix_nse_index, bank_nifty_nse_fut, bank_nifty_nse_index = 0, 0, 0
broad_list, traded_ins = '', ''
# count = 0
latest_minus_one_vol = 100
qualifying_candles = 0
latest_minus_one_nifty_candle, latest_minus_one_ce_candle, latest_minus_one_pe_candle, ce_main_limit_orderid, pe_main_limit_orderid,  ce_stoploss_order, pe_stoploss_order = [], [], [], [], [], [], []
warnings.filterwarnings("ignore")
timestamp, idx = 0, 0
active_count, win_count, loss_count, ce_limit_adjustment, pe_limit_adjustment = 0, 0, 0, 0, 0
last_vol, last_price = 100000000, 0
threshold_volume = 43
stop_loss = -17
target_profit = 10
lots = 1
threshold_trade_not_done_secs = 210
ce_strike = 34800
pe_strike = 34800
threshold_selloff = 15000
abandon_ce_initial, abandon_pe_initial = False, False

def event_handler_quote_update(message):
    global oi_data, ltp, count, timestamp
    # print(message)
    # timestamp = datetime.datetime.fromtimestamp(message['exchange_time_stamp'])
    # count = count + 1
    timestamp = (message['exchange_time_stamp'])
    ltp = message['ltp']
    # date = datetime.datetime.fromtimestamp(timestamp).date()
    oi_data = oi_data.append({'symbol': message['instrument'].symbol, 'timestamp': timestamp, 'vol': message['volume'],'ltp': message['ltp'], 'bid': message['best_bid_price'], 'ask': message['best_ask_price'], 'status': 'pending'}, ignore_index=True)
    # 'readable_time': datetime.datetime.fromtimestamp(timestamp)

def open_callback():
    global socket_opened
    socket_opened = True

def main1():
    global socket_opened
    global alice
    global username
    global password
    global twoFA
    global api_secret
    global EMA_CROSS_SCRIP, oi_data, list_scripts, india_vix_nse_index, bank_nifty_nse_fut, broad_list, bank_nifty_nse_index
    global todays_date, latest_minus_one_vol, qualifying_candles, latest_minus_one_nifty_candle, latest_minus_one_ce_candle, latest_minus_one_pe_candle
    todays_date = datetime.datetime.now().strftime("%Y-%m-%d")
    global ltp, timestamp, active_count, win_count, loss_count, ce_main_limit_orderid, pe_main_limit_orderid, ce_stoploss_order, pe_stoploss_order, stop_loss, target_profit
    global threshold_trade_not_done_secs, threshold_volume, ce_limit_adjustment, pe_limit_adjustment
    global ce_strike, pe_strike, abandon_ce_initial, abandon_pe_initial, threshold_selloff
    global last_vol, last_price, traded_ins, idx

    oi_data = pd.DataFrame(columns=col_names)
    all_candles = pd.DataFrame()
    access_token = AliceBlue.login_and_get_access_token(username=username, password=password, twoFA=twoFA,api_secret=api_secret, app_id='GUkBdb1ZXR')
    print(access_token)
    alice = AliceBlue(username=username, password=password, access_token=access_token, master_contracts_to_download=['NSE', 'NFO'])

    india_vix_nse_index = alice.get_instrument_by_symbol('NSE', 'India VIX')
    bank_nifty_nse_index = alice.get_instrument_by_symbol('NSE', 'Nifty Bank')
    bank_nifty_nse_fut = alice.get_instrument_for_fno(symbol='BANKNIFTY', expiry_date=datetime.date(2021, 5, 27), is_fut=True)
    ins_scrip_ce = alice.get_instrument_for_fno(symbol='BANKNIFTY', expiry_date=datetime.date(2021, 5, 27), is_fut=False,
                                                strike=(ce_strike+0), is_CE=True)
    ins_scrip_pe = alice.get_instrument_for_fno(symbol='BANKNIFTY', expiry_date=datetime.date(2021, 5, 27), is_fut=False,
                                                strike=(pe_strike+0), is_CE=False)
    ce_symbol = 'BANKNIFTY 3 JUN21 '+str(ce_strike)+'.0 CE'
    # ce_symbol = 'BANKNIFTY MAY ' + str(ce_strike) + '.0 CE'
    pe_symbol = 'BANKNIFTY 3 JUN21 '+str(pe_strike)+'.0 PE'
    fut_symbol = 'BANKNIFTY JUN FUT'
    list_scripts=[bank_nifty_nse_index, bank_nifty_nse_fut, ins_scrip_ce, ins_scrip_pe]


    alice.start_websocket(subscribe_callback=event_handler_quote_update, socket_open_callback=open_callback, run_in_background=True)
    while (socket_opened == False):
        pass
    alice.subscribe(list_scripts, LiveFeedType.MARKET_DATA)
    while True:
        if (datetime.datetime.now().second == 0) & (datetime.datetime.now().minute % 5 == 0):
            # latest_nifty_candle = pd.DataFrame(columns=col_names_candle)

            alice.unsubscribe(list_scripts, LiveFeedType.MARKET_DATA)
            t.sleep(1)
            latest_nifty_tick = oi_data[(oi_data['symbol'] == 'Nifty Bank') & (oi_data['status'] == 'pending')]
            latest_niftyfut_tick = oi_data[(oi_data['symbol'] == fut_symbol) & (oi_data['status'] == 'pending')]
            latest_ce_tick = oi_data[(oi_data['symbol'] == ce_symbol) & (oi_data['status'] == 'pending')]
            latest_pe_tick = oi_data[(oi_data['symbol'] == pe_symbol) & (oi_data['status'] == 'pending')]
            oi_data['status'] = 'done'


            #get ohlc of nifty, call and put
            # latest_nifty_tick = latest_nifty_tick.set_index(['timestamp'])
            # latest_nifty_tick.index = pd.to_datetime(latest_nifty_tick.index, unit='s')
            latest_nifty_candle = {'symbol': 'Nifty Bank', 'timestamp': latest_nifty_tick.iloc[-1]['timestamp'], 'open': latest_nifty_tick.iloc[0]['ltp'], 'high': max(latest_nifty_tick['ltp']), 'low': min(latest_nifty_tick['ltp']), 'close': latest_nifty_tick.iloc[-1]['ltp']}
            latest_ce_candle = {'symbol': ce_symbol, 'timestamp': latest_ce_tick.iloc[-1]['timestamp'], 'open': latest_ce_tick.iloc[0]['ltp'], 'high': max(latest_ce_tick['ltp']), 'low': min(latest_ce_tick['ltp']), 'close': latest_ce_tick.iloc[-1]['ltp']}
            latest_pe_candle = {'symbol': pe_symbol, 'timestamp': latest_pe_tick.iloc[-1]['timestamp'],
                                'open': latest_pe_tick.iloc[0]['ltp'], 'high': max(latest_pe_tick['ltp']),
                                'low': min(latest_pe_tick['ltp']), 'close': latest_pe_tick.iloc[-1]['ltp']}
            print(latest_nifty_candle)
            print(latest_ce_candle)
            print(latest_pe_candle)

            all_candles = all_candles.append(latest_nifty_candle, ignore_index=True)
            all_candles = all_candles.append(latest_ce_candle, ignore_index=True)
            all_candles = all_candles.append(latest_pe_candle, ignore_index=True)
            all_candles.to_csv(r'ohlc_' + todays_date + '.csv')
            oi_data.to_csv(r'tick_data_' + todays_date + '.csv')
            latest_volume = (latest_niftyfut_tick.tail(1)['vol'].values - latest_niftyfut_tick.head(1)['vol'].values)/1000

            if(latest_volume < threshold_volume) & (latest_nifty_candle['low'] < latest_nifty_candle['close'] < latest_nifty_candle['high']):
                #we can also check here the length of candle
                qualifying_candles = qualifying_candles + 1
                print('Last closing candle is good (low volume). Total good already: ', qualifying_candles)
                if qualifying_candles > 1:
                    print('we are active at: ' + datetime.datetime.strftime(datetime.datetime.now(), '%H:%M:%S'))
                    active_tick = pd.DataFrame(columns=col_names_active)
                    ce_traded, pe_traded, one_leg_only = False, False, False
                    abandon_ce = abandon_ce_initial
                    abandon_pe = abandon_pe_initial
                    active_count = active_count + 1
                    local_timestamp = timestamp
                    traded_timestamp = 0
                    print('timestamp: ', local_timestamp)
                    active = True
                    ce_lower = min(latest_ce_candle['low'], latest_minus_one_ce_candle['low'])
                    pe_lower = min(latest_pe_candle['low'], latest_minus_one_pe_candle['low'])
                    print("ce_lower: "+ str(ce_lower) + " | pe_lower: "+str(pe_lower))
                    ce_limit_adjustment = 0
                    pe_limit_adjustment = 0

                    if (latest_pe_candle['low'] < latest_minus_one_pe_candle['low']):
                        diff = latest_minus_one_pe_candle['low'] - latest_pe_candle['low']
                        if (4 < diff < 9):
                            pe_limit_adjustment = -5
                        if (9 <= diff <= 15 ):
                            pe_limit_adjustment = -10
                        if (15 < diff < 25):
                            pe_limit_adjustment = -20
                        if ( diff >= 25):
                            pe_limit_adjustment = -40
                        pe_limit_target = pe_lower + pe_limit_adjustment
                    else:
                        pe_limit_target = pe_lower
                        pe_limit_adjustment = 0

                    if (latest_ce_candle['low'] < latest_minus_one_ce_candle['low']):
                        diff = latest_minus_one_ce_candle['low'] - latest_ce_candle['low']
                        if (4 < diff < 9):
                            ce_limit_adjustment = -5
                        if (9 <= diff <= 15 ):
                            ce_limit_adjustment = -10
                        if (15 < diff < 25):
                            ce_limit_adjustment = -20
                        if ( diff >= 25):
                            ce_limit_adjustment = -40
                        ce_limit_target = ce_lower + ce_limit_adjustment
                    else:
                        ce_limit_target = ce_lower
                        ce_limit_adjustment = 0


                    alice.subscribe(ins_scrip_ce, LiveFeedType.MARKET_DATA)
                    t.sleep(1)
                    ce_open = ltp
                    alice.unsubscribe(ins_scrip_ce, LiveFeedType.MARKET_DATA)
                    alice.subscribe(ins_scrip_pe, LiveFeedType.MARKET_DATA)
                    t.sleep(1)
                    pe_open = ltp
                    print("ce_open: "+ str(ce_open)+" | pe_open: " + str(pe_open))
                    list_scripts = [bank_nifty_nse_index, bank_nifty_nse_fut, ins_scrip_ce, ins_scrip_pe]
                    alice.subscribe(list_scripts, LiveFeedType.MARKET_DATA)

                    traded_price = 0
                    initial_limit_orders_placed = False
                    stop_loss = -20
                    target_profit = 10

                    if(abandon_pe):
                        one_leg_only = True
                    if(abandon_ce):
                        one_leg_only = True

                    last_vol = 100000000
                    last_price = 0
                    traded_ins = ''
                    while active:
                        if not initial_limit_orders_placed:
                            print('Placing initial limit orders ' + 'ce_target_buy: '+str(ce_limit_target) + ' | pe_target_buy: '+str(pe_limit_target))
                            if (not abandon_ce):
                                ce_main_limit_orderid = place_limit(ins_scrip_ce, ce_limit_target, 'BUY')
                                print(ce_main_limit_orderid)
                            if (not abandon_pe):
                                pe_main_limit_orderid = place_limit(ins_scrip_pe, pe_limit_target, 'BUY')
                                print(pe_main_limit_orderid)
                            initial_limit_orders_placed = True

                        active_ce_tick = oi_data[(oi_data['symbol'] == ce_symbol) & (oi_data['status'] == 'pending')]
                        active_pe_tick = oi_data[(oi_data['symbol'] == pe_symbol) & (oi_data['status'] == 'pending')]

                        if (not ce_traded) & (not abandon_ce):
                            if (latest_ce_candle['high'] - active_ce_tick.iloc[-1]['ltp'] < 7.5) & (not abandon_ce) & (not ce_traded):
                                print("Abandoning ce side as price reached near last high: ", active_ce_tick.iloc[-1]['ltp'])
                                abandon_ce = True
                                alice.cancel_order(ce_main_limit_orderid['data']['oms_order_id'])

                            if (timestamp - local_timestamp > threshold_trade_not_done_secs) & (not abandon_ce) & (not ce_traded):
                                print("Abandoning ce side as Time elapsed, current time: ",timestamp)
                                abandon_ce = True
                                alice.cancel_order(ce_main_limit_orderid['data']['oms_order_id'])

                            if(active_ce_tick.iloc[-1]['ltp'] - ce_open > 5) & (not abandon_ce) & (not ce_traded):
                                print("Abandoning ce side as price has been going up: ", active_ce_tick.iloc[-1]['ltp'])
                                abandon_ce = True
                                alice.cancel_order(ce_main_limit_orderid['data']['oms_order_id'])

                            ce_order_details = alice.get_order_history(ce_main_limit_orderid['data']['oms_order_id'])
                            if (ce_order_details['status'] == 'success'):
                                if (ce_order_details['data'][0]['order_status'] == 'complete'):
                                    if (not abandon_ce):
                                        traded_price = ce_order_details['data'][0]['average_price']
                                        print("CE traded at: "+ str(traded_price) + " Active_count: " +str(active_count))
                                        print(ce_order_details)
                                        ce_traded = True
                                        abandon_pe = True
                                        traded_timestamp = timestamp
                                        traded_ins = 'CE'
                                        if(not one_leg_only):
                                            alice.cancel_order(pe_main_limit_orderid['data']['oms_order_id'])
                                        print("Placing CE SL order at: " + str(traded_price + stop_loss))
                                        ce_stoploss_order = place_stoploss(ins_scrip_ce, traded_price + stop_loss, 'SELL')
                                        idx = oi_data.loc[(oi_data['symbol'] == ce_symbol) & (oi_data['status'] == 'pending')].index.max()
                                        oi_data.loc[idx, 'misc'] = 'traded_here_CE'


                        if (not pe_traded) & (not abandon_pe):
                            pe_order_details = alice.get_order_history(pe_main_limit_orderid['data']['oms_order_id'])
                            if (pe_order_details['status'] == 'success'):
                                if (pe_order_details['data'][0]['order_status'] == 'complete'):
                                    if (not abandon_pe):
                                        traded_price = pe_order_details['data'][0]['average_price']
                                        print("PE traded at: "+ str(traded_price) + " Active_count: " +str(active_count))
                                        print(pe_order_details)
                                        pe_traded = True
                                        abandon_ce = True
                                        traded_timestamp = timestamp
                                        traded_ins = 'PE'
                                        if (not one_leg_only):
                                            alice.cancel_order(ce_main_limit_orderid['data']['oms_order_id'])
                                        print("Placing PE SL order at: "+ str(traded_price + stop_loss))
                                        pe_stoploss_order = place_stoploss(ins_scrip_pe, traded_price + stop_loss,'SELL')
                                        idx = oi_data.loc[(oi_data['symbol'] == pe_symbol) & (oi_data['status'] == 'pending')].index.max()
                                        oi_data.loc[idx, 'misc'] = 'traded_here_PE'


                            if (active_pe_tick.iloc[-1]['ltp'] - pe_open > 5) & (not abandon_pe) & (not pe_traded):
                                print("Abandoning pe side as price has been going up: ", active_pe_tick.iloc[-1]['ltp'])
                                abandon_pe = True
                                alice.cancel_order(pe_main_limit_orderid['data']['oms_order_id'])

                            if (timestamp - local_timestamp > threshold_trade_not_done_secs) & (not abandon_pe) & (not pe_traded):
                                print("Abandoning pe side as Time elapsed, current time: ",timestamp)
                                abandon_pe = True
                                alice.cancel_order(pe_main_limit_orderid['data']['oms_order_id'])

                            if (latest_pe_candle['high'] - active_pe_tick.iloc[-1]['ltp'] < 7.5) & (not abandon_pe) & (not pe_traded):
                                print("Abandoning pe side as price reached near last high: ", active_pe_tick.iloc[-1]['ltp'])
                                abandon_pe = True
                                alice.cancel_order(pe_main_limit_orderid['data']['oms_order_id'])

                        if ce_traded:
                            print('ce ltp: ', active_ce_tick.iloc[-1]['ltp'], ' | buy price: ', traded_price)
                            print('ce vol: ' + str(active_ce_tick.iloc[-1]['vol'])+ ' | Last vol: '+ str(last_vol)+ ' | Last price: '+ str(last_price))
                            idx = oi_data.loc[(oi_data['symbol'] == ce_symbol) & (oi_data['status'] == 'pending')].index.max()
                            oi_data.loc[idx, 'traded_time_delta'] = (active_ce_tick.iloc[-1]['timestamp'] - traded_timestamp)
                            oi_data.loc[idx, 'vol_delta'] = (active_ce_tick.iloc[-1]['vol'] - last_vol)

                            if(active_ce_tick.iloc[-1]['vol']-last_vol>threshold_selloff):
                                print("huge volume in ce")
                                if (last_price>active_ce_tick.iloc[-1]['ltp']):
                                    alice.cancel_order(ce_stoploss_order['data']['oms_order_id'])
                                    print('Huge selloff came in ce, current vol: ', active_ce_tick.iloc[-1]['vol'])
                                    place_market(ins_scrip_ce, 'SELL')
                                    print("Last volume: " + str(last_vol)+" | Last price: "+str(last_price)+" count: "+str(active_count))
                                    print("Traded timestamp: "+str(traded_timestamp)+" Current timestamp: "+str(timestamp))
                                    abandon_pe = True
                                    abandon_ce = True
                                    loss_count = loss_count + 1
                                    oi_data.loc[idx, 'misc'] = 'vol_spike'

                            if (active_ce_tick.iloc[-1]['bid'] - traded_price >= target_profit):
                                alice.cancel_order(ce_stoploss_order['data']['oms_order_id'])
                                print('ce target reached: ', active_ce_tick.iloc[-1]['bid'])
                                place_market(ins_scrip_ce, 'SELL')
                                abandon_pe = True
                                abandon_ce = True
                                win_count = win_count + 1
                                oi_data.loc[idx, 'misc'] = 'target_reached_here'

                            last_vol = active_ce_tick.iloc[-1]['vol']
                            last_price = active_ce_tick.iloc[-1]['ltp']
                            print('Last price: ' + str(last_price)+ ' | Last Vol: '+ str(last_vol))
                            ce_SLorder_details = alice.get_order_history(ce_stoploss_order['data']['oms_order_id'])
                            if (ce_SLorder_details['status'] == 'success'):
                                if (ce_SLorder_details['data'][0]['order_status'] == 'complete'):
                                    print('ce SL reached: ', ce_SLorder_details['data'][0]['average_price'])
                                    abandon_pe = True
                                    abandon_ce = True
                                    loss_count = loss_count + 1
                                    oi_data.loc[idx, 'misc'] = 'sl_reached_here'


                        if pe_traded:
                            print('pe ltp: ', active_pe_tick.iloc[-1]['ltp'], ' | buy price: ', traded_price)
                            print('pe vol: ' + str(active_pe_tick.iloc[-1]['vol'])+ ' | Last vol: '+ str(last_vol)+ ' | Last price: '+ str(last_price))
                            idx = oi_data.loc[(oi_data['symbol'] == pe_symbol) & (oi_data['status'] == 'pending')].index.max()
                            oi_data.loc[idx, 'traded_time_delta'] = (active_pe_tick.iloc[-1]['timestamp'] - traded_timestamp)
                            oi_data.loc[idx, 'vol_delta'] = (active_pe_tick.iloc[-1]['vol'] - last_vol)

                            if(active_pe_tick.iloc[-1]['vol']-last_vol>threshold_selloff):
                                print("huge vol in pe")
                                if (last_price>active_pe_tick.iloc[-1]['ltp']):
                                    alice.cancel_order(pe_stoploss_order['data']['oms_order_id'])
                                    print('Huge selloff came in pe, vol: ', active_pe_tick.iloc[-1]['vol'])
                                    place_market(ins_scrip_pe, 'SELL')
                                    print("Last volume: " + str(last_vol)+" | Last price: "+str(last_price)+" count: "+str(active_count))
                                    print("Traded timestamp: "+str(traded_timestamp)+" Current timestammp: "+str(timestamp))
                                    abandon_pe = True
                                    abandon_ce = True
                                    loss_count = loss_count + 1
                                    oi_data.loc[idx, 'misc'] = 'vol_spike'

                            last_vol = active_pe_tick.iloc[-1]['vol']
                            last_price = active_pe_tick.iloc[-1]['ltp']
                            print('Last price: ' + str(last_price)+ ' | Last Vol: '+ str(last_vol))

                            if (active_pe_tick.iloc[-1]['bid'] - traded_price >= target_profit):
                                alice.cancel_order(pe_stoploss_order['data']['oms_order_id'])
                                print('pe target reached: ', active_pe_tick.iloc[-1]['bid'])
                                place_market(ins_scrip_pe, 'SELL')
                                abandon_pe = True
                                abandon_ce = True
                                win_count = win_count + 1
                                oi_data.loc[idx, 'misc'] = 'target_reached_here'

                            pe_SLorder_details = alice.get_order_history(pe_stoploss_order['data']['oms_order_id'])
                            if (pe_SLorder_details['status'] == 'success'):
                                if (pe_SLorder_details['data'][0]['order_status'] == 'complete'):
                                    print('pe SL reached: ', pe_SLorder_details['data'][0]['average_price'])
                                    abandon_pe = True
                                    abandon_ce = True
                                    loss_count = loss_count + 1
                                    oi_data.loc[idx, 'misc'] = 'sl_reached_here'


                        if abandon_ce & abandon_pe:
                            if (not ce_traded) & (not pe_traded):
                                print('Not active anymore as both pe and ce sides abandoned')
                                oi_data.loc[(oi_data['status'] == 'pending'), 'active_status'] = 'active_not_traded'
                            else:
                                print('Win: ' + str(win_count) + ' | Loss: ' + str(loss_count))
                                oi_data.loc[(oi_data['status'] == 'pending'), 'active_status'] = 'active_traded'
                                oi_data.loc[(oi_data['status'] == 'pending'), 'traded_ins'] = traded_ins
                                oi_data.loc[(oi_data['status'] == 'pending'), 'traded_price'] = traded_price

                            active = False
                            if(not abandon_pe_initial):
                                alice.cancel_order(pe_main_limit_orderid['data']['oms_order_id'])
                            if(not abandon_ce_initial):
                                alice.cancel_order(ce_main_limit_orderid['data']['oms_order_id'])
                            active_tick = active_tick.append(oi_data[oi_data['status'] == 'pending'], ignore_index=True)
                            active_tick['ce_limit_target'] = ce_limit_target
                            active_tick['ce_limit_adjustment'] = ce_limit_adjustment
                            active_tick['pe_limit_target'] = pe_limit_target
                            active_tick['pe_limit_adjustment'] = pe_limit_adjustment
                            active_tick.to_csv(r'active_tick_data_' + str(active_count) + '.csv')
                            oi_data.loc[(oi_data['status'] == 'pending'), 'active_count'] = active_count

                        t.sleep(0.9)


            else:
                qualifying_candles = 0
                if (latest_volume >= threshold_volume):
                    print('Candle rejected due to high volume: ', latest_volume)
                else:
                    print('Candle rejected as close = High/Low ', latest_nifty_candle['close'])

            latest_minus_one_nifty_candle = latest_nifty_candle
            latest_minus_one_ce_candle = latest_ce_candle
            latest_minus_one_pe_candle = latest_pe_candle
            latest_minus_one_vol = latest_volume
            list_scripts = [bank_nifty_nse_index, bank_nifty_nse_fut, ins_scrip_ce, ins_scrip_pe]
            alice.subscribe(list_scripts, LiveFeedType.MARKET_DATA)


def place_limit(instrument, price, action):
    global alice, lots
    if action == 'BUY':
        order_id = alice.place_order(transaction_type=TransactionType.Buy,
                          instrument=instrument,
                          quantity=25*lots,
                          order_type=OrderType.Limit,
                          product_type=ProductType.Intraday,
                          price=price,
                          trigger_price=None,
                          stop_loss=None,
                          square_off=None,
                          trailing_sl=None,
                          is_amo=False)
    else:
        order_id = alice.place_order(transaction_type=TransactionType.Sell,
                                     instrument=instrument,
                                     quantity=25*lots,
                                     order_type=OrderType.Limit,
                                     product_type=ProductType.Intraday,
                                     price=price,
                                     trigger_price=None,
                                     stop_loss=None,
                                     square_off=None,
                                     trailing_sl=None,
                                     is_amo=False)
    return order_id

def place_market(instrument, action):
    global alice, lots
    if action == 'BUY':
        order_id = alice.place_order(transaction_type=TransactionType.Buy,
                          instrument=instrument,
                          quantity=25*lots,
                          order_type=OrderType.Market,
                          product_type=ProductType.Intraday,
                          price=0.0,
                          trigger_price=None,
                          stop_loss=None,
                          square_off=None,
                          trailing_sl=None,
                          is_amo=False)
    else:
        order_id = alice.place_order(transaction_type=TransactionType.Sell,
                                     instrument=instrument,
                                     quantity=25*lots,
                                     order_type=OrderType.Market,
                                     product_type=ProductType.Intraday,
                                     price=0.0,
                                     trigger_price=None,
                                     stop_loss=None,
                                     square_off=None,
                                     trailing_sl=None,
                                     is_amo=False)
    return order_id

def place_stoploss(instrument, price, action):
    global alice, lots
    if action == 'BUY':
        order_id = alice.place_order(transaction_type=TransactionType.Buy,
                          instrument=instrument,
                          quantity=25*lots,
                          order_type=OrderType.StopLossLimit,
                          product_type=ProductType.Intraday,
                          price=price,
                          trigger_price=price,
                          stop_loss=None,
                          square_off=None,
                          trailing_sl=None,
                          is_amo=False)
    else:
        order_id = alice.place_order(transaction_type=TransactionType.Sell,
                                     instrument=instrument,
                                     quantity=25*lots,
                                     order_type=OrderType.StopLossLimit,
                                     product_type=ProductType.Intraday,
                                     price=price,
                                     trigger_price=price,
                                     stop_loss=None,
                                     square_off=None,
                                     trailing_sl=None,
                                     is_amo=False)
    return order_id



def main2():
    temp = False
    count = 1
    print(datetime.datetime.now().minute)
    data = [['tom', 10], ['nick', 15], ['juli', 14]]
    df = pd.DataFrame(data, columns=['Name', 'Age'])
    tick_data = pd.read_csv('active_tick_data_1.csv')
    # tick_data[(tick_data['symbol'] == 'BANKNIFTY MAY 34800.0 CE')].iloc[-1]['readable_time']='this'
    # tick_data.loc[(tick_data['symbol'] == 'BANKNIFTY MAY 34800.0 PE') & (tick_data.index.isin(tick_data.index[-5:])), 'readable_time'] = 'this'
    # tick_data.loc[(tick_data['symbol'] == 'BANKNIFTY MAY 34800.0 PE') & tick_data['timestamp'] == max(tick_data['timestamp']), 'readable_time'] = 'this'
    idx = tick_data.loc[(tick_data['symbol'] == 'BANKNIFTY MAY 34800.0 PE')].index.max()
    tick_data.loc[idx, 'readable_time'] = 'this'
    tick_data.to_csv(r'output.csv')
    # while count<3:
    #     # if (datetime.datetime.now().second == 0) & (datetime.datetime.now().minute % 5 == 0):
    #     print('ya')
    #     count = count + 1
    #     df.to_csv(r'tick_data_' + str(count) + '.csv')

if __name__ == '__main__':
    main2()


