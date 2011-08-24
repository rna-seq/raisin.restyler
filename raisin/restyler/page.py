"""Page object rendered according to a layout"""

import urlparse
import pickle
from config import JSON
from config import PICKLED
from utils import render_javascript
from utils import render_chartoptions
from utils import render_description
from raisin.box import RESOURCES_REGISTRY
from raisin.page import PAGES
from raisin.restkit import get_resource_by_uri
from raisin.box import RESOURCES
from raisin.box import BOXES

def get_resource(name, content_type, kwargs):
    """Helper method to get a resource by name"""
    try:
        uri = RESOURCES[name]['uri'] % kwargs
    except KeyError:
        print RESOURCES[name]['uri'], kwargs
        raise
    result = get_resource_by_uri(uri, content_type)
    if not result is None:
        if content_type == PICKLED:
            result = pickle.loads(result)
    return result


def get_absolute_url(request):
    """Return an absolute url with a slash at the end"""
    url = request.application_url
    # pylint: disable-msg=E1101
    # no error
    path = urlparse.urlparse(request.url).path
    absolute_url = urlparse.urljoin(url, path)
    if not absolute_url.endswith('/'):
        absolute_url = absolute_url + '/'
    return absolute_url


class Cells(object):
    """Provides information on what cells charts are located in."""

    def __init__(self, view):
        # Remember which columns the cells occupy
        self.columns_for_cells = {}
        # For each cell, remember whether it starts a new row
        self.new_row_for_cells = {}
        # The names in the cells of the layout correspond to the charts
        self.cells = []
        if type(view['rows']) == type(''):
            view['rows'] = [view['rows']]
        for row in view['rows']:
            # Check the number of cells in the row isn't too big
            columns = view[row]
            if type(columns['columns']) == type(''):
                self.cells.append(columns['columns'])
                self.columns_for_cells[columns['columns']] = view['cols'][0]
            else:
                if len(columns['columns']) > len(view['cols']):
                    warning = "Warning: The number of rows is too big: %s %s"
                    raise AttributeError(warning % (columns['columns'],
                                                    view['cols']))
                index = 0
                for column in columns['columns']:
                    # Store whether this column is the start or not of a new row
                    if index == 0:
                        self.new_row_for_cells[column] = True
                    else:
                        self.new_row_for_cells[column] = False
                    self.cells.append(column)
                    if column in self.columns_for_cells:
                        # There is already a column occupied by this item
                        self.columns_for_cells[column] += view['cols'][index]
                    else:
                        self.columns_for_cells[column] = view['cols'][index]
                    index += 1

    def get_cells(self):
        """Get the cells"""
        return self.cells

    def get_column_for_chart(self, chart_id):
        """Returns the column for a chart"""
        return self.columns_for_cells[chart_id]

    def get_new_row_for_chart(self, chart_id):
        """Answers the question whether a new row is needed for this chart"""
        return self.new_row_for_cells[chart_id]


class Layout(object):
    """Provides information on the layout and its cells."""

    def __init__(self, request):
        self.layout_id = request.matched_route.name[len('p1_'):]
        self.layout = PAGES[self.layout_id]
        if self.layout_id in ['homepage', 'experiment_subset']:
            view = self.layout
        elif self.layout_id in ['project', 'experiment', 'run', 'lane']:
            tab_name = request.matchdict.get('tab_name', None)
            if tab_name in self.layout:
                view = self.layout[tab_name]
            else:
                view = self.layout[self.layout['tabbed_views'][0]]
        else:
            raise AttributeError
        self.view = view
        self.cells = Cells(self.view)

    def get_cells(self):
        """Get the cells"""
        return self.cells

    def get_view(self):
        """Get the view"""
        return self.view

    def get_layout(self):
        """Get the layout"""
        return self.layout

    def get_layout_id(self):
        """Get the layout id"""
        return self.layout_id


class Restyler(object):
    """Gets resources and renders them as charts"""

    def __init__(self, request, cells):
        self.cells = cells
        self.resources = self.get_resources()
        self.charts = self.get_charts(request)
        self.packages = self.get_packages()
        self.javascript = render_javascript(self.charts, self.packages)

    def get_charts(self, request):
        """Return the charts needed for rendering"""
        url = get_absolute_url(request)
        charts = []
        for chart in self.get_chart_infos(request):
            chart['chartoptions_rendered'] = ""
            # Render the chart to JSon
            if not JSON in chart or chart[JSON] is None:
                pass
            elif not 'charttype' in chart:
                pass
            else:
                chart['data'] = chart[JSON]
                chart['chartoptions']['is3D'] = False
                rendered = render_chartoptions(chart['chartoptions'])
                chart['chartoptions_rendered'] = rendered
                chart['csv_download_url'] = url + "%s.csv" % chart['id']
                chart['html_download_url'] = url + "%s.html" % chart['id']
            chart['module_id'] = self.cells.get_column_for_chart(chart['id'])
            if self.cells.get_new_row_for_chart(chart['id']):
                chart['module_style'] = "clear: both;"
            else:
                chart['module_style'] = ""
            rendered = render_description(request,
                                          chart.get('description', ''),
                                          chart.get('description_type', ''))
            chart['description_rendered'] = rendered
            # Use an id with the postfox '_div' to make collisions unprobable
            chart['div_id'] = chart['id'] + '_div'
            charts.append(chart)
        return charts

    def get_packages(self):
        """Google Chart tools has a lot of packages covered in the corecharts
        already, and the only chart type that necessitates loading a package
        is the table.
        """
        packages = set(['corechart'])
        for chart in self.charts:
            if chart.get('charttype', None) == 'Table':
                packages.add(chart['charttype'].lower())
        return packages

    def get_resources(self):
        """Get a list of all resources"""
        resources = []
        # And keep track of any that were not found
        unknown = set(self.cells.get_cells())
        # Go through the registry, and take only the resources that are
        # referenced from the cells of the layout
        for resource in RESOURCES_REGISTRY:
            if resource[0] in self.cells.get_cells():
                if resource[0] in unknown:
                    # This is a known resource, so remove it from the unknown
                    unknown.remove(resource[0])
                # Avoid duplicates
                if not resource in resources:
                    resources.append(resource[:])
        if len(unknown) > 0:
            print "Unknown resources: %s" % unknown
            raise AttributeError
        return resources

    def get_chart_infos(self, request):
        """Get all augmented charts from the resources in the context."""
        charts = []
        for chart_name, method, content_types in self.resources:
            # Fill an empty chart with the statistics resources based on the wanted
            # content types
            chart = BOXES[chart_name].copy()
            if not 'id' in chart:
                # At least put in a default id
                chart['id'] = chart_name
            success = True
            for content_type in content_types:
                result = get_resource(chart_name,
                                      content_type,
                                      request.matchdict)
                if result is None:
                    success = False
                else:
                    chart[content_type] = result
            if success:
                # Call the method on the current context
                method(self, chart)
                charts.append(chart)
        return charts

