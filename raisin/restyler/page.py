import urlparse
import pickle

from basefactory import BaseFactory
from config import JSON
from config import PICKLED
from utils import render_javascript
from utils import render_chartoptions
from utils import render_description
from utils import get_chart_infos
from utils import get_resource_directly
from raisin.box import resources_registry
from raisin.page import PAGES

class Page(BaseFactory):

    def __init__(self, request, ):
        BaseFactory.__init__(self, request)
        self.project_name    = request.matchdict.get('project_name',    None)
        self.parameter_list = request.matchdict.get('parameter_list', None)
        self.parameter_values = request.matchdict.get('parameter_values', None)
        self.run_name = request.matchdict.get('run_name', None)
        if self.run_name is None:
            self.statistics_name = request.matchdict.get('experiment_statistics_name', None)
        else:
            self.statistics_name = request.matchdict.get('run_statistics_name', None)        
        self.absolute_url = urlparse.urljoin(request.application_url, urlparse.urlparse(request.url).path)
        if not self.absolute_url.endswith('/'):
            self.absolute_url = self.absolute_url + '/'

        # The layout configures the charts to be shown on the page
        if self.project_name is None:
            self.layout = PAGES['homepage']
        elif self.parameter_list is None:
            self.layout = PAGES['project']
        elif self.run_name is None:
            self.layout = PAGES['experiment_statistics']
        else:
            self.layout = PAGES['run_statistics']
        
        self.breadcrumbs = []
        if self.layout.has_key('breadcrumbs'):
            if type(self.layout['breadcrumbs']) == type(''):
                self.layout['breadcrumbs']=[self.layout['breadcrumbs']]
            for item in self.layout['breadcrumbs']:
                if item == 'homepage':
                    url = request.application_url + '/'
                    crumb = {'title': 'Projects', 'url':url}
                    self.breadcrumbs.append(crumb)
                elif item == 'project':
                    url = '/project/%s/experiment' % self.project_name
                    crumb = {'title': 'Project: %s' % self.project_name, 
                             'url':request.application_url + url}
                    self.breadcrumbs.append(crumb)
                elif item == 'parameters':
                    url = '/project/%s/%s/%s/statistics/%s' % (self.project_name, 
                                                               self.parameter_list, 
                                                               self.parameter_values, 
                                                               self.statistics_name)
                    crumb = {'title': 'Experiment: %s' % self.parameter_values,
                             'url':request.application_url + url}
                    self.breadcrumbs.append()

        if not self.parameter_list is None and self.run_name is None:
            self.items = {}
            self.items['title'] = 'RNASeq Pipeline Runs'
            self.items['level'] = 'Experiment'
            self.items['toggle'] = 'Show the individual %s for this %s' % (self.items['title'], self.items['level'])
            experiment_runs = get_resource_directly('experiment_runs', PICKLED, request.matchdict)
            if experiment_runs is None:
                experiment_runs = {'table_data':[], 
                                   'table_description': [('Project Id', 'string'), 
                                                         ('Experiment Id', 'string'), 
                                                         ('Run Id', 'string'), 
                                                         ('Run Url', 'string')]
                                   }
            else:
                experiment_runs = pickle.loads(experiment_runs)                
            self.items['list'] = []
            for item in experiment_runs['table_data']:
                self.items['list'].append({'title':item[2], 
                                           'url':request.application_url + item[3][:-len('overview')] + self.statistics_name})

        if self.layout.has_key('tabbed_views'):
            self.tabs = []
            for tab in self.layout['tabbed_views']:
                if self.run_name is None:
                    path = '/project/%s/%s/%s/statistics/%s/' % (self.project_name,
                                                                 self.parameter_list,
                                                                 self.parameter_values,
                                                                 tab)
                    url = request.application_url + path
                else:
                    path = '/project/%s/%s/%s/run/%s/statistics/%s/' % (self.project_name,
                                                                        self.parameter_list,
                                                                        self.parameter_values,
                                                                        self.run_name,
                                                                        tab)
                    url = request.application_url + path
                self.tabs.append({'id': tab, 
                                  'title': self.layout[tab]['title'], 
                                  'current': tab == self.statistics_name, 
                                  'url':url})
        
        if self.parameter_list is None:
            view = self.layout
        else:
            if self.layout.has_key(self.statistics_name):
                view = self.layout[self.statistics_name]
            else:
                view = self.layout[self.layout['tabbed_views'][0]]
                       
        # The names in the cells of the layout correspond to the charts 
        cells = []
        # Remember which columns the cells occupy
        self.columns_for_cells = {}
        # For each cell, remember whether it starts a new row
        self.new_row_for_cells = {}
        if type(view['rows']) == type(''):
            view['rows'] = [view['rows']]
        for row in view['rows']:
            # Check the number of cells in the row isn't too big
            columns = view[row]
            if type(columns['columns']) == type(''):                
                cells.append(columns['columns'])                
                self.columns_for_cells[columns['columns']] = view['cols'][0] 
            else:
                if len(columns['columns']) > len(view['cols']):
                    raise AttributeError, "Warning: The number of rows is too big: %s %s" % (columns['columns'], view['cols'])
                i = 0
                for column in columns['columns']:
                    # Store whether this column is the start or not of a new row
                    if i == 0:
                        self.new_row_for_cells[column] = True
                    cells.append(column)
                    if self.columns_for_cells.has_key(column):
                        # There is already a column occupied by this item
                        self.columns_for_cells[column] = self.columns_for_cells[column] + view['cols'][i]
                    else:
                        self.columns_for_cells[column] = view['cols'][i]
                    i = i + 1

        # We need to assemble all of the resources needed on the page
        self.resources = []
        
        # And keep track of any that were not found
        unknown = set(cells)
        
        # Go through the registry, and take only the resources that are referenced from the cells of the layout
        for resource in resources_registry:
            if resource[0] in cells:
                if resource[0] in unknown:
                    # This is a known resource, so remove it from the set of unknown
                    unknown.remove(resource[0])
                # Avoid duplicates
                if not resource in self.resources:
                    self.resources.append(resource[:])                

        if len(unknown) > 0:
            print "Unknown resources: %s" % unknown
            raise AttributeError
        
        self.packages, self.charts = self.get_packages_and_charts(request)

        if len(self.charts) == 0:
            return None            
        javascript = render_javascript([chart for chart in self.charts if (chart.has_key('charttype') and chart.has_key('data'))], self.packages)
        self.javascript = javascript

    def get_packages_and_charts(self, request):    
        packages = set(['corechart'])
        charts = []
        # We need a generic way of getting the variables encoded in the url
        # Fortunately repoze.bfg provides them for us in request.urlvars:
        chart_infos = get_chart_infos(self.resources, request.matchdict)
        for chart_info in chart_infos:
            chart = chart_info['chart']
            method = chart_info['method']
            if set(chart_info['predefined_content_types']) == set(chart_info['successful_content_types']):
                # When all content types are present, the augmentation should work fine
                # and the chart content can be prepared
                method(self, chart)
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
                    if chart.has_key('charttype'):
                        # The downloads are always relative to the current url
                        chart['csv_download_url'] = self.absolute_url + "%s.csv" % chart['id']
                        chart['html_download_url'] = self.absolute_url + "%s.html" % chart['id']
            chart['module_id'] = self.columns_for_cells[chart['id']]
            if self.new_row_for_cells.get(chart['id'], False):
                chart['module_style'] = style="clear: both;"
            else:
                chart['module_style'] = ""
            chart['description_rendered'] = render_description(request, chart.get('description', ''), chart.get('description_type', ''))
            chart['div_id'] = chart['id'] + '_div'
            charts.append(chart)
        return packages, charts

    def Title(self):
        title = "Project: %s" % self.project_name
        if not self.parameter_values is None:
            title = "Experiment: %s" % self.parameter_values
        if not self.run_name is None:
            title = "RNASeq Pipeline Run: %s" % self.run_name
        return title