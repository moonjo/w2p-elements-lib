# -*- coding: utf-8 -*-
"""
Elements (2D) library

Websocket server
python /opt/web2py/gluon/contrib/websocket_messaging2.py -k web2py4me -p 8080 -l 192.168.1.1

"""
import os
import re
from datetime import datetime
from collections import defaultdict
import gluon.contrib.simplejson
from utils import *

import logging
import logging.config
logging.config.fileConfig('logging.conf')
logger = logging.getLogger("web2py.app.%s" %request.application)
logger.setLevel(logging.DEBUG)

from gluon.contrib.websocket_messaging2 import websocket_send

VERSION = '0.9n'

@auth.requires_login()
def index():
    """Main page
    """
    if request.vars.has_key('playlist'):
        pl_id = request.vars.playlist
    else:
        pl_id = ''
    
    if len(request.args) > 1:
        filter_type = request.args[0] # branch or category
        filter_id = request.args[1]
        elem_grid = getElementsGrid(filter_type, filter_id)
        treenode = '{0}-{1}'.format(filter_type, filter_id)
    else:
        treenode = ''
        elem_grid = SPAN()
    
    search_grid = SPAN('search result')
    
    category_dict = getCategories()
    category_tree, branches, tags = categoryTree(category_dict)
    
    source_dict = getSourceCategories()
    proj_tree = projectTree(source_dict)
    
    filterpanel = filterPanel()
    
    # news ticker
    ticker = getXelementsUpdate()
    
    filter_vals = ''
    if request.cookies.has_key(request.application):
        filter_vals = request.cookies[request.application].value
    
    # user panel
    nav_panel = buildNavPanel()
    
    ptemp = previewTemplate()
    
    return dict(ticker=ticker,
                cat_tree=category_tree,
                proj_tree=proj_tree,
                filterpanel=filterpanel,
                grid=elem_grid,
                searched=search_grid,
                filter_vals=filter_vals,
                treenode=treenode,
                navpanel=nav_panel,
                previewtemplate=ptemp,
                playlistval=pl_id,
                websocket_ip=WEBSOCKET_IP,
                websocket_key=WEBSOCKET_KEY,
                websocket_group=WEBSOCKET_GROUP
                )

@auth.requires_login()
def getElementsGrid(filter_type, filter_id, source=None):
    """Return elements
    @param filter_type: filtering type - branch or category
    @param filter_id: filtering id
    @return: elements grid
    """
    if source == 'unknown':
        source = ''
    
    if filter_type == 'project':
        q = (db.xelements_element.source==source) & \
            (db.xelements_element.category_id==db.xelements_category.id) & \
            (db.xelements_category.branch_id==db.xelements_branch.id) & \
            (db.xelements_element.retired==0)
    else:
        if filter_type == 'category':
            q = (db.xelements_element.category_id==filter_id) & \
                (db.xelements_element.category_id==db.xelements_category.id) & \
                (db.xelements_category.branch_id==db.xelements_branch.id) & \
                (db.xelements_element.retired==0)
        elif filter_type == 'branch':
            q = (db.xelements_category.branch_id==filter_id) & \
                (db.xelements_category.branch_id==db.xelements_branch.id) & \
                (db.xelements_element.category_id==db.xelements_category.id) & \
                (db.xelements_element.retired==0)
        if source:
            q &= (db.xelements_element.source==source)
            
    rows = db(q).select(orderby=db.xelements_element.name|db.xelements_element.element_code)
    
    fav_count = countFavourites()
    data = prepElements(rows, request.folder, fav_count)
    result = griddle(data)
    
    return result

def getElementsGridHTML():
    """AJAX wrapper for getElementsGrid()
    """
    #print 'GRIDFILTER', request.vars
    project_code = request.vars.project.replace('%20', ' ')
    filter_type = request.vars.type
    try:
        filter_id = int(request.vars.filterid)
    except Exception, e:
        logger.error(e)
        return ''
    
    result = getElementsGrid(filter_type, filter_id, project_code)
    return result.xml()

