import time, math, pandas
from manticor_market_bot.model.data import Data
from manticor_market_bot.model.order import Order
from manticor_market_bot.controller.static_instances import orderManager, manticoreLog
from decimal import Decimal
WAIT_TIME = 5

def toNearest(num, round_interval):
    numDec = Decimal(str(round_interval))
    return float((Decimal(round(num / round_interval, 0)) * numDec))

class Bot:
    def __init__(self):
        self.didTerminate = False
        self.data = Data()
        self.currTime = time.time()
        self.lastUpdated = {"bestAsk":self.currTime, "bestBid":self.currTime, "createBulkOrders":self.currTime, "amendBulkOrders":self.currTime, "openOrders":self.currTime}
        self.bestAsk = 0
        self.sellPos = 0
        self.updateAsk()
        self.bestBid = 0
        self.buyPos = 0
        self.updateBid()
        #self.spread = self.bestAsk - self.bestBid
        self.orderPairs = 6
        self.orderStartQty = 100
        self.orderStepQty = 100
        self.position = 0
        self.localAllOrders = {}
        self.localCurrentOrders = {}
        self.localFilledOrders = {}
        self.marketAllOrders = {}
        self.recentAsks = []
        self.toCreate = []
        self.toAmend = []
        self.maxPosition = 100
        self.minPosition = -100


    #Not yet used, ask about how
    def sanitize(self, response):
        if response == {"error": {"message": "The system is currently overloaded. Please try again later.", "name": "HTTPError"}}:
            return False
        return True

    def sanityCheck(self):
        #if orderManager.bitmex.get_orders() != self.localAllOrders:
        #    self.didTerminate = True
        return True

    def updateAsk(self):
        if time.time() - self.lastUpdated["bestAsk"] > WAIT_TIME - 1:
            ticker = orderManager.exchange.get_ticker()
            self.bestAsk = ticker["sell"]
            self.recentAsks.append(self.bestAsk)
            if len(self.recentAsks) >= 200:
                del self.recentAsks[100:]
            self.lastUpdated["bestAsk"] = time.time()
            manticoreLog.info("Best Ask: %s" % self.bestAsk)

    def updateBid(self):
        if time.time() - self.lastUpdated["bestBid"] > WAIT_TIME - 1:
            ticker = orderManager.exchange.get_ticker()
            self.bestBid = ticker["buy"]
            self.lastUpdated["bestBid"] = time.time()
            manticoreLog.info("Best Bid: %s" % self.bestBid)

    def updateOrderValues(self):
        self.updateAsk()
        self.updateBid()
        self.buyPos = self.bestBid + orderManager.instrument['tickSize']
        self.sellPos = self.bestAsk - orderManager.instrument['tickSize']

        if self.buyPos == orderManager.exchange.get_highest_buy()['price']:
            self.buyPos = self.bestBid
        if self.sellPos == orderManager.exchange.get_lowest_sell()['price']:
            self.sellPos = self.bestAsk

        if self.buyPos * (1 + self.data.config['minSpread']) > self.sellPos:
            self.buyPos = (1 - (self.data.config['minSpread'] / 2)) * self.buyPos
            self.sellPos = (1 + (self.data.config['minSpread'] / 2)) * self.sellPos

    def createOrder(self, pos):
        price = self.getOrderPrice(pos)
        newOrder = {}
        quantity = self.orderStartQty + (abs(pos) - 1) * self.orderStepQty
        if pos < 0:
            newOrder = {'orderQty': 1, 'price': price, 'side': "Buy"}
            #manticoreLog.info("Buy Position: %s" % price)
        else:
            newOrder = {'orderQty': 1, 'price': price, 'side': "Sell"}
            #manticoreLog.info("Sell Position: %s" % price)
        self.toCreate.append(newOrder)

    def amendOrder(self, order):
        newOrder = {}
        if order["side"] == "Buy":
            newOrder = {'clOrdID': order["clOrdID"], 'orderQty': order["orderQty"],
                        'price': self.bestBid + orderManager.instrument['tickSize'], 'side': order["side"]}
        if order["side"] == "Sell":
            newOrder = {'clOrdID': order["clOrdID"], 'orderQty': order["orderQty"],
                        'price': self.bestAsk - orderManager.instrument['tickSize'], 'side': order["side"]}
        self.toAmend.append(newOrder)

    def getOrderPrice(self, pos):
        price = self.buyPos if pos < 0 else self.sellPos
        if pos < 0:
            pos += 1
        else:
            pos -= 1
        # TODO: make toNearest
        return toNearest(price * (1 + self.data.config["aggressiveness"]) ** pos, orderManager.instrument['tickSize'])
        #return price * (1 + self.data.config["aggressiveness"]) ** pos

    def submitOrders(self):
        if time.time() - self.lastUpdated["createBulkOrders"] > WAIT_TIME: #TEMP VALUE
            #manticoreLog.info("Placing Orders:")
            orderPos = reversed([i for i in range(1, self.orderPairs)])
            for i in orderPos:
                #if not self.maxPositionCheck():
                    self.createOrder(-i)
                #if not self.minPositionCheck():
                    self.createOrder(i)
            if self.toCreate:
                orderManager.exchange.bitmex.create_bulk_orders(self.toCreate)
            for order in self.toCreate:
                #.info("Order: %s" % order)
                self.localAllOrders[order["clOrdID"]] = order
                self.localCurrentOrders[order["clOrdID"]] = order
            self.lastUpdated["createBulkOrders"] = time.time()
            self.toCreate = []
            #self.reviseOrders()

    def reviseOrders(self):
        if time.time() - self.lastUpdated["amendBulkOrders"] > WAIT_TIME: #TEMP VALUE
            for amended_order in self.toAmend:
                current_order = self.marketAllOrders[amended_order["clOrdID"]]
                if not abs((amended_order['price'] / current_order['price']) - 1) > self.data.config["relistThreshold"]:
                    self.toAmend.remove(amended_order)
            if self.toAmend:
                orderManager.exchange.bitmex.amend_bulk_orders(self.toAmend)
            self.lastUpdated["amendBulkOrders"] = time.time()
            for order in self.toAmend:
                self.localAllOrders[order["clOrdID"]] = order
                self.localCurrentOrders[order["clOrdID"]] = order
            self.lastUpdated["amendBulkOrders"] = time.time()

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
        if time.time() - self.lastUpdated["openOrders"] > WAIT_TIME:  # TEMP VALUE
            self.marketAllOrders = orderManager.exchange.bitmex.open_orders()
            for order in self.marketAllOrders:
                if (order['side'] == "Sell") & (order['ordStatus'] == "Filled:"):
                    self.data.numBuy += 1
                    self.data.standardAmount -= order["price"] * order["quantity"]
                    self.data.cryptoAmount += order["quantity"]
                    self.data.feeProfit += (order["price"] * order["quantity"]) * 0.0250
                    self.localCurrentOrders.pop(order["orderID"], None)
                    self.localFilledOrders[order["orderID"]] = order
                if (order['side'] == "Buy") & (order['ordStatus'] == "Filled:"):
                    self.data.numSell += 1
                    self.data.standardAmount += order["price"] * order["quantity"]
                    self.data.cryptoAmount -= order["quantity"]
                    self.data.feeProfit += (order["price"] * order["quantity"]) * 0.0250
                    self.localCurrentOrders.pop(order["orderID"], None)
                    self.localFilledOrders[order["orderID"]] = order
            self.lastUpdated["openOrders"] = time.time()
            manticoreLog.info("Fee Profit: %s" % self.data.feeProfit)


    def minPositionCheck(self):
        if orderManager.exchange.get_delta() <= self.minPosition:
            return True
        return False

    def maxPositionCheck(self):
        if orderManager.exchange.get_delta() >= self.maxPosition:
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
        if orderManager.exchange.bitmex.funds()["availableMargin"] >= self.data.cryptoAmount:
            self.run()
        #TODO: spit back out an error

    def run(self):
        #print("test")
        #orderManager.exchange.cancel_all_orders()
        while not self.didTerminate:
            if time.time() - self.currTime > self.data.config['terminateTime']:
                self.didTerminate = False
                break
            self.sanityCheck()
            self.updateOrderValues()
            self.localUpdate()
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
