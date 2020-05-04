from flask import Flask, request
app = Flask(__name__)

@app.route('/', methods=['POST'])
def result():
    print(request.form['foo'])
    return "Received"

app.run()