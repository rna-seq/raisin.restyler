"""Utility methods for rendering"""

from zope.pagetemplate.pagetemplatefile import PageTemplateFile


def render_javascript(charts, packages):
    """Render the javascript for the charts and packages"""
    render_charts = []
    for chart in charts:
        if 'charttype' in chart and 'data' in chart:
            render_charts.append(chart)
    if len(render_charts) == 0:
        return None
    pagetemplate = PageTemplateFile('templates/javascript.pt')
    context = {'packages': "'%s'" % ','.join(packages),
               'charts': render_charts}
    return pagetemplate.pt_render(namespace=context)


def render_chartoptions(chartoptions):
    """Render the gviz chart options"""
    rendered = ""
    for key, value in chartoptions.items():
        if rendered:
            # Add a comma only when there is already an item
            rendered += ", "
        rendered += "%s: " % key
        if key in ['height', 'width', 'max', 'min', 'pointSize',
                   'lineSize', 'legendFontSize', 'pageSize',
                   'lineWidth', 'hAxis', 'vAxis']:
            rendered += "%s" % value
        elif key in ['isStacked', 'is3D', 'smoothLine',
                     'showRowNumber', 'allowHtml', 'chartArea']:
            rendered += "%s" % str(value).lower()
        elif key in ['titleX', 'titleY', 'legend', 'page',
                     'curveType', 'title']:
            rendered += "'%s'" % value
        elif key in ['colors', ]:
            rendered += str(value)
        else:
            print key, value, type(value)
            raise AttributeError
    return rendered


def render_description(request, description, description_type):
    """Render description according to description type"""
    if description is None or description == []:
        description = ""
    rendered = []
    if description_type == 'infotext':
        rendered = render_infotext(description)
    elif description_type == 'properties':
        rendered = render_properties(description)
    elif description_type == 'linklist':
        rendered = render_linklist(description, request.application_url)
    elif description_type == 'projectlist':
        rendered = render_projectlist(description, request.application_url)
    else:
        rendered = render_list(description)
    rendered = '\n'.join(rendered)
    return rendered


def render_infotext(description):
    """Render description as infotext paragraph"""
    rendered = []
    # Render body text as infotext
    rendered.append('<br />')
    paragraph = """<p class="infotext"><strong>%s</strong></p>"""
    rendered.append(paragraph % description)
    return rendered


def render_properties(description):
    """Render description as properties"""
    rendered = []
    # Render body text as accentheader
    rendered.append('<br />')
    for dictionary in description:
        key, value = dictionary.items()[0]
        rendered.append(("""<p class="info">"""
                         """%s: <strong>%s</strong></p>""" % (key, value)))
    return rendered


def render_linklist(description, application_url):
    """Render description as linklist"""
    rendered = []
    rendered.append('<ul class="linklist">')
    for line in description:
        rendered.append(("""<li class="schemagroup sg_announcements" """
                         """style="float:none;">"""))
        link = application_url + line['URL']
        rendered.append("""<a href="%s">%s</a>""" % (link,
                                                     line['Experiment id']))
        rendered.append("""</li>""")
    rendered.append('</ul>')
    return rendered


def render_projectlist(description, application_url):
    """Render description as projectlist"""
    rendered = []
    rendered.append('<ul class="projectlist">')
    for line in description:
        rendered.append("""<li>""")
        link = application_url + line['URL']
        rendered.append("""<a href="%s">%s</a>""" % (link,
                                                     line['Project Id']))
        rendered.append("""</li>""")
    rendered.append('</ul>')
    return rendered


def render_list(description):
    """Render description as list"""
    rendered = []
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
    return rendered
