from functools import wraps

def cors(func):
    """
    Enable CORS for local devs

    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        request.setHeader('Access-Control-Allow-Origin', '*')
        request.setHeader('Access-Control-Allow-Methods', 'GET,POST')
        request.setHeader('Access-Control-Allow-Headers', 'x-prototype-version,x-requested-with,Authorization')
        request.setHeader('Access-Control-Max-Age', 2520)
        request.setHeader('Content-type', 'application/json')
        return func(request, *args, **kwargs)
    return wrapper