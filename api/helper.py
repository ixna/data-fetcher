import jwt
import functools
import flask
from .error import TokenError, RoleError, ConversionError
import requests
import config
import os
import time

def prep_cache_file():
    if not os.path.isfile(config.CURRCONV_CACHE_KEY):
        with open(config.CURRCONV_CACHE_KEY,'a') as f:
            pass

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

def get_cache():
    rate = None
    expiry = None
    with open(config.CURRCONV_CACHE_KEY, "r") as cache_data:
        try:
            rate, expiry = cache_data.read().split(" ")
            rate = int(float(rate))
            expiry = int(expiry)
        except:
            pass
        
    if expiry is not None:
        # invalidate data cache if more than 10 minutes passed,
        if expiry + (10 * 60) < int(time.time()):
            rate = None
    
    return rate

def set_cache(price):
    expiry = int(time.time())

    # format data cache so it can be used by get_cache func
    data = f"{price} {expiry}"
    with open(config.CURRCONV_CACHE_KEY, "w") as cache_data:
        cache_data.write(data)

def mandiri_usdtoidr():
    # get cookie
    get_cookie = requests.get("https://www.bankmandiri.co.id/kurs", 
        headers={'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS \
            X 10.15; rv:75.0) Gecko/20100101 Firefox/75.0'})
    cookie = get_cookie.headers['Set-Cookie']

    # build request
    url = ('https://www.bankmandiri.co.id/web/guest/kurs?'
        'p_p_id=Exchange_Rate_Portlet_INSTANCE_9070nSEKk62r&'
        'p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&'
        'p_p_resource_id=calculateCurrency&p_p_cacheability=cacheLevelPage')
    
    data = {
        '_Exchange_Rate_Portlet_INSTANCE_9070nSEKk62r_value': '1', 
        '_Exchange_Rate_Portlet_INSTANCE_9070nSEKk62r_from': '204', 
        '_Exchange_Rate_Portlet_INSTANCE_9070nSEKk62r_to': '61', 
        '_Exchange_Rate_Portlet_INSTANCE_9070nSEKk62r_jenis': 'BUY'
    }

    headers = {
        'User-Agent' : ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; '
            'rv:75.0) Gecko/20100101 Firefox/75.0'), 
        'Referer': 'https://www.bankmandiri.co.id/kurs', 
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 
        'Origin': 'https://www.bankmandiri.co.id', 
        'Cookie': cookie}
    
    try:
        data_raw = requests.post(
            url, headers=headers, data=data, timeout=30)
        
        currency_rate = data_raw.json()["value"]
        return currency_rate
    except:
        return None

def usdtoidr():
    """Get currency exchange usd to idr rate"""
    # Get data from cache
    rate = get_cache()

    # Pull data from server if cache expired
    if rate is None: 
        rate = mandiri_usdtoidr()

    if rate is None:
        rate_data = requests.get(config.CURRCONV_URL, timeout=30)
        if rate_data.status_code == 200:
            rate_json = rate_data.json()
            rate = rate_json["USD_IDR"]
            
        else:
            raise ConversionError
    
    if rate is not None:
        # save to cache
        set_cache(rate) 

    return int(rate)

def convert_price(price_idr:int) -> str:
    per_usd = usdtoidr()
    price_usd = price_idr/per_usd
    
    # Limit to 2 digit precision float
    price_usd_fmt = f"{price_usd:0.2f}"
    return price_usd_fmt

def update_data(data_json):
    for data in data_json:
        # Handle for None valued price 
        price_idr = data["price"] or ""
        price_usd = None
        if price_idr.isdigit():
            # All price to be processed must be in numeric format
            price_usd = convert_price(int(price_idr))
            
        data["price_usd"] = price_usd