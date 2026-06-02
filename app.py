"""
Application that utilizes Interactive Brokers' API for live data retrieval and TradingView's 
Lightweight Charts API to visualize and chart the data.

The ultimate goal is to implement my personal trading strategy into this program and bring
everything together to automating the trading process.

Attributes:
    LIVE_TRADING (bool): Flag to switch between live and paper trading accounts.
    LIVE_TRADING_PORT (int): TWS network port dedicated to live accounts.
    PAPER_TRADING_PORT (int): TWS network port dedicated to paper accounts.
    TRADING_PORT (int): The default active connection port.
    INITIAL_TICKER (str): The stock ticker loaded by default on application start.
    DEFAULT_HOST (str): Local IP address running the TWS application.
    DEFAULT_CLIENT_ID (int): Unique identifier for this API client session.
    data_queue (queue.Queue): Threaded queue managing incoming historical bars.
    current_lines (list): Active visual indicators currently rendered on the chart.
"""


import time, datetime
import queue
import pandas as pd
from threading import Thread
from lightweight_charts import Chart

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.client import Contract, Order
from ibapi.tag_value import TagValue

LIVE_TRADING = False

LIVE_TRADING_PORT = 7496
PAPER_TRADING_PORT = 7497

TRADING_PORT = PAPER_TRADING_PORT
if LIVE_TRADING:
    TRADING_PORT = LIVE_TRADING_PORT

INITIAL_TICKER = "AAPL"

DEFAULT_HOST = '127.0.0.1'
DEFAULT_CLIENT_ID = 1

data_queue = queue.Queue()
current_lines = []


