import flask
import jwt
import redis
import config
import functools
import requests
from error import (
    BaseError, 
    ConversionError,
    DataSourceError,
)
import pandas
from helper import auth, validate_token, process_data

def factory():
    app = flask.Flask(__name__)
    app.config.from_object(config)
    
    # Register routes
    @app.errorhandler(Exception)
    def handle_exception(e):
        """Custom error handling"""
        import traceback
        app.logger.info(traceback.format_exc())

        if isinstance(e, BaseError):        
            return flask.jsonify({"message": e.message}), e.status
        else:
            # For debugging purpose can log the original error (e)
            return flask.jsonify({"message": "Unhandled error occured"}), 500

    @app.route("/data", methods=["GET"])
    @auth()
    def get_data():
        # Get list user
        response = requests.get(app.config.get("DATA_FETCH_URL"), timeout=30)
        # Make sure server responded OK
        if response.status_code == 200:
            data_dict = response.json()
            
            # Processing dictionary, inplace memory processing no need return 
            process_data(data_dict)

            return flask.jsonify(data_dict)
        else:
            raise DataSourceError


    @app.route("/summary", methods=["GET"])
    @auth(admin=True)
    def get_aggregate():
        # Get list user
        response = requests.get(app.config.get("DATA_FETCH_URL"), timeout=30)
        # Make sure server responded OK
        if response.status_code == 200:
            df = pandas.read_json(response.content)
            data = df.groupby([
                    pandas.Grouper(key='timestamp', freq='W-MON'), 
                    "area_provinsi"
                ])['price']\
                .agg([("Min", "min"), ("Max", "max"), ("Mean", "mean"), ("Median", "median")])\
                .reset_index()\
                .sort_values("area_provinsi")

            return flask.jsonify(data.to_dict("records"))
        else:
            raise DataSourceError
        
    @app.route("/me", methods=["GET"])
    def check_token():
        claims = validate_token()
        return flask.jsonify(claims)

    return app

if __name__ == "__main__":
    app = factory()
    app.run()