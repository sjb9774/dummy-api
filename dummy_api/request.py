class RouteRequest:

    def __init__(
            self,
            request_path: str = None,
            request_method: str = None,
            query_parameters: dict = None,
            request_body: dict = None
    ):
        self.request_path = request_path
        self.request_method = request_method or "GET"
        self.query_parameters = query_parameters or {}
        self.request_body = request_body or {}

    def get_query_params(self) -> dict:
        return self.query_parameters.copy() if self.query_parameters else {}

    def get_request_path(self) -> str:
        return self.request_path

    def get_request_method(self) -> str:
        return self.request_method

    def get_request_body(self) -> dict:
        return self.request_body