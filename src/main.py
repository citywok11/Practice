from flask import Flask, jsonify, request
from models import destinations

app = Flask(__name__)

@app.get("/destinations")
def get_destinations():
    return jsonify(destinations)

#adding a new destination
@app.post("/newdestinations")
def add_destination():
    print(request)
    new_data = request.get_json()
    new_id = max(d["id"] for d in destinations) + 1
    new_destination = {
        "id" : new_id,
        "name" : new_data.get("name"),
        "country" : new_data.get("country"),
        "attractions" : new_data.get("attractions", [])
    }
    destinations.append(new_destination)
    return jsonify(new_destination), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)