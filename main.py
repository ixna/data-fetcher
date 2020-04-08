import flask
import jwt
import config
import functools

def factory():
    app = flask.Flask(__name__)
    app.config.from_object(config)
    return app

def auth(admin=False):
    def decorator(func):
        @functools.wraps(func)
        def wrapper_validate(*args, **kwargs):
            claims = validate_token()
            if admin is True and claims['role'] != "admin":
                # Raise error if the access requirement is admin level, but user's role is not
                raise RoleError("Restricted access")
            return func(*args, **kwargs)
        return wrapper_validate
    return decorator

def validate_token() -> str:
    auth_string = flask.request.headers.get("Authorization", "")
    auth_fields = auth_string.strip().split()
    if len(auth_fields) == 2 and auth_fields[0].lower() == "bearer":
        token = auth_fields[1]
        try:
            claims = jwt.decode(token, config.JWT_SECRET, algorithms=['HS256'])
            return claims
        except:
            raise TokenError(message="Token is invalid, check your request")
    raise TokenError(message="Authorization header is in invalid format, check your request")

class BaseError(Exception):
    def __init__(self, status=400, message=""):
        self.status = status
        self.message = message

class TokenError(BaseError):
    def __init__(self, message):
        self.message = message
    
class RoleError(BaseError):
    def __init__(self, message):
        super().__init__(status=401)
        self.message = message


if __name__ == "__main__":
    app = factory()

    
    @app.errorhandler(Exception)
    def handle_exception(e):
        """Custom error handling"""
        if isinstance(e, BaseError):        
            return flask.jsonify({"message": e.message}), e.status
        else:
            # For debugging purpose can log the original error (e)
            # Or alternatively using traceback module
            import traceback
            app.logger.info(traceback.format_exc())

            return flask.jsonify({"message": "Unhandled error occured"}), 500

    @app.route("/data", methods=["GET"])
    @auth()
    def get_data():
        int("a")
        return "Haloo data"

    @app.route("/summary", methods=["GET"])
    @auth(admin=True)
    def get_aggregate():
        return "Okesip"

    @app.route("/me", methods=["GET"])
    def check_token():
        claims = validate_token()
        return flask.jsonify(claims)

    app.run()