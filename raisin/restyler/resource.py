"""Resource class responsible for fetching resources from the Restish server
by resource name.
"""
import pickle
from raisin.box import RESOURCES
from config import PICKLED
from http_parser.http import NoMoreData

class Resource:
    """Fetch RESTful resource using a provider implementing the method:
    def get(uri, content_type)
    """

    def __init__(self, provider):
        """Store the provider used to fetch the resources."""
        self.provider = provider

    def get(self, name, content_type=PICKLED, kwargs=None):
        """Get a resource from a resource provider"""
        try:
            resource = RESOURCES[name]
        except KeyError:
            raise
        uri = resource['uri']
        if not kwargs is None:
            uri = uri % kwargs
        result = None
        try:
            result = self.provider.get(uri, content_type)
        except NoMoreData:
            # Catch the following exception:
            # http_parser-0.7.5-py2.6-linux-x86_64.egg/http_parser/http.py'
            # line 70 in _check_headers_complete
            # raise NoMoreData("Can't parse headers")
            # NoMoreData: Can't parse headers
            pass 
        if not result is None and content_type == PICKLED:
            result = pickle.loads(result)
        return result