@auth.requires_login()
def getCategories():
    """Return element categories for Filter Tree
    """
    data = defaultdict(list)
    for row in db(db.xelements_category.branch_id==db.xelements_branch.id).select(db.xelements_category.ALL,
                           db.xelements_branch.ALL,
                           orderby=db.xelements_category.ordering):
        
        category = {'id': row.xelements_category.id,
                    'name': row.xelements_category.name,
                    'colour': row.xelements_category.colour,
                    'order': row.xelements_category.ordering,
                    'branch': row.xelements_branch.name,
                    'project': '',
                    'sg_status_list': '',
                    'tag_list': '',
                    }
        data[row.xelements_branch.id].append(category)
        
    return data

@auth.requires_login()
def getSourceCategories():
    """Return element categories for Filter Tree
    """#(db.xelements_element.source!='' and db.xelements_element.source!=None) &\
    data = defaultdict(dict)
    for row in db((db.xelements_element.source!=None) &\
                  (db.xelements_element.category_id==db.xelements_category.id) &\
                  (db.xelements_category.branch_id==db.xelements_branch.id) &\
                  (db.xelements_element.retired==0)
                  ).select(db.xelements_element.source,
                           db.xelements_category.id,
                           db.xelements_category.name,
                           db.xelements_category.colour,
                           db.xelements_category.ordering,
                           db.xelements_branch.id,
                           db.xelements_branch.name,
                           orderby=db.xelements_category.ordering,
                           distinct=True,
                           ):
        
        if row.xelements_element.source:
            project_code = row.xelements_element.source.replace(' ', '%20')
        else:
            project_code = 'unknown'
            
        category = {'id': row.xelements_category.id,
                    'name': row.xelements_category.name,
                    'colour': row.xelements_category.colour,
                    'order': row.xelements_category.ordering,
                    'branch': row.xelements_branch.name,
                    'project': project_code,
                    'sg_status_list': '',
                    'tag_list': '',
                    }
        branch_label = '{0}|{1}'.format(row.xelements_branch.name, row.xelements_branch.id)
        cats = data[project_code].setdefault(branch_label, [])
        cats.append(category)
    return data


def projectTree(pdict, eorder=None):
    """Build grid for (Asset) Lib
    @return: UL object, list of element types, list of element tags
    """
    nothumb = '/%s/static/images/nothumb.jpg' %(request.application)
    #print pdict
    # loop thru entities
    def litemize(entity, project_code):
        """Return LI() of given entity
        """
        img_url = None
        if entity.has_key('image'):
            img_url = entity.get('image')
        if not img_url:
            img_url = nothumb
        
        entity_name = entity['name']
        branch = entity['branch']
        branch_code = codeformat(branch)
        
        desc = entity.get('description')
        
        all_tags.extend(entity['tag_list'])
        entity_tag_list = [t.replace(' ','') for t in entity['tag_list']]
        
        tags_str = ','.join(entity['tag_list'])
        
        thumb_class = 'tree-thumb'
        li_class = 'category-li'
        
        name = entity_name
        if len(name) > ENTITY_NAME:
            name = '%s..' %name[:ENTITY_NAME-2]
        
        fullname = entity_name
        if len(fullname) > ENTITY_FULLNAME:
            fullname = '%s..' %fullname[:ENTITY_FULLNAME-2]
        
        fullname = SPAN(
                        SPAN(fullname, _class='entity-code treenode-info'),
                        #IMG(_src=img_url, _class=thumb_class),
                        )
        
        litem = LI(fullname,
                   **{'_id': 'category-{0}-{1}'.format(project_code, entity['id']),
                      '_class': li_class,
                      '_data-iconclass': 'tree-category',
                      '_data-branch': branch,
                      '_data-type': 'category',
                      '_data-filterid': entity['id'],
                      '_data-project': entity['project'],
                      '_data-desc': desc,
                      '_data-tags': tags_str,
                      '_data-jstree': response.json({"type":branch}),
                      }
                   )
        return litem
    # end litemize()
    
    p = re.compile('\s+')
    
    json_data = []
    all_tags = []
    asset_types = {}
    parent_shots = []
    sub_shots = []
    parent_assets = []
    sub_assets = []
    plis = []
    container = 'shot-container'
    
    categories = defaultdict(list)
    
    project_codes = sorted(pdict.keys(), key=lambda x:x.lower())
    
    for z in ['elements', 'unknown']:
        try:
            project_codes.remove(z)
            project_codes.append(z)
        except ValueError:
            pass
    
    for project_code in project_codes:
        lis = []
        branch_dict = pdict[project_code]
        for b, categories in branch_dict.iteritems():
            branch_name, branch_id = b.split('|')
            
            cat_lis = []
            for category in categories:
                # build parent li and add sub lisfor element in categories[category]:
                cat_lis.append(litemize(category, project_code))
                
            lis.append(LI(branch_name.upper(),
                          UL(cat_lis),
                          **{'_id': 'branch-{0}-{1}'.format(branch_id, project_code),
                             '_class': 'branch-li folder expanded',
                             '_data-type': 'branch',
                             '_data-filterid': branch_id,
                             '_data-project': project_code,
                             '_data-iconclass': 'tree-branch',
                             }
                          )
                       )
        plis.append(LI(project_code.upper().replace('%20', ' '),
                       UL(lis),
                       **{'_id': 'source-{0}'.format(project_code),
                          '_class': 'project-li folder expanded',
                          '_data-type': 'project',
                          '_data-filterid': 0,
                          '_data-project': project_code,
                          '_data-iconclass': 'tree-project',
                          }
                       )
                    )
    return UL(plis, _id='ptree-ul', _class='grid-bootstrap')

