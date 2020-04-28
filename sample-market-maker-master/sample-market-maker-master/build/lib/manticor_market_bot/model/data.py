import json, time, pandas

class Data:
    def __init__(self):
        # The json that holds all the user configured values
        self.config = {}
        self.updateConfigs()
        # The amount of standard currency we have to buy with
        self.standardAmount = 0
        # The amount of cryptocurrency we have to sell
        self.cryptoAmount = self.config["walletAmountCrypto"]
        # The number of buy orders we have completed by now
        self.numBuy = 0
        # The number of sell orders we have completed so far
        self.numSell = 0
        # The direction of the rate of change of the market's prices
        self.marketTrend = "Side"
        # The profit made from market trades
        self.marketProfit = 0
        # The profit made from BitMEX's fees for placing orders
        self.feeProfit = 0

    def updateConfigs(self):
        # Download JSON from website
        with open("manticor_market_bot\\config.json", 'r') as j:
            self.config = json.loads(j.read())
        self.config["terminateTime"] = self.config["terminateTime"] + time.time()

    def rateOfChange(self, asks):
        rates = pandas.Series(asks).pct_change()
        avgRate = rates.sum() / rates.size
        if avgRate > 0.02: #TEMP VALUE
            self.marketTrend = "High"
        if avgRate < -0.02: #TEMP VALUE
            self.marketTrend = "Low"
        else:
            self.marketTrend = "Side"