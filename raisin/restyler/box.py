import os
from basefactory import BaseFactory
from config import JSON
from config import CSV
from utils import render_javascript
from utils import render_chartoptions
from utils import render_description
from utils import get_chart_infos
from utils import get_resource_directly
from raisin.box import resources_registry
from raisin.box import BOXES
from raisin.resource.root import stats_registry

class Box(BaseFactory):
    """
    Shows one box on the page.
    """

    def __init__(self, request):
        if request.matchdict == {'box_id_with_extension': u'favicon.ico'}:
            return

        BaseFactory.__init__(self, request)
        self.charts = None
        self.chart_type = None
        
        # Check input coming from URl, preventing SQL injections and access to unintended files            
        for key, value in request.matchdict.items():
            if key == 'box_id_with_extension':
                if '.' in value:
                    self.chart_name, self.chart_format = value.split('.')
                else:
                    self.chart_name = None
                    self.chart_format = None
                if not self.chart_name in BOXES.keys():
                    print self.chart_name
                    raise AttributeError
                if not self.chart_format in ['html', 'csv', 'json']:
                    raise AttributeError
            elif key == 'project_name':
                if not value.replace('_', '').isalnum():
                    raise AttributeError
                self.project_name = value
            elif key == 'parameter_list':
                if not value.replace('-', '').replace('_', '').isalnum():
                    raise AttributeError
                self.parameter_list = value
            elif key == 'parameter_values':
                if not value.replace('-', '').replace('_', '').isalnum():
                    raise AttributeError
                self.parameter_values = value
            elif key == 'run_name':
                if not value.replace('-', '').isalnum():
                    raise AttributeError
                self.run_name = value
            elif key == 'lane_name':
                if not value.replace('-', '').isalnum():
                    raise AttributeError
                self.lane_name = value
            elif key == 'experiment_statistics_name':
                if not value in ('overview', 'read', 'mapping', 'expression', 'splicing', 'discovery'):
                    raise AttributeError
                self.experiment_statistics_name = value
            elif key == 'run_statistics_name':
                if not value in ('overview', 'read', 'mapping', 'expression', 'splicing', 'discovery'):
                    raise AttributeError
                self.run_statistics_name = value
            elif key == 'lane_statistics_name':
                if not value in ('overview', 'read', 'mapping', 'expression', 'splicing', 'discovery'):
                    raise AttributeError
                self.lane_statistics_name = value
            else:
                print key, value
                raise AttributeError               
            
        # Go through the registry, and take only the resources that are referenced from the cells of the layout
        for resource in resources_registry:
            if resource[0] == self.chart_name:
                self.resource = resource

        if self.chart_format == 'html':            
            packages = set(['corechart'])
            charts = []
            chart_infos = get_chart_infos([self.resource], request.matchdict)
            if len(chart_infos) == 0:
                raise AttributeError
            for chart_info in chart_infos:
                chart = chart_info['chart']
                method = chart_info['method']
                method(self, chart)
                if chart.has_key('charttype') and chart.has_key('data'):
                    if chart['charttype'] == 'Table':
                        packages.add(chart['charttype'].lower())
                    self.javascript = render_javascript([chart,], packages)
    
            # Render the chart to JSon
            if not chart.has_key(JSON) or chart[JSON] is None:
                 pass
            elif not chart.has_key('charttype'):
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
            if chart.has_key('chartoptions'):
                # Depending on the chart type different JavaScript libraries need to be used
                self.chart_type = chart['charttype']
    
                # Sometimes it is necessary to override the width and height completely from
                # the outside by just passing the width and height through the url
                # This is useful when doing screenshots.
                if request.queryvars.has_key('width'):
                    # width can be overridden from the request query
                    chart['chartoptions']['width'] = int(request.queryvars['width'])
                if request.queryvars.has_key('height'):
                    # height can be overridden from the request query
                    chart['chartoptions']['height'] = int(request.queryvars['height'])

                # Now render the chart options with the new values
                chart['chartoptions_rendered'] = render_chartoptions(chart['chartoptions'])

            # Use a proper id for the chart when not rendered with any other divs
            chart['div_id'] = chart['id']
            self.charts = [chart]
            javascript = render_javascript(self.charts, packages)
            self.javascript = javascript
        elif self.chart_format == 'csv':
            self.body = get_resource_directly(self.chart_name, CSV, request.matchdict)
        elif self.chart_format == 'json':
            self.body = get_resource_directly(self.chart_name, JSON, request.matchdict)
        elif self.chart_format == 'ico':
            self.body = ""
        else:
            print "Format not supported %s" % self.chart_format 
            raise AttributeError
            