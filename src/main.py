from flask import Flask, jsonify, request
from models import destinations
from werkzeug.exceptions import BadRequest, HTTPException

app = Flask(__name__)

#IF YOU WANT TO FORMAT YOUR ERROR
# @app.errorhandler(BadRequest)
# def handle_400_error(e):
#     response = {
#         "error": "Bad Request",
#         "message": "bellend.",
#         "status": 400
#     }
#     return jsonify(response), 400

@app.get("/destinations")
def get_destinations():
    return jsonify(destinations)

#adding a new destination
@app.post("/newdestinations")
def add_destination():
    print(request)  
    new_data = request.get_json()
    if not new_data:
        raise BadRequest("Missing data from request!")

    
    new_id = max(d["id"] for d in destinations) + 1
    #if theres no data in req throw 500
    new_destination = {
        "id" : new_id,
        "name" : new_data.get("name"),
        "country" : new_data.get("country"),
        "attractions" : new_data.get("attractions", [])
    }
    destinations.append(new_destination)
    return jsonify(new_destination), 200

@app.delete("/destinations/<id>")
def delete_destination(id):
    destinations.delete(id)
    return jsonify({"status": "deleted", "id": id}), 200



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)