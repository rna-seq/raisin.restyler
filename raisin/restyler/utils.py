import pickle
from zope.pagetemplate.pagetemplatefile import PageTemplateFile

from raisin.restkit import resource
from raisin.box import RESOURCES
from raisin.box import BOXES

from config import PICKLED


def render_javascript(charts, packages):
    pt = PageTemplateFile('templates/javascript.pt')
    context = {'packages': "'%s'" % ','.join(packages),
               'charts': charts}
    return pt.pt_render(namespace=context)


def render_chartoptions(chartoptions):
    rendered = ""
    for key, value in chartoptions.items():
        if rendered:
            # Add a comma only when there is already an item
            rendered += ", "
        rendered += "%s: " % key
        if key in ['height', 'width', 'max', 'min', 'pointSize', 'lineSize', 'legendFontSize', 'pageSize', 'lineWidth', 'hAxis', 'vAxis']:
            rendered += "%s" % value
        elif key in ['isStacked', 'is3D', 'smoothLine', 'showRowNumber', 'allowHtml', 'chartArea']:
            rendered += "%s" % str(value).lower()
        elif key in ['titleX', 'titleY', 'legend', 'page', 'curveType', 'title']:
            rendered += "'%s'" % value
        elif key in ['colors', ]:
            rendered += str(value)
        else:
            print key, value, type(value)
            raise AttributeError
    return rendered


def render_description(request, description, description_type):
    rendered = []
    if description is None or description == []:
        description = ""
    if description_type == 'infotext':
        # Render body text as infotext
        rendered.append('<br />')
        rendered.append("""<p class="infotext">
        <strong>
%s
</strong>
</p>""" % description)
    elif description_type == 'properties':
        # Render body text as accentheader
        rendered.append('<br />')
        for dictionary in description:
            key, value = dictionary.items()[0]
            rendered.append("""<p class="info">%s: <strong>%s</strong></p>""" % (key, value))
    elif description_type == 'linklist':
        rendered.append('<ul class="linklist">')
        for line in description:
            rendered.append("""<li class="schemagroup sg_announcements" style="float:none;">""")
            link = request.application_url + line['URL']
            rendered.append("""<a href="%s">%s</a>""" % (link, line['Experiment id']))
            rendered.append("""</li>""")
        rendered.append('</ul>')
    elif description_type == 'projectlist':
        rendered.append('<ul class="projectlist">')
        for line in description:
            rendered.append("""<li>""")
            link = request.application_url + line['URL']
            rendered.append("""<a href="%s">%s</a>""" % (link, line['Project Id']))
            rendered.append("""</li>""")
        rendered.append('</ul>')
    else:
        in_list = False
        for line in description.split('\n'):
            line = line.strip()
            if line.startswith("*"):
                line = line[1:]
                if not in_list:
                    rendered.append("<ul>")
                    in_list = True
            else:
                if in_list:
                    rendered.append("</ul>")
                in_list = False
            if in_list:
                rendered.append('<li class="infotext">%s</li>' % line)
            else:
                rendered.append('<p class="infotext">%s</p>' % line)
        if rendered:
            rendered = ['<br />'] + rendered

    rendered = '\n'.join(rendered)
    return rendered


def get_chart_infos(context, request):
    charts = []
    for chart_name, method, predefined_content_types in context.resources:
        # Fill an empty chart with the statistics resources based on the wanted content types
        chart = BOXES[chart_name].copy()
        if not 'id' in chart:
            # At least put in a default id
            chart['id'] = chart_name
        request.matchdict['chart_name'] = chart_name
        successful_content_types = []
        for content_type in predefined_content_types:
            try:
                uri = RESOURCES[chart_name]['uri'] % request.matchdict
            except KeyError:
                print RESOURCES[chart_name]['uri'], request.matchdict
                raise
            if content_type == PICKLED:
                pick = resource.get(uri, content_type)
                if pick is None:
                    pass
                else:
                    chart[content_type] = pickle.loads(pick)
                    successful_content_types.append(content_type)
            else:
                result = resource.get(uri, content_type)
                if not result is None:
                    chart[content_type] = result
                    successful_content_types.append(content_type)

        charts.append({'chart': chart,
                       'method': method,
                       'successful_content_types': successful_content_types,
                       'predefined_content_types': predefined_content_types})

    return charts


def get_resource_directly(name, content_type, kw):
    uri = RESOURCES[name]['uri'] % kw
    return resource.get(uri, content_type)


def get_resource_by_url(url, content_type):
    return resource.get(url, content_type)
