import time, math, pandas
from manticor_market_bot.model.data import Data
from manticor_market_bot.model.order import Order
from manticor_market_bot.controller.static_instances import orderManager

class Bot:
    def __init__(self):
        self.didTerminate = False
        self.data = Data()
        self.data.updateConfigs()
        self.lastUpdated = { "bestAsk": 0.0, "bestBid": 0.0, "createBulkOrders": 0.0, "amendBulkOrders": 0.0, "open_orders": 0.0}
        self.bestAsk = 0
        self.updateAsk()
        self.bestBid = 0
        self.updateBid()
        #self.spread = self.bestAsk - self.bestBid
        self.orderPairs = 6
        self.position = 0
        self.localAllOrders = {}
        self.localCurrentOrders = {}
        self.localFilledOrders = {}
        self.marketAllOrders = {}
        self.recentAsks = []
        self.toCreate = []
        self.toAmend = []

    #Not yet used, ask about how
    def sanitize(self, response):
        if response == {"error": {"message": "The system is currently overloaded. Please try again later.", "name": "HTTPError"}}:
            return False
        return True

    def sanityCheck(self):
        if orderManager.bitmex.funds() >= self.data.standardAmount + (self.data.cryptoAmount * self.bestAsk): #UNSURE
            self.didTerminate = True
        elif orderManager.bitmex.get_orders() != self.localAllOrders:
            self.didTerminate = True

    def updateAsk(self):
        if (self.lastUpdated["bestAsk"] - time.time()) > 60.0:
            ticker = orderManager.get_ticker()
            self.bestAsk = ticker["sell"]
            self.recentAsks.append(self.bestAsk)
            if len(self.recentAsks) >= 200:
                del self.recentAsks[100:]
            self.lastUpdated["bestAsk"] = time.time()

    def updateBid(self):
        if (self.lastUpdated["bestBid"] - time.time()) > 60.0:
            ticker = orderManager.get_ticker()
            self.bestBid = ticker["buy"]
            self.lastUpdated["bestBid"] = time.time()

    def createOrder(self, pos):
        newOrder = {}
        if pos >= 0:
            newOrder = {'orderQty': 1, 'price': self.getOrderPrice(pos), 'side': "Buy"}
        if pos < 0:
            newOrder = {'orderQty': 1, 'price': self.getOrderPrice(-pos), 'side': "Sell"}
        self.toCreate.append(newOrder)

    def amendOrder(self, order):
        newOrder = {}
        if order["side"] == "Buy":
            newOrder = {'orderID': order["orderID"], 'orderQty': order["orderQty"],
                        'price': self.bestBid + orderManager.instrument['tickSize'], 'side': order["side"]}
        if order["side"] == "Sell":
            newOrder = {'orderID': order["orderID"], 'orderQty': order["orderQty"],
                        'price': self.bestAsk - orderManager.instrument['tickSize'], 'side': order["side"]}
        self.toAmend.append(newOrder)

    def getOrderPrice(self, pos):
        price = self.bestBid if pos >= 0 else self.bestAsk
        if pos < 0:
            pos += 1
        else:
            pos -= 1
        #return math.toNearest(price * (1 + self.data.config["aggressiveness"]) ** pos, orderManager.instrument['tickSize'])
        return price * (1 + self.data.config["aggressiveness"]) ** pos

    def submitOrders(self):
        if self.lastUpdated["create_bulk_orders"] - time.time() > 60: #TEMP VALUE
            #orderPos = reversed([for i in range(1, self.orderPairs)])
            #FOR NOW
            orderPos = []
            for i in range(1, self.orderPairs):
                orderPos.append(i)
            orderPos.reverse()
            for i in orderPos:
                if not self.maxPositionCheck():
                    self.createOrder(i)
                if not self.minPositionCheck():
                    self.createOrder(-i)
            orderManager.bitmex.create_bulk_orders([self.toCreate])
            for order in self.toCreate:
                self.localAllOrders[order["orderID"]] = order
                self.localCurrentOrders[order["orderID"]] = order
            self.lastUpdated["create_bulk_orders"] = time.time()
            self.reviseOrders()

    def reviseOrders(self):
        if self.lastUpdated["amend_bulk_orders"] - time.time() > 60: #TEMP VALUE
            for amended_order in self.toAmend:
                current_order = self.marketAllOrders[amended_order["orderID"]]
                if not abs((amended_order['price'] / current_order['price']) - 1) > self.data.config["relistThreshold"]:
                    self.toAmend.remove(amended_order)
            orderManager.bitmex.amend_bulk_orders([self.toAmend])
            self.lastUpdated["amend_bulk_orders"] = time.time()
            for order in self.toAmend:
                self.localAllOrders[order["orderID"]] = order
                self.localCurrentOrders[order["orderID"]] = order

    def highestBuyOrder(self):
        max = {"price": 0}
        for order in self.localCurrentOrders:
            if (order["side"] == "Buy") & (order["price"] > max["price"]):
                max = order
        return max

    def lowestSellOrder(self):
        min = {"price": float("inf")}
        for order in self.localCurrentOrders:
            if (order["side"] == "Sell") & (order["price"] < min["price"]):
                min = order
        return min

    def localUpdate(self):
        if self.lastUpdated["open_orders"] - time.time() > 60:  # TEMP VALUE
            self.marketAllOrders = orderManager.bitmex.open_orders()
        for order in self.marketAllOrders:
            if (order['side'] == "Sell") & (order['ordStatus'] == "Filled:"):
                self.data.numBuy += 1
                self.data.standardAmount -= order.price
                self.data.cryptoAmount += order.quantity
                self.localCurrentOrders.pop(order["orderID"], None)
                self.localFilledOrders[order["orderID"]] = order
            if (order['side'] == "Buy") & (order['ordStatus'] == "Filled:"):
                self.data.numSell += 1
                self.data.standardAmount += order.price
                self.data.cryptoAmount -= order.quantity
                self.localCurrentOrders.pop(order["orderID"], None)
                self.localFilledOrders[order["orderID"]] = order

    def minPositionCheck(self):
        if orderManager.exchange.get_delta <= self.data.config["minPosition"]:
            return True
        return False

    def maxPositionCheck(self):
        if orderManager.exchange.get_delta >= self.data.config["maxPosition"]:
            return True
        return False

    def test_run(self):
        print("Termination time: %f" % self.data.config["terminateTime"])
        while not self.didTerminate:
            self.updateAsk()
            self.updateBid()
            print("Trades are occuring!")
            print("Current time: %f" % time.time())
            print("Best Ask: %f / Best Bid: %f" % (self.bestAsk, self.bestBid))
            if self.data.config["terminateTime"] <= time.time():
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
            self.updateAsk()
            self.updateBid()
            self.data.rateOfChange(self.recentAsks)
            if self.data.marketTrend == "Low":
                self.position = 1
            elif self.data.marketTrend == "High":
                recentRates = pandas.Series(self.recentAsks[(len(self.recentAsks)-11):]).pct_change()
                recentRateOfChange = recentRates.sum() / recentRates.size
                if recentRateOfChange > .015:
                    self.position = -1
            else:
                self.submitOrders()
            self.sanityCheck()