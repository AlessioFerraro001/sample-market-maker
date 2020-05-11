import time, pandas
from manticor_market_bot.model.data import Data
from manticor_market_bot.controller.static_instances import manticoreLog #orderManager
from market_maker.custom_strategy import CustomOrderManager
from decimal import Decimal
from manticor_market_bot.controller.coinmarketcap import getCoin, getPrice

WAIT_TIME = 10

def toNearest(num, round_interval):
    numDec = Decimal(str(round_interval))
    return float((Decimal(round(num / round_interval, 0)) * numDec))

class Bot:
    def __init__(self):
        self.didTerminate = False
        self.orderManager = None
        self.data = Data()
        self.currTime = time.time()
        self.startFunds = 0
        self.lastUpdated = {"bestAsk":self.currTime, "bestBid":self.currTime, "createBulkOrders":self.currTime, "amendBulkOrders":self.currTime, "openOrders":self.currTime, "funds":self.currTime}
        self.bestAsk = 0
        self.sellPos = 0
        self.bestBid = 0
        self.buyPos = 0
        #self.spread = self.bestAsk - self.bestBid
        self.orderPairs = 6
        self.orderStartQty = 100
        self.orderStepQty = 100
        self.position = 0
        self.localAllOrders = {}
        self.localCurrentOrders = {}
        self.localFilledOrders = {}
        self.marketAllOrders = {}
        self.marketCurrentOrders = {}
        self.marketFilledOrders = {}
        self.qntFilled = {}
        self.recentAsks = []
        self.toCreate = []
        self.toAmend = []
        self.maxPosition = 1000
        self.minPosition = -1000
        self.coinName = False
        # self.updateBid()
        # self.updateAsk()

    def initOrderManager(self):
        self.orderManager = CustomOrderManager(self.data.config['symbol'], self.data.config['apiKey'], self.data.config['apiSecret'])

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
        if time.time() - self.lastUpdated["bestAsk"] > -1:
            ticker = self.orderManager.exchange.get_ticker()
            self.bestAsk = getPrice(self.coinName) if self.data.config['dataSource'] == 'CoinMarketCap' else ticker['sell']
            self.recentAsks.append(self.bestAsk)
            if len(self.recentAsks) >= 200:
                del self.recentAsks[100:]
            self.lastUpdated["bestAsk"] = time.time()
            #manticoreLog.info("Best Ask: %s" % self.bestAsk)

    def updateBid(self):
        if time.time() - self.lastUpdated["bestBid"] > -1:
            ticker = self.orderManager.exchange.get_ticker()
            if self.data.config['dataSource'] == "CoinMarketCap":
                self.bestBid = getPrice(self.coinName)
            else:
                self.bestBid = ticker["buy"]
            self.lastUpdated["bestBid"] = time.time()
            #manticoreLog.info("Best Bid: %s" % self.bestBid)

    def updateOrderValues(self):
        self.updateAsk()
        self.updateBid()
        if self.data.config['dataSource'] == "CoinMarketCap":
            self.buyPos = self.bestBid - self.orderManager.instrument['tickSize']
            self.sellPos = self.bestAsk + self.orderManager.instrument['tickSize']
        else:
            self.buyPos = self.bestBid + self.orderManager.instrument['tickSize']
            self.sellPos = self.bestAsk - self.orderManager.instrument['tickSize']

        if self.buyPos == self.orderManager.exchange.get_highest_buy()['price']:
            self.buyPos = self.bestBid
        if self.sellPos == self.orderManager.exchange.get_lowest_sell()['price']:
            self.sellPos = self.bestAsk

        if self.buyPos * (1 + self.data.config['minSpread']) > self.sellPos:
            self.buyPos = (1 - (self.data.config['minSpread'] / 2)) * self.buyPos
            self.sellPos = (1 + (self.data.config['minSpread'] / 2)) * self.sellPos

    def createOrder(self, pos):
        price = self.getOrderPrice(pos)
        newOrder = {}
        quantity = self.orderStartQty + (abs(pos) - 1) * self.orderStepQty
        if pos < 0:
            newOrder = {'orderQty': quantity, 'price': price, 'side': "Buy"}
            #manticoreLog.info("Buy Position: %s" % price)
        else:
            newOrder = {'orderQty': quantity, 'price': price, 'side': "Sell"}
            #manticoreLog.info("Sell Position: %s" % price)
        self.toCreate.append(newOrder)

    #Currently unused, might be deleted
    def amendOrder(self, order):
        newOrder = {}
        if order["side"] == "Buy":
            newOrder = {'clOrdID': order["clOrdID"], 'orderQty': order["orderQty"],
                        'price': self.bestBid + self.orderManager.instrument['tickSize'], 'side': order["side"]}
        if order["side"] == "Sell":
            newOrder = {'clOrdID': order["clOrdID"], 'orderQty': order["orderQty"],
                        'price': self.bestAsk - self.orderManager.instrument['tickSize'], 'side': order["side"]}
        self.toAmend.append(newOrder)

    def getOrderPrice(self, pos):
        price = self.buyPos if pos < 0 else self.sellPos
        if pos < 0:
            pos += 1
        else:
            pos -= 1

        adjPrice = toNearest(price * (1 + self.data.config["aggressiveness"]) ** pos, self.orderManager.instrument['tickSize'])
        # manticoreLog.info("tick size: %s" % orderManager.instrument['tickSize'])
        # manticoreLog.info("Preadjusted: %s" % price)
        # manticoreLog.info("Order Price: %s" % (price * (1 + self.data.config["aggressiveness"]) ** pos))
        lowSell = self.lowestSellOrder()
        if pos < 0 and adjPrice > lowSell:
            adjPrice = lowSell - self.orderManager.instrument['tickSize']
        highBuy = self.highestBuyOrder()
        if pos >= 0 and adjPrice < highBuy:
            adjPrice = highBuy + self.orderManager.instrument['tickSize']

        return adjPrice
        #return toNearest(price * (1 + self.data.config["aggressiveness"]) ** pos, orderManager.instrument['tickSize'])
        #return price * (1 + self.data.config["aggressiveness"]) ** pos

    def submitOrders(self):
        if time.time() - self.lastUpdated["createBulkOrders"] > WAIT_TIME: #TEMP VALUE
            self.updateOrderValues()
            #manticoreLog.info("Placing Orders:")
            orderPos = reversed([i for i in range(1, self.orderPairs)])
            for i in orderPos:
                #if not self.maxPositionCheck():
                self.createOrder(-i)
                #if not self.minPositionCheck():
                self.createOrder(i)
            # for order in self.toCreate:
            #     #.info("Order: %s" % order)
            #     self.localAllOrders[order["clOrdID"]] = order
            #     self.localCurrentOrders[order["clOrdID"]] = order
            buyOrders = [o for o in self.toCreate if o['side'] == "Buy"]
            sellOrders = [o for o in self.toCreate if o['side'] == "Sell"]
            self.toCreate.clear()
            self.lastUpdated["createBulkOrders"] = time.time()
            self.mergeOrders(buyOrders, sellOrders)

    # Currently unused, might be deleted
    def reviseOrders(self):
        if time.time() - self.lastUpdated["amendBulkOrders"] > WAIT_TIME: #TEMP VALUE
            for amended_order in self.toAmend:
                current_order = self.marketAllOrders[amended_order["clOrdID"]]
                if not abs((amended_order['price'] / current_order['price']) - 1) > self.data.config["relistThreshold"]:
                    self.toAmend.remove(amended_order)
            if self.toAmend:
                self.orderManager.exchange.bitmex.amend_bulk_orders(self.toAmend)
            self.lastUpdated["amendBulkOrders"] = time.time()
            for order in self.toAmend:
                self.localAllOrders[order["clOrdID"]] = order
                self.localCurrentOrders[order["clOrdID"]] = order
            self.lastUpdated["amendBulkOrders"] = time.time()

    def mergeOrders(self, buyOrders, sellOrders):
        buy_to_merge = 0
        sell_to_merge = 0
        to_change = []
        to_add = []
        to_remove = []

        self.localUpdate()

        for o in self.marketCurrentOrders:
            if o['side'] == "Buy":
                if buy_to_merge < len(buyOrders):
                    newOrd = buyOrders[buy_to_merge]
                    buy_to_merge += 1
                else:
                    to_remove.append(o)
                    continue
            else:
                if sell_to_merge < len(sellOrders):
                    newOrd = sellOrders[sell_to_merge]
                    sell_to_merge += 1
                else:
                    to_remove.append(o)
                    continue

            if newOrd['orderQty'] != o['leavesQty']:
                self.qntFilled[o['clOrdID']] = self.qntFilled.get(o['clOrdID'], o['orderQty'])
                num_filled = self.qntFilled[o['clOrdID']] - o['leavesQty']
                manticoreLog.info("num_filled: %s" % num_filled)
                manticoreLog.info("price: %s" % o["price"])
                self.qntFilled[o['clOrdID']] = self.qntFilled[o['clOrdID']] - num_filled
                self.data.feeProfit += Decimal(str(o["price"])) * Decimal(str(num_filled)) * Decimal(str(0.000250))
                manticoreLog.info("Fee Profit: %s" % self.data.feeProfit)

            if newOrd['orderQty'] != o['leavesQty'] or abs((newOrd['price'] / o['price']) - 1) > self.data.config[
                "relistThreshold"]:
                to_change.append(
                    {'orderID': o['orderID'], 'orderQty': o['cumQty'] + newOrd['orderQty'], 'price': newOrd['price'],
                     'side': o['side']})

        while buy_to_merge < len(buyOrders):
            to_add.append(buyOrders[buy_to_merge])
            buy_to_merge += 1

        while sell_to_merge < len(sellOrders):
            to_add.append(sellOrders[sell_to_merge])
            sell_to_merge += 1

        if to_change:
            try:
                self.orderManager.exchange.amend_bulk_orders(to_change)
            except:
                return self.submitOrders()

        if to_add:
            self.orderManager.exchange.create_bulk_orders(to_add)

        if to_remove:
            self.orderManager.exchange.cancel_bulk_orders(to_remove)


    def highestBuyOrder(self):
        max = {"price": 0}
        for order in self.toCreate:
            if (order["side"] == "Buy") & (order["price"] > max["price"]):
                max = order
        return max['price']

    def lowestSellOrder(self):
        min = {"price": float("inf")}
        for order in self.toCreate:
            if (order["side"] == "Sell") & (order["price"] < min["price"]):
                min = order
        return min['price']

    def localUpdate(self):
        if time.time() - self.lastUpdated["openOrders"] > -1:  # TEMP VALUE
            self.marketAllOrders = self.orderManager.exchange.bitmex.all_orders()
            self.marketCurrentOrders = self.orderManager.exchange.bitmex.open_orders()
            manticoreLog.info(self.marketCurrentOrders)
            self.marketFilledOrders = self.orderManager.exchange.bitmex.filled_orders()
            manticoreLog.info(self.marketFilledOrders)

            # for o in self.marketCurrentOrders:
            #     self.qntFilled[o['clOrdID']] = self.qntFilled.get(o['clOrdID'], o['orderQty'])
            #     num_filled = self.qntFilled[o['clOrdID']] - o['leavesQty']
            #     self.qntFilled[o['clOrdID']] = self.qntFilled[o['clOrdID']] - num_filled
            #     self.data.feeProfit += Decimal(str(o["price"] * num_filled)) * Decimal(str(0.0250))

            self.lastUpdated["openOrders"] = time.time()
            #manticoreLog.info("Filled Orders: %s" % self.marketFilledOrders)

    def updateProfit(self):
        if time.time() - self.lastUpdated["funds"] > 10:
            self.data.updateProfit(self.startFunds, self.orderManager.exchange.bitmex.funds()["walletBalance"])
            #manticoreLog.info("Available funds: %s" % orderManager.exchange.bitmex.funds()['availableMargin'])
            #manticoreLog.info("Total equity value: %s" % orderManager.exchange.bitmex.funds()['amount'])
            #manticoreLog.info("Available funds: %s" % self.orderManager.exchange.bitmex.funds())
            manticoreLog.info("Total Profit: %s" % self.data.marketProfitTotal)

            self.lastUpdated["funds"] = time.time()

    def minPositionCheck(self):
        if self.orderManager.exchange.get_delta() <= self.minPosition:
            return True
        return False

    def maxPositionCheck(self):
        if self.orderManager.exchange.get_delta() >= self.maxPosition:
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
        self.initOrderManager()
        if self.data.config["dataSource"] == "CoinMarketCap":
            self.coinName = getCoin(self.data.config["symbol"])
        self.startFunds = self.orderManager.exchange.bitmex.funds()["walletBalance"]
        if self.startFunds >= self.data.cryptoAmount:
            manticoreLog.info("Funds: %s" % self.orderManager.exchange.bitmex.funds())
            self.run()
        #TODO: spit back out an error

    def run(self):
        #print("test")
        #orderManager.exchange.cancel_all_orders()
        while not self.didTerminate:
            if time.time() - self.currTime > self.data.config['terminateTime']:
                self.didTerminate = True
            self.sanityCheck()
            #self.updateOrderValues()
            #self.localUpdate()
            self.updateProfit()
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
        self.orderManager.exchange.cancel_alciml_orders()