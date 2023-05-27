from dummy_api.api import setup_routes, app
import os


file_path = os.environ.get("ROUTES_FILE_PATH", "new_routes.json")
abspath = os.path.join(os.path.dirname(__file__), file_path)


setup_routes(file_path)
