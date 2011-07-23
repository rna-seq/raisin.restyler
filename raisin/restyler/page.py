import urlparse

from config import JSON
from config import PICKLED
from utils import render_javascript
from utils import render_chartoptions
from utils import render_description
from utils import get_chart_infos
from utils import get_resource
from raisin.box import RESOURCES_REGISTRY
from raisin.page import PAGES


class Page(object):

    def __init__(self, request):
        self.request = request
        self.matchdict = request.matchdict
        self.layout_id = request.matched_route.name[len('p1_'):]
        self.layout = PAGES[self.layout_id]
        self.project_name = self.matchdict.get('project_name', None)
        self.parameter_list = self.matchdict.get('parameter_list', None)
        self.parameter_values = self.matchdict.get('parameter_values', None)
        self.run_name = self.matchdict.get('run_name', None)
        self.lane_name = self.matchdict.get('lane_name', None)
        self.tab_name = self.matchdict.get("tab_name", None)

        # pylint: disable-msg=E1101
        # no error
        self.absolute_url = urlparse.urljoin(request.application_url,
                                             urlparse.urlparse(request.url).path)
        if not self.absolute_url.endswith('/'):
            self.absolute_url = self.absolute_url + '/'

        self.breadcrumbs = self.get_breadcrumbs()

        if self.layout_id == 'experiment':
            self.items = self.get_items()

        if 'tabbed_views' in self.layout:
            self.tabs = self.get_tabs()

        if self.layout_id in ['homepage', 'experiment_subset']:
            view = self.layout
        elif self.layout_id in ['project', 'experiment', 'run', 'lane']:
            if self.tab_name in self.layout:
                view = self.layout[self.tab_name]
            else:
                view = self.layout[self.layout['tabbed_views'][0]]
        else:
            raise AttributeError

        cells = self.calculate_columns(view)

        # We need to assemble all of the resources needed on the page
        self.resources = []

        # And keep track of any that were not found
        unknown = set(cells)

        # Go through the registry, and take only the resources that are referenced from the cells of the layout
        for resource in RESOURCES_REGISTRY:
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

        self.packages, self.charts = self.get_packages_and_charts()

        if len(self.charts) == 0:
            return None
        javascript = render_javascript([chart for chart in self.charts if ('charttype' in chart and 'data' in chart)], self.packages)
        self.javascript = javascript

    def calculate_columns(self, view):
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
                    raise AttributeError("Warning: The number of rows is too big: %s %s" % (columns['columns'], view['cols']))
                i = 0
                for column in columns['columns']:
                    # Store whether this column is the start or not of a new row
                    if i == 0:
                        self.new_row_for_cells[column] = True
                    cells.append(column)
                    if column in self.columns_for_cells:
                        # There is already a column occupied by this item
                        self.columns_for_cells[column] = self.columns_for_cells[column] + view['cols'][i]
                    else:
                        self.columns_for_cells[column] = view['cols'][i]
                    i = i + 1
        return cells

    def get_packages_and_charts(self):
        packages = set(['corechart'])
        charts = []
        for chart in get_chart_infos(self):
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
                if 'charttype' in chart:
                    # The downloads are always relative to the current url
                    chart['csv_download_url'] = self.absolute_url + "%s.csv" % chart['id']
                    chart['html_download_url'] = self.absolute_url + "%s.html" % chart['id']
            chart['module_id'] = self.columns_for_cells[chart['id']]
            if self.new_row_for_cells.get(chart['id'], False):
                chart['module_style'] = "clear: both;"
            else:
                chart['module_style'] = ""
            chart['description_rendered'] = render_description(self.request, chart.get('description', ''), chart.get('description_type', ''))
            # Use an id with the postfox '_div' to make collisions unprobable
            chart['div_id'] = chart['id'] + '_div'
            charts.append(chart)
        return packages, charts

    def Title(self):
        title = "Project: %s" % self.project_name
        if self.layout_id == 'experiment_subset':
            title = "Subset: %s" % self.parameter_values
        elif self.layout_id in ['homepage', 'experiment_subset', 'project', 'experiment', 'run', 'lane']:
            if not self.parameter_values is None:
                title = "Experiment: %s" % self.parameter_values
            if not self.run_name is None:
                title = "RNASeq Pipeline Run: %s" % self.run_name
        else:
            raise AttributeError
        return title

    def get_breadcrumbs(self):
        breadcrumbs = []
        if 'breadcrumbs' in self.layout:
            if type(self.layout['breadcrumbs']) == type(''):
                self.layout['breadcrumbs'] = [self.layout['breadcrumbs']]
            for item in self.layout['breadcrumbs']:
                if item == 'homepage':
                    url = self.request.application_url + '/'
                    crumb = {'title': 'Projects', 'url': url}
                    breadcrumbs.append(crumb)
                elif item == 'project':
                    url = '/project/%s/tab/experiments/' % self.project_name
                    crumb = {'title': 'Project: %s' % self.project_name,
                             'url': self.request.application_url + url}
                    breadcrumbs.append(crumb)
                elif item == 'parameters':
                    url = '/project/%s/%s/%s/tab/%s' % (self.project_name,
                                                               self.parameter_list,
                                                               self.parameter_values,
                                                               self.tab_name)
                    crumb = {'title': 'Experiment: %s' % self.parameter_values,
                             'url': self.request.application_url + url}
                    breadcrumbs.append(crumb)
                elif item == 'run':
                    url = '/project/%s/%s/%s/run/%s/tab/%s' % (self.project_name,
                                                                      self.parameter_list,
                                                                      self.parameter_values,
                                                                      self.run_name,
                                                                      self.tab_name)
                    crumb = {'title': 'Run: %s' % self.run_name,
                             'url': self.request.application_url + url}
                    breadcrumbs.append(crumb)
        return breadcrumbs

    def get_items(self):
        items = {}
        items['title'] = 'RNASeq Pipeline Runs'
        items['level'] = 'Experiment'
        items['toggle'] = 'Show %(title)s for this %(level)s' % items
        experiment_runs = get_resource('experiment_runs',
                                       PICKLED,
                                       self.matchdict)
        if experiment_runs is None:
            experiment_runs = {'table_data': [],
                               'table_description': [('Project Id', 'string'),
                                                     ('Experiment Id', 'string'),
                                                     ('Run Id', 'string'),
                                                     ('Run Url', 'string')]
                               }
        items['list'] = []
        for item in experiment_runs['table_data']:
            url = self.request.application_url + item[4]
            if self.tab_name == 'experiments':
                items['list'].append({'title': item[3],
                                      'url': url})
            else:
                items['list'].append({'title': item[3],
                                      'url': url[:-len('overview')] + self.tab_name})
        return items

    def get_tabs(self):
        tabs = []
        for tab in self.layout['tabbed_views']:
            if self.layout_id == 'project':
                path = '/project/%s/tab/%s/' % (self.project_name,
                                                       tab)
                url = self.request.application_url + path
            elif self.layout_id == 'experiment':
                path = '/project/%s/%s/%s/tab/%s/' % (self.project_name,
                                                             self.parameter_list,
                                                             self.parameter_values,
                                                             tab)
                url = self.request.application_url + path
            elif self.layout_id == 'run':
                path = '/project/%s/%s/%s/run/%s/tab/%s/' % (self.project_name,
                                                                    self.parameter_list,
                                                                    self.parameter_values,
                                                                    self.run_name,
                                                                    tab)
                url = self.request.application_url + path
            elif self.layout_id == 'lane':
                path = '/project/%s/%s/%s/run/%s/lane/%s/tab/%s/' % (self.project_name,
                                                                            self.parameter_list,
                                                                            self.parameter_values,
                                                                            self.run_name,
                                                                            self.lane_name,
                                                                            tab)
                url = self.request.application_url + path
            else:
                raise AttributeError
            tabs.append({'id': tab,
                         'title': self.layout[tab]['title'],
                         'current': tab == self.tab_name,
                         'url': url})
        return tabs
