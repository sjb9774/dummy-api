from dummy_api.app import app
from dummy_api.routes import RoutesProvider
from flask import request
import os


route_provider = RoutesProvider(os.path.join(os.path.dirname(__file__), "./routes.json"))


@app.route("/")
def index():
    return f"Welcome to dummy-api"


@app.route("/api/<path:path>")
def api_route(path):
    response = route_provider.get_route_response_data(
        path,
        query_parameters=request.args.to_dict(),
        request_method=request.method,
        request_body=request.form.to_dict()
    )
    return response