class Page(object):
    """Renders a page with boxes in a layout."""

    def __init__(self, request):
        self.layout = Layout(request)
        cells = self.layout.get_cells()
        self.restyler = Restyler(request, cells)
        self.breadcrumbs = self.get_breadcrumbs(request)
        self.items = self.get_items(request)
        self.tabs = self.get_tabs(request)

    def title(self, request):
        """Returns the title of the page depending on the layout"""
        layout_id = self.layout.get_layout_id()
        title = "Project: %(project_name)s" % request.matchdict
        if layout_id == 'experiment_subset':
            title = "Subset: %(parameter_values)s" % request.matchdict
        elif layout_id in ['homepage',
                           'experiment_subset',
                           'project',
                           'experiment',
                           'run',
                           'lane']:
            if not request.matchdict.get('parameter_values', None) is None:
                title = "Experiment: %(parameter_values)s" % request.matchdict
            if not request.matchdict.get('run_name', None) is None:
                title = "RNASeq Pipeline Run: %(run_name)s" % request.matchdict
        else:
            raise AttributeError
        return title

    def get_breadcrumbs(self, request):
        """Returns a list of dictionaries of breadcrumbs"""
        layout = self.layout.get_layout()
        if not 'breadcrumbs' in layout:
            return

        if type(layout['breadcrumbs']) == type(''):
            layout['breadcrumbs'] = [layout['breadcrumbs']]

        _pro = '/project/%(project_name)s'
        _par = '/%(parameter_list)s/%(parameter_values)s'
        _run = '/run/%(run_name)s'
        _tab = '/tab/%(tab_name)s'

        mapping = {
            'homepage': ('Projects',
                         '/'),
            'project': ('Project: %(project_name)s',
                        _pro + '/tab/experiments/'),
            'parameters': ('Experiment: %(parameter_values)s',
                           _pro + _par + _tab),
            'run': ('Run: %(run_name)s',
                    _pro + _par + _run + _tab)
            }

        breadcrumbs = []
        for item in layout['breadcrumbs']:
            title, url = mapping[item]
            crumb = {'title': title % request.matchdict,
                     'url': request.application_url + url % request.matchdict}
            breadcrumbs.append(crumb)
        return breadcrumbs

    def get_items(self, request):
        """Returns a list of dictionaries of sub items"""
        items = None
        if self.layout.get_layout_id() == 'experiment':
            items = get_run_items(request)
        return items

    def get_tabs(self, request):
        """Returns a list of dictionaries of tabs"""
        layout_id = self.layout.get_layout_id()
        layout = self.layout.get_layout()
        if not 'tabbed_views' in layout:
            return
        tab_name = request.matchdict.get('tab_name', None)
        tabs = []

        _pro = '/project/%(project_name)s'
        _par = '/%(parameter_list)s/%(parameter_values)s'
        _run = '/run/%(run_name)s'
        _lan = '/lane/%(lane_name)s'
        _tab = '/tab/%s/'

        mapping = {
            'project': _pro,
            'experiment': _pro + _par,
            'run': _pro + _par + _run,
            'lane': _pro + _par + _run + _lan,
            }

        for tab in layout['tabbed_views']:
            path = mapping[layout_id] % request.matchdict + _tab % tab
            tabs.append({'id': tab,
                         'title': layout[tab]['title'],
                         'current': tab == tab_name,
                         'url': request.application_url + path})
        return tabs

    def get_charts(self):
        """Get the precalculated charts"""
        return self.restyler.charts

    def get_javascript(self):
        """Get the precalculated javascript"""
        return self.restyler.javascript


def get_run_items(request):
    """Return items for run"""
    items = {}
    items['title'] = 'RNASeq Pipeline Runs'
    items['level'] = 'Experiment'
    items['toggle'] = 'Show %(title)s for this %(level)s' % items
    experiment_runs = get_resource('experiment_runs',
                                   PICKLED,
                                   request.matchdict)
    if experiment_runs is None:
        description = [('Project Id', 'string'),
                       ('Experiment Id', 'string'),
                       ('Run Id', 'string'),
                       ('Run Url', 'string')]
        experiment_runs = {'table_data': [],
                           'table_description': description,
                          }
    tab_name = request.matchdict.get('tab_name', None)
    items['list'] = []
    for item in experiment_runs['table_data']:
        url = request.application_url + item[4]
        if tab_name == 'experiments':
            items['list'].append({'title': item[3],
                                  'url': url})
        else:
            items['list'].append({'title': item[3],
                                  'url': url[:-len('overview')] + tab_name})
    return items
