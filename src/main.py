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


@app.delete("/destinations/soft-delete/<id>")
def soft_delete_destination(id):
    is_soft_deleted = destinations.soft_delete(id)
    return jsonify({"status": "soft delete", "id": id, "is_soft_deleted": is_soft_deleted}), 200

@app.put("/destinations/undelete-delete/<id>")
def undo_soft_delete_destination(id):
    is_soft_deleted = destinations.undelete_delete(id)
    return jsonify({"status": "undone soft delete", "id": id, "is_soft_deleted": is_soft_deleted}), 200



@app.get("/new_row")
def add_new_row():
    try:
        is_deleted = destinations.add_new_row()
        return jsonify({"is_deleted": is_deleted})
    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)