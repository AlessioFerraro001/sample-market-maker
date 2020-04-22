from manticor_market_bot.model.order import Order
from manticor_market_bot.controller.static_instances import orderManager

class Data:
    def __init__(self, config):
        # The current highest price to buy cryptocurrency
        self.bestBid = self.updateBid()
        # The current lowest price to sell cryptocurrency
        self.bestAsk = self.updateAsk()
        # The id of the most recent order
        self.orderID = 0
        # The list of all our active orders with the time they were sent and if they were buy or sell
        self.pastOrders = []
        # The list of orders that have been completed
        self.filledOrders = set()
        # The amount of standard currency we have to buy with
        self.standardAmount = config["walletAmountStandard"]
        # The amount of cryptocurrency we have to sell
        self.cryptoAmount = config["walletAmountCrypto"]
        # The number of buy orders we have completed by now
        self.numBuy = 0
        # The number of sell orders we have completed so far
        self.numSell = 0

    def updateBid(self, source = None):
        ticker = orderManager.get_ticker()
        self.bestBid = ticker["buy"]

    def updateAsk(self, source = None):
        ticker = orderManager.get_ticker()
        self.bestAsk = ticker["sell"]

    def update(self, source = None):
        ticker = orderManager.get_ticker()
        self.bestBid = ticker["buy"]
        self.bestAsk = ticker["sell"]

    def addOrder(self, isBuy):
        self.pastOrders.append(Order(isBuy))
        self.orderID += 1

    def deleteOrder(self, id):
        self.pastOrders.pop(id)
        self.orderID -= 1