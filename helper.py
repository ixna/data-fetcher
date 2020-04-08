import jwt
import functools
import flask
import redis
from error import TokenError, RoleError, ConversionError
import requests
import config

# init redis to be used in application
redis_cache = redis.Redis(host='localhost', port=6379, db=0)

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

def usdtoidr():
    """Get currency exchange usd to idr rate"""
    # Get data from cache
    rate = redis_cache.get(config.CURRCONV_CACHE_KEY)

    # Pull data from server if cache expired
    if rate is None: 
        rate_data = requests.get(config.CURRCONV_URL, timeout=30)
        if rate_data.status_code == 200:
            rate_json = rate_data.json()
            rate = rate_json["USD_IDR"]
            redis_cache.setex(config.CURRCONV_CACHE_KEY, 10 * 60, rate)
        else:
            raise ConversionError
    return int(rate)

def convert_price(price_idr:int) -> str:
    per_usd = usdtoidr()
    price_usd = price_idr/per_usd
    
    # Limit to 2 digit precision float
    price_usd_fmt = f"{price_usd:0.2f}"
    return price_usd_fmt

def process_data(data_json):
    for data in data_json:
        # Handle for None valued price 
        price_idr = data["price"] or ""
        price_usd = None
        if price_idr.isdigit():
            # All price to be processed must be in numeric format
            price_usd = convert_price(int(price_idr))
            
        data["price_usd"] = price_usd