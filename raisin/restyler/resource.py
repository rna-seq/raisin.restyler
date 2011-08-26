"""Resource class responsible for fetching resources from the Restish server
by resource name.
"""
import pickle
from raisin.box import RESOURCES
from config import PICKLED


class Resource:
    """Fetch RESTful resource using a provider implmenting the method: 
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
        result = self.provider.get(uri, content_type)
        if not result is None and content_type == PICKLED:
            result = pickle.loads(result)
        return result