class Client(EWrapper, EClient):

    """
    API client that handles data retrieval from IBKR DB and routes orders as well.

    Class inherits from:
        EWrapper: receives asynchronous messages from Trader Workstation (TWS).
        EClient: sends requests to TWS.

    Attributes:
        order_id (int): the unique ID associated with a specific order.    
    """

    def __init__(self, host, port, client_id):
        """
        Initializes the Client and connects it to the TWS server.

        Args:
            host (str): Host address of the TWS/IB Gateway instance.
            port (int): Network port used by TWS for API connections.
            client_id (int): Unique identifier for this API session.

        """

        EClient.__init__(self, self) 
        
        self.connect(host, port, client_id)
        
        thread = Thread(target=self.run)
        thread.start()

    
    def nextValidId(self, orderId: int):
        """
        Callback fired when TWS provides next valid order ID. 

        Args:
            orderID (int): the unique ID associated with a specific order.  
        """

        super().nextValidId(orderId)
        self.order_id = orderId
        print(f"next valid id is {self.order_id}")

    
    def error(self, req_id, code, msg, advancedOrderRejectJson, errorTime=""):
        """
        Handle error messages received from TWS.

        Args:
            req_id (int): Request ID associated with the error.
            code (int): IBKR error code.
            msg (str): Human-readable error message.
            advancedOrderRejectJson (str): Additional order rejection details.
            errorTime (str): Timestamp of the error (if provided).
        """

        if code in [2104, 2106, 2158]:
            print(msg)
        else:
            print('Error {}: {}'.format(code, msg)) 


    def historicalData(self, req_id, bar):
        """
        Callback for each historical bar received from TWS.

        Args:
            req_id (int): Request ID associated with the data.
            bar (BarData): OHLCV bar object returned by IBKR.
        """
        
        t = datetime.datetime.fromtimestamp(int(bar.date))

        data = {
            'date': t,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': int(bar.volume)
        }

        data_queue.put(data)


    def historicalDataEnd(self, reqId, start, end):
        """
        Callback fired when all historical data for a request has been received.

        Args:
            reqId (int): Request ID.
            start (str): Start timestamp of the data range.
            end (str): End timestamp of the data range.
        """

        print(f"end of data {start} {end}")
            
        update_chart()


    # function to check order status - not implementing this yet... reasoning below
    def orderStatus(self, order_id, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        print(f"order status {order_id} {status} {filled} {remaining} {avgFillPrice}") 

        """
        API documentation for this function: 
            This event is called whenever the status of an order changes. It is also fired 
            after reconnecting to TWS if the client has any open orders.

        Args:
            order_id (int): Order identifier.
            status (str): Current order status.
            filled (float): Quantity filled so far.
            remaining (float): Quantity remaining.
            avgFillPrice (float): Average fill price.
            permId (int): Permanent order ID.
            parentId (int): Parent order ID (if applicable).
            lastFillPrice (float): Price of the most recent fill.
            clientId (int): Client ID associated with the order.
            whyHeld (str): Reason the order is being held.
            mktCapPrice (float): Market cap price.   

        """
        


def get_bar_data(ticker, timeframe):
    """
    Request historical bar data for a given ticker and timeframe.

    Args:
        ticker (str): Stock symbol to request data for.
        timeframe (str): Bar size (e.g., '5 mins', '1 hour').
    """

    print(f"getting bar data for {ticker} {timeframe}")

    contract = Contract()
    contract.ticker = ticker
    contract.secType = 'STK'
    contract.exchange = 'SMART'
    contract.currency = 'USD'
    what_to_show = 'TRADES'
    
    chart.spinner(True)

    client.reqHistoricalData(
        2, contract, '', '30 D', timeframe, what_to_show, True, 2, False, []
    )

    # force a pause to let the previous function call receive and process some of the data before the script continues acquiring data
    time.sleep(1)
       
    chart.watermark(ticker)


def take_screenshot(key):
    """
    Capture and save a screenshot of the current chart view.

    Args:
        key (str): Hotkey pressed to trigger the screenshot.
    """
    # the idea here is to be able to capture images of trades for journaling purposes

    img = chart.screenshot()
    t = time.time()
    with open(f"screenshot-{t}.png", 'wb') as f:
        f.write(img)


def place_order(key):
    """
    Place a market order for the currently displayed ticker.

    Args:
        key (str): Hotkey pressed ('O' for buy, 'P' for sell).
    """
    ticker = chart.topbar['ticker'].value

    contract = Contract()
    contract.ticker = ticker
    contract.secType = "STK"
    contract.currency = "USD"
    contract.exchange = "SMART"
    
    order = Order()
    order.orderType = "MKT"
    order.totalQuantity = 1

    client.reqIds(-1)
    time.sleep(2)
    
    if key == 'O':
        print("buy order")
        order.action = "BUY"

    if key == 'P':
        print("sell order")
        order.action = "SELL"

    if client.order_id:
        print("got order id, placing buy order")
        client.placeOrder(client.order_id, contract, order)


def on_search(chart, searched_string):
    """
    Handle ticker search events from the chart UI.

    Args:
        chart (Chart): Chart instance.
        searched_string (str): User-entered ticker symbol.
    """

    get_bar_data(searched_string, chart.topbar['timeframe'].value)
    chart.topbar['ticker'].set(searched_string)


def on_timeframe_selection(chart):
    """
    Handle timeframe selection changes from the chart UI.

    Args:
        chart (Chart): Chart instance.
    """

    print("selected timeframe")
    print(chart.topbar['ticker'].value, chart.topbar['timeframe'].value)
    get_bar_data(chart.topbar['ticker'].value, chart.topbar['timeframe'].value)
    

def on_horizontal_line_move(chart, line):
    """
    Callback fired when a horizontal line is moved on the chart.

    Args:
        chart (Chart): Chart instance.
        line (Line): The moved line object.
    """

    print(f'Horizontal line moved to: {line.price}')


def update_chart():
    """
    Process queued historical bar data, update the chart, and render indicators.

    This function:
        - Drains the data queue
        - Converts bars to a DataFrame
        - Updates the chart with OHLCV data
        - Draws horizontal lines and indicators (e.g., SMA)
    """

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
    
    client = Client(DEFAULT_HOST, TRADING_PORT, DEFAULT_CLIENT_ID)

    chart = Chart(width=1000, inner_width=1.0, inner_height=1)

    chart.hotkey('shift', 'O', place_order)

    chart.hotkey('shift', 'P', place_order)

    chart.legend(True)

    chart.events.search += on_search

    chart.topbar.textbox('ticker', INITIAL_TICKER)

    chart.topbar.switcher('timeframe', ('5 mins', '15 mins', '1 hour'), default='5 mins', func=on_timeframe_selection)

    get_bar_data(INITIAL_TICKER, '5 mins')

    chart.topbar.button('screenshot', 'Screenshot', func=take_screenshot)

    chart.show(block=True)