def categoryTree(category_dict, eorder=None):
    """Build grid for (Asset) Lib
    @return: UL object, list of element types, list of element tags
    """
    nothumb = '/%s/static/images/nothumb.jpg' %(request.application)
    
    # loop thru entities
    def litemize(entity):
        """Return LI() of given entity
        """
        img_url = None
        if entity.has_key('image'):
            img_url = entity.get('image')
        if not img_url:
            img_url = nothumb
        
        entity_name = entity['name']
        branch = entity['branch']
        branch_code = codeformat(branch)
        
        desc = entity.get('description')
        
        all_tags.extend(entity['tag_list'])
        entity_tag_list = [t.replace(' ','') for t in entity['tag_list']]
        
        tags_str = ','.join(entity['tag_list'])
        
        thumb_class = 'tree-thumb'
        li_class = 'category-li'
        
        name = entity_name
        if len(name) > ENTITY_NAME:
            name = '%s..' %name[:ENTITY_NAME-2]
        
        fullname = entity_name
        if len(fullname) > ENTITY_FULLNAME:
            fullname = '%s..' %fullname[:ENTITY_FULLNAME-2]
        
        fullname = SPAN(
                        SPAN(fullname, _class='entity-code treenode-info'),
                        #IMG(_src=img_url, _class=thumb_class),
                        )
        
        litem = LI(fullname,
                   **{'_id': 'category-{0}'.format(entity['id']),
                      '_class': li_class,
                      '_data-iconclass': 'tree-category',
                      '_data-branch': branch,
                      '_data-type': 'category',
                      '_data-filterid': entity['id'],
                      '_data-desc': desc,
                      '_data-tags': tags_str,
                      '_data-jstree': response.json({"type":branch}),
                      '_data-project': '',
                      }
                   )
        return litem
    # end litemize()
    
    p = re.compile('\s+')
    
    json_data = []
    all_tags = []
    asset_types = {}
    lis = []
    parent_shots = []
    sub_shots = []
    parent_assets = []
    sub_assets = []
    container = 'shot-container'
    
    categories = defaultdict(list)
    #subcategories = {}
    # group by categories
    branches = []
    for row in db().select(db.xelements_branch.ALL, orderby=db.xelements_branch.ordering):
        branches.append((row.name, row.id))
    
    for branch in branches:
        branch_name, branch_id = branch
        categories = category_dict.get(branch_id, [])
        cat_lis = []
        for category in categories:
            # build parent li and add sub lisfor element in categories[category]:
            cat_lis.append(litemize(category))
        lis.append(LI(branch_name.upper(),
                      UL(cat_lis),
                      **{'_id': 'branch-{0}'.format(branch_id),
                         '_class': 'branch-li folder expanded',
                         '_data-type': 'branch',
                         '_data-filterid': branch_id,
                         '_data-iconclass': 'tree-branch',
                         '_data-project': '',
                         }
                      
                      )
                   )
    
    ul_list = UL(lis, _id="tree-ul", _class="grid-bootstrap")
    return ul_list, branches, sorted(set(all_tags))

