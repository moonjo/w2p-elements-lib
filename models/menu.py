# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## Customize your APP title, subtitle and menus here
#########################################################################

response.logo = DIV(
                    A(
                      B(SPAN('Elements '), SMALL(' Library'), SMALL(' Beta', _style='color:#b20;')),
                      _class="navbar-brand",_href=URL(c='default',f='index')
                      ),
                    _class='navbar-header'
                    )
response.title = ' '.join(word.capitalize() for word in request.application.split('_'))
response.subtitle = T('customize me!')

## read more at http://dev.w3.org/html5/markup/meta.name.html
response.meta.author = 'Sean Kim <moonbal@gmail.com>'
response.meta.description = 'xRecruit'
response.meta.keywords = 'element library'
response.meta.generator = 'Web2py Web Framework'

## your http://google.com/analytics id
response.google_analytics_id = None

#########################################################################
## this is the main application menu add/remove items as required
#########################################################################

response.menu = [
    #('Reload', False, URL('default', 'index')),
    ('', False, SPAN(INPUT(_id='size-toggle', _type='checkbox'), LABEL('', _for='size-toggle'), _id='size-toggle-menu')),
    ('', False, A("Wiki", _href="http://wiki/Xelements", _target="_wiki"), []),
]


DEVELOPMENT_MENU = False

#########################################################################
## provide shortcuts for development. remove in production
#########################################################################

def _():
    # shortcuts
    app = request.application
    ctr = request.controller
    # useful links to internal and external resources
    if auth.has_membership('admin') or auth.has_membership('elementalist'):
        response.menu += [
            ('Admin', False, URL('manage', 'index')),
        ]
   
_()

