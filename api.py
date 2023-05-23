from .app import app
from .routes import RoutesProvider
from flask import request


route_provider = RoutesProvider("./routes.json")


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