def filterPanel():
    """Return filter panel
    """
    name_filter = filterOptions('name')
    tags_filter = filterOptions('tag')
    source_filter = filterOptions('source')
    alpha_filter = filterOptions('alpha')
    resolution_filter = filterOptions('resolution')
    colourspace_filter = filterOptions('colourspace')
    favourite_aggregate = filterOptions('favourite')
    
    num_result = 0
    """
    # example
    filters_used = [{'name':'blah', 'type':'tag', 'value':12},
                    {'name':'fubar', 'type':'tag', 'value':35},
                    {'name':'2500x1125', 'type':'resolution', 'value':'2500x1125'},
                    {'name':'Glut', 'type':'colourspace', 'value':'glut'},
                    {'name':'Lum. Key', 'type':'alpha', 'value':'luminencekey'},
                    ]
    """
    filters_used = []
    
    cur_filters = []
    for fv in filters_used:
        cls = ''
        if fv['type'] == 'tag':
            cls = 'label-primary'
        elif fv['type'] == 'alpha':
            cls = 'label-default'
        elif fv['type'] == 'resolution':
            cls = 'label-info'
        elif fv['type'] == 'colourspace':
            cls = 'label-success'
        elif fv['type'] == 'favourite':
            cls = 'label-danger'
        
        cur_filters.append(
                           SPAN(
                                '{0} '.format(fv['name']),
                                A(
                                  I(_class='fa fa-times fa-lg'),
                                  **{'_href':'#{0}'.format(fv['value']),
                                     '_class':'tag-remove',
                                     '_data-value': fv['value']
                                     }
                                  ),
                                _class='tag label {0}'.format(cls)
                                )
                           )
    
    # current filtering options used
    filter_status = DIV(
                        H5('Current Filters', _class='filter-row-header'),
                        DIV(
                            DIV(
                                SPAN('Found {0} elements'.format(num_result),
                                     _id='filter-result-num',
                                     _class='text-primary'
                                    ),
                                DIV(
                                    LABEL(
                                          INPUT(_id='filter-method-tree',
                                                _name='filter-method',
                                                _value='tree',
                                                _type='radio',
                                                _checked=True
                                                ),
                                          'Tree',
                                          _id='filter-method-tree',
                                          _class='btn btn-default btn-xs active',
                                          _title='Filter Tree Grid',
                                          ),
                                    LABEL(
                                          INPUT(_id='filter-method-current',
                                                _name='filter-method',
                                                _value='current',
                                                _type='radio'
                                                ),
                                          'Result',
                                          _id='filter-method-current',
                                          _class='btn btn-default btn-xs',
                                          _title='Filter current result',
                                          _disabled=True,
                                          ),
                                    LABEL(
                                          INPUT(_id='filter-method-new',
                                                _name='filter-method',
                                                _value='new',
                                                _type='radio'
                                                ),
                                          'New',
                                          _class='btn btn-default btn-xs',
                                          _title='Start new search',
                                          ),
                                    **{'_class':'btn-group pull-right filter-method-btns',
                                       '_data-toggle': 'buttons',
                                       }
                                    ),
                                _class='filter-method-div',
                            ),
                            DIV('Filtered By:'),
                            _class='filter-result-div'
                            ),
                        DIV(
                            *cur_filters,
                            _id='current-filters'
                            ),
                        DIV(
                        BUTTON('Search',
                               _id='new-search',
                               _class='btn btn-primary',
                               _style='display:none;'
                               ),
                        BUTTON('Reset',
                               _id='reset-filter',
                               _class='btn btn-none text-danger',
                               ),
                            _class='btn-group-vertical btn-group-justified'
                            ),
                        _class='filter-table'
                        )
    
    filterpanel = DIV(
                      filter_status,
                      name_filter,
                      source_filter,
                      tags_filter,
                      alpha_filter,
                      resolution_filter,
                      colourspace_filter,
                      favourite_aggregate,
                      _class=''
                      )
    
    return filterpanel

