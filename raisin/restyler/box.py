"""Box Base factory"""

import re
from config import JSON
from config import CSV
from utils import render_javascript
from utils import render_chartoptions
from utils import render_description
from utils import get_chart_infos
from utils import get_resource_directly
from raisin.box import RESOURCES_REGISTRY
from raisin.box import BOXES



class Box(object):
    """Shows one box on the page"""

    def __init__(self, request):
        if request.matchdict == {'box_id_with_extension': u'favicon.ico'}:
            return

        self.charts = None
        self.chart_type = None
        
        self.chart_name, self.chart_format = request.matchdict['box_id_with_extension'].split('.')

        # Go through the registry, and find the resource for this box
        for resource in RESOURCES_REGISTRY:
            if resource[0] == self.chart_name:
                self.resources = [resource]

        if self.chart_format == 'html':
            packages = set(['corechart'])
            chart_infos = get_chart_infos(self, request)
            if len(chart_infos) == 0:
                raise AttributeError
            for chart_info in chart_infos:
                chart = chart_info['chart']
                method = chart_info['method']
                method(self, chart)
                if 'charttype' in chart and 'data' in chart:
                    if chart['charttype'] == 'Table':
                        packages.add(chart['charttype'].lower())
                    self.javascript = render_javascript([chart, ], packages)

            # Render the chart to JSon
            if not JSON in chart or chart[JSON] is None:
                pass
            elif not 'charttype' in chart:
                pass
            else:
                chart['data'] = chart[JSON]
                # Prepare the packages that need to be loaded for google chart tools
                if chart['charttype'] == 'Table':
                    packages.add(chart['charttype'].lower())
                chart['chartoptions']['is3D'] = False
                chart['chartoptions_rendered'] = render_chartoptions(chart['chartoptions'])
            chart['description_rendered'] = render_description(request,
                                                               chart.get('description', ''),
                                                               chart.get('description_type', ''))
            if 'chartoptions' in chart:
                # Depending on the chart type different JavaScript libraries need to be used
                self.chart_type = chart['charttype']

                # Sometimes it is necessary to override the width and height completely from
                # the outside by just passing the width and height through the url
                # This is useful when doing screenshots.
                if 'width' in request.GET:
                    # width can be overridden from the request query
                    chart['chartoptions']['width'] = int(request.GET['width'])
                if 'height' in request.GET:
                    # height can be overridden from the request query
                    chart['chartoptions']['height'] = int(request.GET['height'])

                # Now render the chart options with the new values
                chart['chartoptions_rendered'] = render_chartoptions(chart['chartoptions'])

            # Use the chart id without a postfix as we do for boxes on a page
            chart['div_id'] = chart['id']
            self.charts = [chart]
            self.javascript = render_javascript(self.charts, packages)
        elif self.chart_format == 'csv':
            self.body = get_resource_directly(self.chart_name,
                                              CSV,
                                              request.matchdict)
        elif self.chart_format == 'json':
            self.body = get_resource_directly(self.chart_name,
                                              JSON,
                                              request.matchdict)
        elif self.chart_format == 'ico':
            self.body = ""
        else:
            print "Format not supported %s" % self.chart_format
            raise AttributeError
