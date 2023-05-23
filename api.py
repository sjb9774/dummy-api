from app import app
from routes import RoutesProvider


route_provider = RoutesProvider("./routes.json")


@app.route("/")
def index():
    return "Welcome to dummy-api"


@app.route("/api/<path:path>")
def api_route(path):
    response = route_provider.get_route_response_data(path)
    return response
