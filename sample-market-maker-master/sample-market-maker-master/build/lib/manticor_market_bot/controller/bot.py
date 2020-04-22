import time, json
from manticor_market_bot.model.data import Data
from manticor_market_bot.model.order import Order
from manticor_market_bot.controller.static_instances import orderManager

class Bot:
    def __init__(self):
        self.didSomethingHappen = False
        self.didTerminate = False
        self.config = {}
        self.updateConfigs()
        self.data = Data(self.config)


    def updateConfigs(self):
        #Download JSON from website

        with open("manticor_market_bot\\config.json", 'r') as j:
            self.config = json.loads(j.read())
        self.config["terminateTime"] = self.config["terminateTime"] + time.time()

    def terminate(self):
        self.didTerminate = True

    def test_run(self):
        print("Termination time: %f" % self.config["terminateTime"])
        while not self.didTerminate:
            self.data.update()
            print("Trades are occuring!")
            print("Current time: %f" % time.time())
            print("Best Ask: %f / Best Bid: %f" % (self.data.bestAsk, self.data.bestBid))
            if self.config["terminateTime"] <= time.time():
                self.didTerminate = True
                print("Trades have concluded!")
            else:
                print("-------Waiting 10 secs-------")
                time.sleep(10)

    def start(self):
        #placeholders
        self.run()

    def run(self):
        while not self.didTerminate:
            self.data.update()
            if (self.data.numSell - self.data.numBuy) <= 0 & self.data.cryptoAmount > 0:
                self.didSomethingHappen = True
                # TODO: Send new sell offer
                self.data.pastOrders.insert(self.data.orderID, Order())
                self.data.pastOrders[self.data.orderID].timestamp = time.time()
                self.data.pastOrders[self.data.orderID].side = "Sell"
                self.data.orderID += 1
            for order in orderManager.exchange.get_orders():
                if order['side'] == "Sell":
                    self.didSomethingHappen = True
                    if (time.time() - self.data.pastOrders) >= self.config["waitTime"]:
                        # TODO: Resubmit sell offer
                        self.data.pastOrders.insert(self.data.orderID, Order())
                        self.data.pastOrders[self.data.orderID].timestamp = time.time()
                        self.data.pastOrders[self.data.orderID].side = "Sell"
                        self.data.orderID += 1
            if (self.data.numBuy - self.data.numSell) < 0 & self.data.standardAmount >= self.data.bestBid:
                self.didSomethingHappen = True
                # TODO: Send new buy offer
                self.data.pastOrders.insert(self.data.orderID, Order())
                self.data.pastOrders[self.data.orderID].timestamp = time.time()
                self.data.pastOrders[self.data.orderID].side = "Buy"
                self.data.orderID += 1
            for order in orderManager.exchange.get_orders():
                if order['side'] == "Buy":
                    self.didSomethingHappen = True
                    if (time.time() - self.data.pastOrders) >= self.config["waitTime"]:
                        # TODO: Resubmit buy offer
                        self.data.pastOrders.insert(self.data.orderID, Order())
                        self.data.pastOrders[self.data.orderID].timestamp = time.time()
                        self.data.pastOrders[self.data.orderID].side = "Buy"
                        self.data.orderID += 1
            if not self.didSomethingHappen:
                # TODO: Warn user of insufficient funds
                pass
            # ASK ABOUT COMBINING THESE WITH PREVIOUS GET_ORDERS()
            for order in orderManager.exchange.get_orders():
                if order['side'] == "Sell" & order['ordStatus'] == "Filled:":
                    self.data.numBuy += 1
                    self.data.standardAmount -= order.price
                    self.data.cryptoAmount += order.quantity
                    self.data.pastOrders.remove(self.data.orderID)
            for order in orderManager.exchange.get_orders():
                if order['side'] == "Buy" & order['ordStatus'] == "Filled:":
                    self.data.numSell += 1
                    self.data.standardAmount += order.price
                    self.data.cryptoAmount -= order.quantity
                    self.data.pastOrders.remove(self.data.orderID)
            # TODO: If rate of change is too positive
            # TODO: If rate of change is too negative
        # TODO: Cancel all buy orders
        # TODO: Place sell orders for all currently possessed crypto
        while not orderManager.exchange.get_orders() == []:
            if time.time() - self.config["terminateTime"] > 5400:
                if self.config["lossyShutdown"]:
                    pass
                    # TODO: If "current offer" - (self.config["aggressiveness"] * (self.data.bestAsk - self.data.bestBid)) > self.data.bestBid:
                        # TODO: Resubmit sell offer
                    # TODO: Else: "Accept best bid offer"
                else:
                    pass
                    # TODO: Email user and shut down
            else:
                time.sleep(self.configs["waitTime"])
                if not orderManager.exchange.get_orders() == []:
                    # TODO: Resubmit sell offers
                    pass