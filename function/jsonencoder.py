from flask import jsonify
import json
from bson.objectid import ObjectId



def json_encoder(array):
    return jsonify(json.loads(JSONEncoder().encode(array)))

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)
