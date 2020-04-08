import flask
import jwt
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

def validate_token(auth_string:str) -> str:
    auth_fields = auth_string.strip().split()
    schema = auth_fields[0].lower()
    if schema == "bearer":
        return auth_fields[1]
    return ""

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
        auth_string = flask.request.headers.get("Authorization")
        token = validate_token(auth_string)
        if not token:
            return flask.jsonify({"message": "Authorization header is missing, check your request"}), 400
        
        try:
            claims = jwt.decode(token, config.JWT_SECRET, algorithms=['HS256'])
        except:
            return flask.jsonify({"message": "Invalid authorization token, check your request"}), 400
        return flask.jsonify(claims)

    app.run()