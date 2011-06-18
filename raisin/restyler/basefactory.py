class BaseFactory(object):
    def __init__(self, request=None):
        request.environ['HTTP_HOST'] = request.registry.settings['fix_http_host']