"""Resource class responsible for fetching resources from the Restish server
by resource name.
"""
import pickle
from raisin.box import RESOURCES
from config import PICKLED


class Resource:

    def __init__(self, provider):
        """Store the provider used to fetch the resources."""
        self.provider = provider

    def get(self, name, content_type=PICKLED, kwargs={}):
        """Get a resource from a resource provider"""
        try:
            uri = RESOURCES[name]['uri'] % kwargs
        except KeyError:
            raise
        result = self.provider.get(uri, content_type)
        if not result is None and content_type == PICKLED:
            result = pickle.loads(result)
        return result