def resolutionClass(res):
    w,_ = map(int, res.lower().split('x'))
    resx = [1,320,480,640,800,1024,1280,1600,1920,2048,9999]
    #resx = RESOLUTION_X
    a = resx[0]
    for x in resx[1:]:
        if w >= a and w < x:
            return a
    return resx[-1]
    
def filterOptions(attr):
    """
    """
    max_show = 9
    title = attr
    boundary_cls = ''
    style = ''
    num = 0
    options = []
    
    if attr == 'tag':
        title = 'Tags'
        
        count = db.xelements_tag.id.count()
        query = (db.xelements_tag.id==db.xelements_tagmap.tag_id) & \
                (db.xelements_tagmap.element_id==db.xelements_element.id)
        for row in db(query).select(db.xelements_tag.ALL, count, groupby=db.xelements_tag.id, orderby=~count|db.xelements_tag.name):
            if num == max_show:
                boundary_cls = ' boundary'
                style = 'border-bottom: none;'
            elif num > max_show:
                boundary_cls = ' excess'
                style = ''
            
            name = '{0} ({1})'.format(row.xelements_tag['name'], row[count])
            t = DIV(
                    LABEL(
                          INPUT(_class='tag-checkbox filter-option',
                                _value='tag-{0}'.format(row.xelements_tag['id']),
                                _type='checkbox'
                                ),
                          name,
                          ),
                    _class='filter-row-tag{0}'.format(boundary_cls),
                    _style=style
                    )
            options.append(t)
            num += 1
        # add show more button
        if num > max_show:
            options.append(BUTTON('Show More', _class='btn filter-more-btn'))
        
    elif attr == 'alpha':
        title = 'Alpha Channel'
        options = [DIV(
                    LABEL(
                          INPUT(_id='filter-alpha-val',
                                _class='tag-checkbox filter-option',
                                _value='alpha',
                                _type='checkbox'
                                ),
                          'exists',
                          ),
                    _class='filter-row-tag'
                    )]
        
    elif attr == 'colourspace':
        title = 'Colourspace'
        
    elif attr == 'resolution':
        title = 'Resolution'
        
        resx = [1,480,800,1024,1280,1600,1920,2048,4096,9999]
        #resx = RESOLUTION_X
        xdict = defaultdict(int)
        
        count = db.xelements_element.resolution.count()
        rows = db().select(db.xelements_element.resolution, count, groupby=db.xelements_element.resolution, orderby=~count|db.xelements_element.resolution).as_list()
        
        for row in db().select(db.xelements_element.resolution, count, groupby=db.xelements_element.resolution, orderby=~count|db.xelements_element.resolution):
            element_res = row.xelements_element.resolution
            ecount = row[count]
            if not element_res:
                xdict[1] += ecount
            else:
                a = resx[0]
                for x in resx[1:]:
                    w, _ = map(int, element_res.lower().split('x'))
                    if w < x and w >= a:
                        xdict[a] += ecount
                        break
                    a = x
                    
        for xkey in sorted(xdict.keys(), reverse=True):
            if num == max_show:
                boundary_cls = ' boundary'
                style = 'border-bottom: none;'
            elif num > max_show:
                boundary_cls = ' excess'
                style = ''
            
            if xkey > 1:
                #resclass = resolutionClass(row.xelements_element.resolution)
                xres = '{0}x'.format(xkey)
                val = 'resolution-{0}'.format(xkey)
            else:
                xres = 'Unknown'
                val = 'resolution-unknown'
            name = '{0} ({1})'.format(xres, xdict[xkey])
            
            r = DIV(
                    LABEL(
                          INPUT(_class='tag-checkbox filter-option',
                                _value=val,
                                _type='checkbox'
                                ),
                          name,
                          ),
                    _class='filter-row-tag{0}'.format(boundary_cls),
                    _style=style
                    )
            options.append(r)
            num += 1
        
        # add show more button
        if num > max_show:
            options.append(BUTTON('Show More', _class='btn btn-none filter-more-btn'))
        
    elif attr == 'favourite':
        title = 'Favourite'
        options = [DIV(
                    LABEL(
                          INPUT(_id='allfaves',
                                _class='tag-checkbox filter-option',
                                _value='favourite',
                                _type='checkbox'
                                ),
                          'All Favourites',
                          ),
                    _class='filter-row-tag'
                    )]
    elif attr == 'name':
        title = 'Name'
        options = [DIV(
                       INPUT(_id='filter-name-val',
                             _class='form-control input-sm',
                             _placeholder='filter by name',
                             _type='text'
                             ),
                       _class='filter-row-tag'
                       )]
    elif attr == 'source':
        title = 'Source'
        options = [DIV(
                       INPUT(_id='filter-source-val',
                             _class='form-control input-sm',
                             _placeholder='filter by source show',
                             _type='text'
                             ),
                       _class='filter-row-tag'
                       )]
    
    return DIV(
               H5(title, _class='filter-row-header'),
               *options,
               _id='filter-{0}'.format(attr),
               _class='filter-table'
               )

