from manticor_market_bot.controller.bot import Bot
from flask import Flask, request, make_response, jsonify
app = Flask(__name__)

def _build_cors_prelight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "*")
    response.headers.add("Access-Control-Allow-Methods", "*")
    return response

def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

@app.route('/', methods=['POST','OPTIONS'])
def result():
    if request.method == "OPTIONS":  # CORS preflight
        return _build_cors_prelight_response()
    elif request.method == "POST":  # The actual request following the preflight
        mantibot = Bot()
        mantibot.data.updateConfigs(request.form.to_dict())
        print(mantibot.data.config)
        mantibot.start()
        return _corsify_actual_response(jsonify("RECEIVED!"))

app.run(host="0.0.0.0", port=5000)

