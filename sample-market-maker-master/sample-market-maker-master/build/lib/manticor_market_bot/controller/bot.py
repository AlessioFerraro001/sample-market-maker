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
        self.toCreate = []
        self.toAmend = []
        self.submitTime = time.time()


    def updateConfigs(self):
        #Download JSON from website
        with open("manticor_market_bot\\config.json", 'r') as j:
            self.config = json.loads(j.read())
        self.config["terminateTime"] = self.config["terminateTime"] + time.time()

    def terminate(self):
        self.didTerminate = True

    def addCreate(self, side):
        newOrder = {}
        if side == "Buy":
            newOrder = {'orderID': self.data.orderID, 'orderQty': 1,
                        'price': self.data.bestBid, 'side': side}
        if side == "Sell":
            newOrder = {'orderID': self.data.orderID, 'orderQty': 1,
                        'price': self.data.bestAsk, 'side': side}
        self.toCreate.append(newOrder)

    def addAmend(self, order):
        newOrder = {}
        if order["side"] == "Buy":
            newOrder = {'orderID': order["orderID"], 'orderQty': 1,
                        'price': self.data.bestBid, 'side': order["side"]}
        if order["side"] == "Sell":
            newOrder = {'orderID': order["orderID"], 'orderQty': 1,
                        'price': self.data.bestAsk, 'side': order["side"]}
        self.toAmend.append(newOrder)

    def submit(self):
        if not self.toCreate == []:
            # TODO: send the orders in bulk
            orderManager.exchange.create_bulk_orders(self.toCreate)
        if not self.toAmend == []:
            # TODO: send to ammend in bulk
            orderManager.exchange.amend_bulk_orders(self.toAmend)
        self.toCreate = []
        self.toAmend = []

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
            if self.submitTime <= time.time() + 30:
                self.submit()
            self.data.update()
            if (self.data.numSell - self.data.numBuy) <= 0 & self.data.cryptoAmount > 0:
                self.didSomethingHappen = True
                # TODO: Send new sell offer
                self.addCreate("Sell")
                self.data.pastOrders.insert(self.data.orderID, Order())
                self.data.pastOrders[self.data.orderID].timestamp = time.time()
                self.data.pastOrders[self.data.orderID].side = "Sell"
                self.data.orderID += 1
            for order in orderManager.exchange.get_orders():
                if order['side'] == "Sell":
                    self.didSomethingHappen = True
                    if (time.time() - self.data.pastOrders[self.data.orderID].timestamp) >= self.config["waitTime"]:
                        # TODO: Resubmit sell offer
                        self.addAmend(order)
                        self.data.pastOrders.insert(self.data.orderID, Order())
                        self.data.pastOrders[self.data.orderID].timestamp = time.time()
                        self.data.pastOrders[self.data.orderID].side = "Sell"
                        self.data.orderID += 1
            if (self.data.numBuy - self.data.numSell) < 0 & self.data.standardAmount >= self.data.bestBid:
                self.didSomethingHappen = True
                # TODO: Send new buy offer
                self.addCreate("Buy")
                self.data.pastOrders.insert(self.data.orderID, Order())
                self.data.pastOrders[self.data.orderID].timestamp = time.time()
                self.data.pastOrders[self.data.orderID].side = "Buy"
                self.data.orderID += 1
            for order in orderManager.exchange.get_orders():
                if order['side'] == "Buy":
                    self.didSomethingHappen = True
                    if (time.time() - self.data.pastOrders) >= self.config["waitTime"]:
                        # TODO: Resubmit buy offer
                        self.addAmend(order)
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
        while orderManager.exchange.get_orders():
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
                if orderManager.exchange.get_orders():
                    # TODO: Resubmit sell offers
                    pass