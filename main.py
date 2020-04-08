import flask
import jwt
import requests
import config
import functools

def factory():
    app = flask.Flask(__name__)
    app.config.from_object(config)
    return app

def validate(func):
    @functools.wraps(func)
    def wrapper_validate(*args, **kwargs):
        pass
        return func(*args, **kwargs)
    return wrapper_validate


if __name__ == "__main__":
    app = factory()
    @app.route("/data", methods=["GET"])
    @validate
    def get_data():
        print("Haloo data")

    @app.route("/summary", methods=["GET"])
    @validate
    def get_aggregate():
        print("Okesip")

    @app.route("/me", methods=["GET"])
    def check_token():
        params = flask.request.headers.get("token")
        if not params:
            return flask.Response(400, "Token is missing, check your request")
        check_token_service_addr = config.CHECK_TOKEN_SERVICE
        data = dict(token=params.get("token"))
        response = requests.post(check_token_service_addr, json=data)
        return flask.jsonify(response.json())

    app.run()