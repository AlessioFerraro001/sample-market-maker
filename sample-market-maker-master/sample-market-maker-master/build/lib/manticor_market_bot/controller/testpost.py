import requests
r = requests.post("http://localhost:5000", data={'foo': 'bar'})
# And done.
print(r.text) # displays the result body.