"""Box Base factory"""

from config import JSON
from config import CSV
from utils import render_javascript
from utils import render_chartoptions
from utils import render_description
from raisin.box import RESOURCES_REGISTRY
from page import Restyler
from page import get_resource

class Cells(object):
    """Provides information on what cells charts are located in."""

    def __init__(self, chart_name):
        self.chart_name = chart_name

    def get_cells(self):
        return [self.chart_name]

    def get_column_for_chart(self, chart_id):
        return self.chart_name
        
    def get_new_row_for_chart(self, chart_id):
        return False
        
class Layout(object):
    """Provides information on the layout and its cells."""

    def __init__(self, request):
        box_id = request.matchdict['box_id_with_extension']
        self.chart_name = box_id.split('.')[0]

    def get_cells(self):
        return Cells(self.chart_name)

class Box:
    """Shows one box on the page"""

    def __init__(self, request):
        self.layout = Layout(request)
        cells = self.layout.get_cells()
        self.restyler = Restyler(request, cells)


        self.body = ''
        self.javascript = ''
        if request.matchdict == {'box_id_with_extension': u'favicon.ico'}:
            return

        self.charts = None
        self.chart_type = None

        box_id = request.matchdict['box_id_with_extension']
        self.chart_name, self.chart_format = box_id.split('.')

        # Go through the registry, and find the resource for this box
        # XXX This should be a dictionary
        for resource in RESOURCES_REGISTRY:
            if resource[0] == self.chart_name:
                self.resources = [resource]

        if self.chart_format == 'html':
            self.render_html(request)
        elif self.chart_format == 'csv':
            self.render_csv(request)
        elif self.chart_format == 'json':
            self.render_json(request)
        else:
            print "Format not supported %s" % self.chart_format
            raise AttributeError

    def render_html(self, request):
        """Render a resource as HTML"""
        packages = set(['corechart'])
        chart = self.restyler.get_chart_infos(request)[0]
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
            # Prepare the packages are needed by the google chart tools
            if chart['charttype'] == 'Table':
                packages.add(chart['charttype'].lower())
            chart['chartoptions']['is3D'] = False
            rendered = render_chartoptions(chart['chartoptions'])
            chart['chartoptions_rendered'] = rendered

        rendered = render_description(request,
                                      chart.get('description', ''),
                                      chart.get('description_type', ''))
        chart['description_rendered'] = rendered

        if 'chartoptions' in chart:
            # Depending on the chart type different JavaScript libraries
            # need to be used
            self.chart_type = chart['charttype']

            # Sometimes it is necessary to override the width and height
            # completely from the outside by just passing the width and height
            # through the url. This is useful when doing screenshots.
            if 'width' in request.GET:
                # width can be overridden from the request query
                width = int(request.GET['width'])
                chart['chartoptions']['width'] = width
            if 'height' in request.GET:
                # height can be overridden from the request query
                height = int(request.GET['height'])
                chart['chartoptions']['height'] = height

            # Now render the chart options with the new values
            rendered = render_chartoptions(chart['chartoptions'])
            chart['chartoptions_rendered'] = rendered

        # Use the chart id without a postfix as we do for boxes on a page
        chart['div_id'] = chart['id']
        self.charts = [chart]
        self.javascript = render_javascript(self.charts, packages)

    def render_csv(self, request):
        """Render a resource as CSV"""
        self.body = get_resource(self.chart_name,
                                 CSV,
                                 request.matchdict)

    def render_json(self, request):
        """Render a resource as JSON"""
        self.body = get_resource(self.chart_name,
                                 JSON,
                                 request.matchdict)
