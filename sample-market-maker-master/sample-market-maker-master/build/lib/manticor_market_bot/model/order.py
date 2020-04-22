import time

class Order:
    def __init__(self):
        self.orderId = 0
        self.symbol = ""
        self.side = ""
        self.quantity = 0
        self.price = 0
        self.settlCurrency = ""
        self.currency = ""
        self.ordStatus = ""
        self.timestamp = 0