def savePreference():
    """Save user preference in cookie
    """
    val = request.vars.filterval
    response.cookies[request.application] = val
    response.cookies[request.application]['expires'] =  30 * 24 * 3600
    response.cookies[request.application]['path'] = '/'

@auth.requires_login()
def updateWatchlist():
    """Update user's watchlist (ignore, subscribe) - need page reload
    
    only checked values will pass (value == 'on')
    """
    return ''

def sharePlaylist():
    """Share playlist to target users
    """
    playlist_id = request.vars.playlistid
    recipients = request.vars.recipients

@auth.requires_login()
def importPlaylist():
    """Import playlist from playlist data in url
    """
    if request.vars.has_key('playlist'):
        try:
            playlist_id = int(request.vars.playlist)
        except ValueError, e:
            session.flash = 'Failed to import playlist - invalid id: {0}'.format(request.vars.playlist)
            redirect(URL('index'))
            #return dict()
            
        prow = db(db.xelements_playlist.id==playlist_id).select().first()
        if prow:
            elementids = prow.element_ids
            name = prow.name
            if not name:
                auser = db(db.auth_user.id==prow.user_id).select().first()
                name = "{0}'s Faves".format(auser.username)
        else:
            session.flash = 'Failed to import playlist - invalid id: {0}'.format(request.vars.playlist)
            redirect(URL('index'))
            #return dict()
            
    elif request.vars.has_key('elements'):
        elementids = request.vars.elements
        name = 'name'
    else:
        session.flash = 'Failed to import playlist - no valid playlist id or element ids given.'
        redirect(URL('index'))
        #return dict()
        
    # check name
    numbering = 1
    q = """SELECT MAX(name) FROM xelements_playlist WHERE user_id="{0}" AND name LIKE "{1}%";""".format(auth.user.id, name)
    row = db.executesql(q)
    tmp = row[0][0]
    if tmp:
        basename = name
        m = re.match('(.+)(\d+)', tmp)
        if m:
            basename = m.group(1)
            numbering += int(m.group(2))
        name = '{0}{1}'.format(basename, numbering)
        
    if elementids and name:
        ret = db.xelements_playlist.insert(user_id=auth.user.id,
                                           element_ids=elementids,
                                           name=name,
                                           date_modified=datetime.today()
                                           )
    else:
        ret = ''
    redirect(URL('index', vars={'playlist':ret}))
    #return dict()

#@auth.requires_login()
def currentUser():
    """Return currently logged in username + email
    """
    #return '%s %s (%s)' %(auth.user.first_name, auth.user.last_name, auth.user.email)
    return '{0} {1}'.format(auth.user.first_name, auth.user.last_name)

def websocket_test():
    updaterid = request.vars.updater
    data = response.json({'type':'update', 'value':updaterid})
    websocket_send('http://%s' %WEBSOCKET_IP, data, WEBSOCKET_KEY, WEBSOCKET_GROUP)

def getXelementsUpdate():
    """Return list of LI objects
    """
    now = datetime.now()
    result = []
    rows = db(db.xelements_news.id>0).select()
    for row in rows:
        if row.content:
            tstamp = pretty_date(row.date_created)
            body = '{0} ~ {1}'.format(row.content, tstamp)
            result.append(LI(XML(body), _class='ticker-message'))
    if not result:
        result = [LI('Nothing to report', _class='ticker-message')]
    
    return result[::-1]

def error():
    
    return {}

"""
 default methods
"""

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())

