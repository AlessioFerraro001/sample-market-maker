import requests
r = requests.post("http://localhost:5000", data={
  "dataSource": "BitMEX",
  "currencyStandard": "USD",
  "currencyCrypto": "XBT",
  "walletAmountCrypto": 500,
  "minSpread": 0.01,
  "marketLowThreshold": -0.5,
  "marketHighThreshold": 0.5,
  "relistThreshold": 0.01,
  "aggressiveness": 0.005,
  "terminateTime": 120,
  "lossyShutdown": False
})
# And done.
print(r.text) # displays the result body.