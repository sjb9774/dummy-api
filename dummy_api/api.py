from dummy_api.app import app
from dummy_api.routes import RoutesProvider
from flask import request, jsonify
import os


def index():
    return f"Welcome to dummy-api"


def setup_routes(routes_file_path: str):
    route_provider = RoutesProvider(routes_file_path)

    def api(path):
        response = route_provider.get_route_response_data(
            path,
            query_parameters=request.args.to_dict(),
            request_method=request.method,
            request_body=request.json if request.method in ["POST", "PUT"] else None
        )
        return jsonify(response)

    index_route = app.route("/")
    index_route(index)
    api_route = app.route("/api/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
    api_route(api)
