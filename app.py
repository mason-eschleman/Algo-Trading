import time, datetime
import queue
import pandas as pd
from threading import Thread
from lightweight_charts import Chart

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.client import Contract, Order
from ibapi.tag_value import TagValue


## set up some constants that are to be used throughout the connection and trading processes ##

# we want to be on a Demo Account unless specified otherwise
LIVE_TRADING = False

# these are the ports to be used in our connection to the TWS application
LIVE_TRADING_PORT = 7496
PAPER_TRADING_PORT = 7497

# set the trading port we're utilizing as the Demo port
# create if-statement in case we want to implement prompt user for port later down the line
TRADING_PORT = PAPER_TRADING_PORT
if LIVE_TRADING:
    TRADING_PORT = LIVE_TRADING_PORT

# initial chart ticker to be displayed
INITIAL_TICKER = "AAPL"

# default IP and Client ID
DEFAULT_HOST = '127.0.0.1'
DEFAULT_CLIENT_ID = 1

# create a queue for data coming from IB API
data_queue = queue.Queue()

# instantiate a list for any drawings that the user might make on the chart
current_lines = []



# create the Client per API's requirements
class Client(EWrapper, EClient):
     
    def __init__(self, host, port, client_id):
        EClient.__init__(self, self) 
        
        self.connect(host, port, client_id)

        # API uses threading. Create a new Thread
        thread = Thread(target=self.run)
        thread.start()

    # this function handles the placing of orders
    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        self.order_id = orderId
        print(f"next valid id is {self.order_id}")

    # define an error function for traceback purposes
    def error(self, req_id, code, msg, advancedOrderRejectJson, errorTime=""):
        if code in [2104, 2106, 2158]:
            print(msg)
        else:
            print('Error {}: {}'.format(code, msg)) 

    # function to acquire bar data of a given ticker for specified timeframe
    def historicalData(self, req_id, bar):
        t = datetime.datetime.fromtimestamp(int(bar.date))

        # creation bar dictionary for each bar received
        data = {
            'date': t,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': int(bar.volume)
        }

        # Put the data into the queue
        data_queue.put(data)


    # callback when all historical data has been received
    def historicalDataEnd(self, reqId, start, end):
        print(f"end of data {start} {end}")
            
        # update chart once all data has been received
        update_chart()


    # function to check order status - not implementing this yet... reasoning below
    def orderStatus(self, order_id, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        print(f"order status {order_id} {status} {filled} {remaining} {avgFillPrice}") 

        '''API documentation for this function: 
        
        This event is called whenever the status of an order changes. It is also fired after reconnecting to TWS if the client has any open orders.'''   


# writing this function in snake_case as it is not an API function
# this function processes the initial request for retrieving bar data for a given ticker
def get_bar_data(ticker, timeframe):

    # let user know we have received request and are now fetching data
    print(f"getting bar data for {ticker} {timeframe}")

    # create an instance of a Contract, as "reqHistoricalData" requires a Contract object
    contract = Contract()
    contract.ticker = ticker
    contract.secType = 'STK'
    contract.exchange = 'SMART'
    contract.currency = 'USD'
    what_to_show = 'TRADES'
    
    # a lightweight-charts function
    chart.spinner(True)

    # call the API's function to acquire historical data for a given ticker 
    client.reqHistoricalData(
        2, contract, '', '30 D', timeframe, what_to_show, True, 2, False, []
    )

    # force a pause to let the previous function call receive and process some of the data before the script continues acquiring data
    time.sleep(1)
       
    # display the ticker's watermark - a lightweight-charts function   
    chart.watermark(ticker)


# handler for the screenshot button
# the idea here is to be able to capture images of trades for journaling purposes
def take_screenshot(key):
    img = chart.screenshot()
    t = time.time()
    with open(f"screenshot-{t}.png", 'wb') as f:
        f.write(img)


# function to handle order-placing
def place_order(key):
    # get current ticker
    ticker = chart.topbar['ticker'].value

    # create a contract object
    contract = Contract()
    contract.ticker = ticker
    contract.secType = "STK"
    contract.currency = "USD"
    contract.exchange = "SMART"
    
    # create an order object
    order = Order()
    order.orderType = "MKT"
    order.totalQuantity = 1
    
    # get next order id
    client.reqIds(-1)
    time.sleep(2)
    
    # set action to buy or sell depending on key pressed
    # shift+O is for a buy order
    if key == 'O':
        print("buy order")
        order.action = "BUY"

    # shift+P for a sell order
    if key == 'P':
        print("sell order")
        order.action = "SELL"

    # place the order
    if client.order_id:
        print("got order id, placing buy order")
        client.placeOrder(client.order_id, contract, order)


# get new bar data when the user enters a different ticker
def on_search(chart, searched_string):
    get_bar_data(searched_string, chart.topbar['timeframe'].value)
    chart.topbar['ticker'].set(searched_string)


# get new bar data when the user changes timeframes
def on_timeframe_selection(chart):
    print("selected timeframe")
    print(chart.topbar['ticker'].value, chart.topbar['timeframe'].value)
    get_bar_data(chart.topbar['ticker'].value, chart.topbar['timeframe'].value)
    

# callback for when the user changes the position of the horizontal line
def on_horizontal_line_move(chart, line):
    print(f'Horizontal line moved to: {line.price}')


# called when we want to update what is rendered on the chart 
def update_chart():
    global current_lines

    try:
        bars = []
        while True:  # Keep checking the queue for new data
            data = data_queue.get_nowait()
            bars.append(data)
    except queue.Empty:
        print("empty queue")
    finally:
        # once we have received all the data, convert to pandas dataframe
        df = pd.DataFrame(bars)
        print(df)

        # set the data on the chart
        chart.set(df)
        
        if not df.empty:
            # draw a horizontal line at the high
            chart.horizontal_line(df['high'].max(), func=on_horizontal_line_move)

            # if there were any indicator lines on the chart already (eg. SMA), clear them so we can recalculate
            if current_lines:
                for l in current_lines:
                    l.delete()
            
            current_lines = []

            # calculate any new lines to render
            # create a line with SMA label on the chart
            line = chart.create_line(name='SMA 50')
            line.set(pd.DataFrame({
                'time': df['date'],
                f'SMA 50': df['close'].rolling(window=50).mean()
            }).dropna())
            current_lines.append(line)

            # once we get the data back, we don't need a spinner anymore
            chart.spinner(False)


if __name__ == '__main__':
    # create a client object
    client = Client(DEFAULT_HOST, TRADING_PORT, DEFAULT_CLIENT_ID)

    # create chart object, specify display settings
    chart = Chart(width=1000, inner_width=1.0, inner_height=1)

    # hotkey to place a buy order
    chart.hotkey('shift', 'O', place_order)

    # hotkey to place a sell order
    chart.hotkey('shift', 'P', place_order)

    chart.legend(True)
    
    # set up a function to call when searching for ticker
    chart.events.search += on_search

    # set up top bar
    chart.topbar.textbox('ticker', INITIAL_TICKER)

    # give ability to switch between timeframes
    chart.topbar.switcher('timeframe', ('5 mins', '15 mins', '1 hour'), default='5 mins', func=on_timeframe_selection)

    # populate initial chart
    get_bar_data(INITIAL_TICKER, '5 mins')

    # create a button for taking a screenshot of the chart
    chart.topbar.button('screenshot', 'Screenshot', func=take_screenshot)

    # show the chart
    chart.show(block=True)