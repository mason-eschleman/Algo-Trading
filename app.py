import time
from ibapi.client import *
from ibapi.wrapper import *



from threading import Thread

class IBClient(EWrapper, EClient):
     
    def __init__(self, host, port, client_id):
        EClient.__init__(self, self) 
        
        self.connect(host, port, client_id)

        thread = Thread(target=self.run)
        thread.start()


def error(self, reqId: TickerId, errorTime: int, errorCode: int, 
          errorString: str, advancedOrderRejectJson = ""):
    
    print("Error. Id:", reqId, errorTime, "Code:", 
          errorCode, "Msg:", errorString, "AdvancedOrderRejectJson:", 
          advancedOrderRejectJson)



client = IBClient('127.0.0.1', 7497, 1)

time.sleep(1)

contract = Contract()
contract.symbol = 'NQ'
contract.secType = 'FUT'
contract.exchange = 'GLOBEX'
contract.currency = 'USD'
what_to_show = 'TRADES'

client.reqHistoricalData(
    2, contract, '', '30 D', '5 mins', what_to_show, True, 2, False, []
)

time.sleep(1)