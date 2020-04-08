class BaseError(Exception):
    def __init__(self, status=400, message=""):
        self.status = status
        self.message = message

class TokenError(BaseError):
    def __init__(self, message):
        super().__init__(status=400)
        self.message = message
    
class RoleError(BaseError):
    def __init__(self, message):
        super().__init__(status=401)
        self.message = message

class ConversionError(BaseError):
    def __init__(self):
        super().__init__(status=503, message="Conversion rate service is unavailable")

class DataSourceError(BaseError):
    def __init__(self):
        super().__init__(status=503, message="Data source service is unavailable")
