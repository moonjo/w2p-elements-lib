"""

Elements Database admin page

"""
from datatablesserver import DataTablesServer
from utils import *
from gluon.contrib import simplejson
import logging
import logging.config
from _collections import defaultdict

logging.config.fileConfig('logging.conf')
logger = logging.getLogger("web2py.app.%s" %request.application)
logger.setLevel(logging.DEBUG)

DEFAULT_BRANCH = 14
DEFAULT_CATEGORY = 52

@auth.requires_login()
def addXelementsUpdate(target_id, type, msg):
    """Insert new update message and delete old one
    mrxcms u.submitApplication.php does this in raw SQL
    
    @param target_id: target item id
    @param msg: message text with format strings
    @return: dictionary
    """
    UNKNOWN = 5
    MSGLIMIT = 10
    
    rows = db().select(db.xelements_news.ALL, orderby=db.xelements_news.id)
    # delete excess old messages
    old = [rows[i].id for i in range(len(rows)-MSGLIMIT)]
    db(db.xelements_news.id.belongs(old)).delete()
    
    typerow = db(db.xelements_type.name==type).select(db.xelements_type.id).first()
    if typerow:
        type_id = typerow.id
    else:
        type_id = UNKNOWN
    
    # now insert latest message
    ret = db.xelements_news.insert(target_id=target_id,
                                   type_id=type_id,
                                   content=msg,
                                   user_id=auth.user.id,
                                   date_created=datetime.now()
                                   )
    logger.debug('Added XelementsMessage %d' %ret)
    # broadcast via websocket
    #data = response.json({'type':'update', 'value':updaterid})
    #websocket_send('http://%s' %WEBSOCKET_IP, data, WEBSOCKET_KEY, WEBSOCKET_GROUP)

@auth.requires_login()
def index():
    """
    """
    if len(request.args) > 0:
        page = 'dashboard-{0}'.format(request.args[0])
    else:
        page = 'dashboard-home'
    menu = buildMenu()
    
    # stat - 5 most bookmarked elements
    bookmark_data = simplejson.dumps(bookmarkStat()[:5])
    
    # stat - category usage distribution
    category_data = simplejson.dumps(categoryStat())
    
    # stat - branches and categories
    branch_cat_data = simplejson.dumps(branchCategoryStat())
    
    # stat - tags
    tag_data = simplejson.dumps(tagStat())
    
    return dict(menu=menu,
                page=page,
                bookmark_data=bookmark_data,
                category_data=category_data,
                branch_cat_data=branch_cat_data,
                tag_data=tag_data,
                )

def buildMenu(selected='dashboard'):
    """Manage page menu
    """
    if selected == 'dashboard':
        dashboard_cls = 'menu-header current'
        home_link = '#home'
        stat_link = '#stat'
    else:
        dashboard_cls = 'menu-header has-submenu notcurrent'
        home_link = URL('index')
        stat_link = URL('index', args=['stat'])
        
    '''
    menu_dashboard = LI(
                        A(
                          SPAN(_class='menu-icon fa fa-lg fa-windows'),
                          SPAN('Overview', _class='menu-name'),
                          _href=URL('index'),
                          _class='submenu-header'
                          ),
                        UL(
                           LI(A('Home', _id='dashboard-home', _class='submenu-item', _href=home_link)),
                           LI(A('Stat', _id='dashboard-stat', _class='submenu-item', _href=stat_link)),
                           _class='admin-submenu'
                           ),
                        _class=dashboard_cls
                        )
    '''
    menu_dashboard = LI(
                        A(
                          SPAN(_class='menu-icon fa fa-lg fa-dashboard'),
                          SPAN('Overview', _class='menu-name'),
                          _href=URL('index'),
                          _class='submenu-header'
                          ),
                        _class=dashboard_cls
                        )
    
    menu_items = [menu_dashboard]
    
    if selected == 'elements':
        elements_cls = 'menu-header has-submenu current'
        home_link = '#home'
        new_link = '#new'
    else:
        elements_cls = 'menu-header has-submenu notcurrent'
        home_link = URL('elements')
        new_link = URL('elements') + '#new'
        
    menu_elements = LI(
                       A(
                         SPAN(_class='menu-icon fa fa-lg fa-bolt'),
                         SPAN('Elements', _class='menu-name'),
                         _href=URL('elements'),
                         _class='submenu-header'
                         ),
                       UL(
                          LI(A('All Elements', _id='elements-home', _class='submenu-item', _href=home_link)),
                          LI(A('Add New', _id='elements-new', _class='submenu-item', _href=new_link)),
                          _class='admin-submenu'
                          ),
                       _class=elements_cls
                       )
    menu_items.append(menu_elements)
    
    if selected == 'group':
        categories_cls = 'menu-header has-submenu current'
        home_link = '#home'
        #new_link = '#branches'
        new_link = URL('branches')
    elif selected == 'branches':
        categories_cls = 'menu-header has-submenu current'
        home_link = URL('group')
        new_link = '#home'
    else:
        categories_cls = 'menu-header has-submenu notcurrent'
        home_link = URL('group')
        new_link = URL('branches')
        
    menu_categories = LI(
                         A(
                           SPAN(_class='menu-icon fa fa-lg fa-sitemap'),
                           SPAN('Group', _class='menu-name'),
                           _href=URL('group'),
                           _class='submenu-header'
                           ),
                         UL(
                            LI(A('Categories', _id='group-home', _class='submenu-item', _href=home_link)),
                            LI(A('Branches', _id='group-branches', _class='submenu-item', _href=new_link)),
                            _class='admin-submenu'
                            ),
                         _class=categories_cls
                         )
    menu_items.append(menu_categories)
    
    if selected == 'tags':
        tags_cls = 'menu-header current'
        home_link = '#home'
        new_link = '#new'
    else:
        tags_cls = 'menu-header notcurrent'
        home_link = URL('tags')
        new_link = URL('tags', args=['new'])
        
    menu_tags = LI(
                   A(
                     SPAN(_class='menu-icon fa fa-lg fa-tags'),
                     SPAN('Tags', _class='menu-name'),
                     _href=URL('tags'),
                     _class='submenu-header'
                     ),
                   _class=tags_cls
                   )
    menu_items.append(menu_tags)
    
    return UL(menu_items, _id='admin-menu')

def branchCategoryStat():
    count = db.xelements_element.id.count()
    rows = db((db.xelements_branch.id==db.xelements_category.branch_id)).select(
                                                        db.xelements_branch.name,
                                                        db.xelements_category.name,
                                                        db.xelements_category.colour,
                                                        count,
                                                        left=db.xelements_element.on(db.xelements_element.category_id==db.xelements_category.id),
                                                        groupby=db.xelements_category.name,
                                                        orderby=[db.xelements_branch.name,db.xelements_category.name]
                                                        )
    
    data = []
    for row in rows:
        data.append([row.xelements_category.colour, '{0}-{1}'.format(row.xelements_branch.name, row.xelements_category.name), row[count]])
    return data

def bookmarkStat():
    """Return element bookmark stat
    """
    # get element ids from bookmarks
    user_bookmarks = defaultdict(set)
    for row in db(db.xelements_playlist.element_ids!='').select():
        user_bookmarks[row.user_id].update(set(map(int, row.element_ids.strip(',').split(','))))
        
    counter = defaultdict(int)
    for element_ids in user_bookmarks.values():
        for element_id in element_ids:
            counter[element_id] += 1
            
    # get elements from the bookmark
    data = []
    for row in db((db.xelements_element.id.belongs(counter.keys())) & \
                   (db.xelements_category.id==db.xelements_element.category_id)).select():
        count = counter.get(row.xelements_element.id, 0)
        if count > 0:
            name = '{0}X{1}'.format(row.xelements_element.name,row.xelements_element.element_code)
            data.append({'name': name,
                         'count': count,
                         'colour': '#'+row.xelements_category.colour,
                         'url': URL('detail', 'index', args=[row.xelements_element.id]),
                         })
    return sorted(data, key=lambda x: x['count'], reverse=True)

def categoryStat():
    """
    """
    # get element ids from bookmarks
    user_bookmarks = defaultdict(set)
    for row in db(db.xelements_playlist.element_ids!='').select():
        user_bookmarks[row.user_id].update(set(map(int, row.element_ids.strip(',').split(','))))
        
    counter = defaultdict(int)
    for element_ids in user_bookmarks.values():
        for element_id in element_ids:
            counter[element_id] += 1
            
    # get elements from the bookmark
    result = []
    count = db.xelements_category.id.count()
    rows = db((db.xelements_element.id.belongs(counter.keys())) & (db.xelements_category.id==db.xelements_element.category_id)).select(
                   db.xelements_category.ALL,
                   count,
                   groupby=db.xelements_category.id,
                   orderby=~count
                   )
    for row in rows:
        if row[count] > 0:
            result.append({'name':row.xelements_category.name, 'count':row[count], 'colour':'#'+row.xelements_category.colour})
            
    # group categories below the top 5, into Others
    top_cats = 4
    data = result[:top_cats]
    data.append({'name':'Others', 'count':sum([x['count'] for x in result[top_cats:]]), 'colour':'#751975'})
    return data

def tagStat():
    """
    """
    count = db.xelements_tag.id.count()
    tags = []
    rows = db(db.xelements_tag.id==db.xelements_tagmap.tag_id).select(
                db.xelements_tag.name,
                count,
                groupby=db.xelements_tag.id,
                orderby=count
                )
    for row in rows:
        tags.append({'tag':row.xelements_tag.name, 'count':row[count]})
    return tags

def getBranches():
    rows = db(db.xelements_branch.id>0).select(orderby=db.xelements_branch.name)
    return rows

def getBranchesAJAX():
    options = []
    branches = getBranches()
    for branch in branches:
        options.append(OPTION(branch.name, _value=branch.id).xml())
    return simplejson.dumps(''.join(options))

def getCategories(branchid=None):
    if branchid:
        rows = db(db.xelements_category.branch_id==int(branchid)).select(orderby=db.xelements_category.name)
    else:
        rows = db(db.xelements_category.id>0).select(orderby=db.xelements_category.name)
    return rows

def getCategoriesAJAX():
    options = []
    if request.vars.branch:
        branchid = int(request.vars.branch)
    else:
        branchid = None
    categories = getCategories(branchid)
    for category in categories:
        options.append(OPTION(category.name, _value=category.id).xml().replace('\"',''))
    return simplejson.dumps(''.join(options))

def getElementTags(eid):
    rows = db((db.xelements_tagmap.element_id==eid) & \
              (db.xelements_tagmap.tag_id==db.xelements_tag.id)
              ).select(db.xelements_tag.ALL).as_list()
    return rows

def getElementTagsAJAX():
    element_id = int(request.vars.element)
    rows = db((db.xelements_tagmap.element_id==element_id) & \
              (db.xelements_tagmap.tag_id==db.xelements_tag.id)
              ).select(db.xelements_tag.name, orderby=db.xelements_tag.name)#.as_list()
    
    tags = []
    for row in rows:
        tags.append(row.name)
    
    return simplejson.dumps(tags)

def getPopularTags(num=5):
    """Return #number of  most used Tags
    """
    count = db.xelements_tagmap.tag_id.count()
    rows = db(db.xelements_tag.id>0).select(db.xelements_tag.ALL,
                                            count,
                                            left=db.xelements_tagmap.on(db.xelements_tagmap.tag_id==db.xelements_tag.id),
                                            groupby=db.xelements_tag.id,
                                            orderby=db.xelements_tag.name,
                                            limitby=(0,num)).as_list()
    return rows

def getPopularTagsAJAX():
    return simplejson.dumps(getPopularTags())

def elementForm(mode='new'):
    """
    """
    if mode == 'new':
        tag_loading = SPAN()
        elementid_input = ''
        submitbtn = BUTTON('Create',
                           _id='element-create',
                           _class='btn btn-primary element-form-submit bold',
                           _style='width:100%;margin-bottom:20px;'
                           )
        thumbnail_btn = SPAN(
                             SPAN('Select a file', _class='manualupload-fakebtn btn btn-default btn-sm', _type='button'),
                             _class='btn-group btn-group-justified manualupload-fakebtn-div'
                             )
    else:
        tag_loading = SPAN(_class='fa fa-spin fa-refresh pull-right tag-loading')
        elementid_input = INPUT(_name='elementid', _id='elementid', _type='hidden')
        submitbtn = BUTTON('Update',
                           _id='element-update',
                           _class='btn btn-info element-form-submit bold',
                           _style='width:100%;margin-bottom:20px;'
                           )
        thumbnail_btn = SPAN(
                             INPUT(_id='edit-thumbnail-orig', _class='hidden'),
                             SPAN('Reset', _id='edit-thumbnail-reset', _class='btn btn-inverse btn-sm', _type='button'),
                             SPAN('Select a file', _class='manualupload-fakebtn btn btn-default btn-sm', _type='button'),
                             _class='btn-group btn-group-justified manualupload-fakebtn-div'
                             )
        
        
    branch_opts = [OPTION('Select a Branch...', _value='')]
    for branch in getBranches():
        branch_opts.append(OPTION(branch.name.upper(), _value=branch.id))
    
    branch_select = SELECT(*branch_opts,
                           **{'_id':'{0}-branch-select'.format(mode),
                              '_class':'branch-select mode-{0} form-control'.format(mode),
                              '_data-orig':'',
                              }
                           )
    
    category_select = SELECT(**{'_id':'{0}-category-select'.format(mode),
                                '_name':'categoryid',
                                '_class':'category-select mode-{0} form-control'.format(mode),
                                '_data-orig':'',
                                }
                             )
    
    form = FORM(
                elementid_input,
                INPUT(_name='tags', _type='hidden'),
                DIV(
                    DIV(
                        DIV(
                            SPAN('New Element Name',
                                 _id='{0}-fullname'.format(mode),
                                 _class='fullname text-muted'
                                 ),
                            _style='margin-bottom:15px;'
                            ),
                        DIV(
                            DIV(
                                DIV(
                                    LABEL('Base Name', _class='text-label', _for='name'),
                                    INPUT(**{'_name':'name',
                                             '_id':'{0}-name'.format(mode),
                                             '_class':'form-control nameinput',
                                             '_placeholder':'[Basename]XCode',
                                             '_type':'text',
                                             '_data-orig':'',
                                             }
                                          ),
                                    _class='form-group'
                                    ),
                                DIV(
                                    LABEL('Element Code', _class='text-label', _for='code'),
                                    INPUT(**{'_name':'code',
                                             '_id':'{0}-code'.format(mode),
                                             '_class':'form-control nameinput',
                                             '_placeholder':'BasenameX[Code]',
                                             '_type':'text',
                                             '_data-orig':'',
                                             }
                                          ),
                                    _class='form-group'
                                    ),
                                DIV(
                                    LABEL('Resolution', _class='text-label', _for='resolution'),
                                    INPUT(**{'_name':'resolution',
                                             '_id':'{0}-resolution'.format(mode),
                                             '_class':'form-control',
                                             '_placeholder':'Resolution',
                                             '_type':'text',
                                             '_data-orig':'',
                                             }
                                          ),
                                    _class='form-group'
                                    ),
                                DIV(
                                    LABEL('Length', _class='text-label', _for='length'),
                                    INPUT(**{'_name':'length',
                                             '_id':'{0}-length'.format(mode),
                                             '_class':'form-control',
                                             '_placeholder':'Cut Length',
                                             '_type':'text',
                                             '_data-orig':'',
                                             }
                                          ),
                                    _class='form-group'
                                    ),
                                DIV(
                                    LABEL('Colourspace', _class='text-label', _for='colourspace'),
                                    INPUT(**{'_name':'colourspace',
                                             '_id':'{0}-colourspace'.format(mode),
                                             '_class':'form-control',
                                             '_placeholder':'Colourspace',
                                             '_type':'text',
                                             '_data-orig':'',
                                             }
                                          ),
                                    _class='form-group'
                                    ),
                                DIV(
                                    LABEL('Camera', _class='text-label', _for='camera'),
                                    INPUT(**{'_name':'camera',
                                             '_id':'{0}-camera'.format(mode),
                                             '_class':'form-control',
                                             '_placeholder':'Camera',
                                             '_type':'text',
                                             '_data-orig':'',
                                             }
                                          ),
                                    _class='form-group'
                                    ),
                                DIV(
                                    LABEL('Source', _class='text-label', _for='source'),
                                    INPUT(**{'_name':'source',
                                             '_id':'{0}-source'.format(mode),
                                             '_class':'form-control',
                                             '_placeholder':'Source Show/Project',
                                             '_type':'text',
                                             '_data-orig':'',
                                             }
                                          ),
                                    _class='form-group'
                                    ),
                                DIV(
                                    LABEL('Alpha', _class='text-label', _for='alpha'),
                                    SELECT(
                                           OPTION('No', _value=0),
                                           OPTION('Yes', _value=1),
                                           **{'_name':'alpha',
                                              '_id':'{0}-alpha'.format(mode),
                                              '_class':'form-control',
                                              '_data-orig':'',
                                              }
                                           ),
                                    _class='form-group'
                                    ),
                                DIV(
                                    LABEL('Stereo', _class='text-label', _for='stereo'),
                                    SELECT(
                                           OPTION('No', _value=0),
                                           OPTION('Yes', _value=1),
                                           **{'_name':'stereo',
                                              '_id':'{0}-stereo'.format(mode),
                                              '_class':'form-control',
                                              '_data-orig':'',
                                              }
                                           ),
                                    _class='form-group'
                                    ),
                                DIV(
                                    LABEL('File Path', _class='text-label', _for='linuxpath'),
                                    INPUT(**{'_name':'linuxpath',
                                             '_id':'{0}-linuxpath'.format(mode),
                                             '_class':'form-control',
                                             '_placeholder':'Linux scheme',
                                             '_type':'text',
                                             '_data-orig':'',
                                             }
                                          ),
                                    _class='form-group'
                                    ),
                                DIV(
                                    LABEL('Notes', _class='text-label', _for='notes'),
                                    INPUT(**{'_name':'notes',
                                             '_id':'{0}-notes'.format(mode),
                                             '_class':'form-control',
                                             '_placeholder':'Notes',
                                             '_type':'text',
                                             '_data-orig':'',
                                             }
                                          ),
                                    _class='form-group'
                                    ),
                                _class='left-part'
                                ),
                            DIV(
                                submitbtn,
                                DIV(
                                    INPUT(_id='{0}-uploadvideo'.format(mode), _name='videofile', _class='videoupload', _type='file'),
                                    SPAN(
                                         SPAN('Select a Video', _class='videoupload-btn btn btn-default btn-sm', _type='button'),
                                         _class='btn-group btn-group-justified videoupload-btn-div'
                                         ),
                                    _class='manualupload-div'
                                    ),
                                DIV(_class='clearfix', _style='height:25px;'),
                                DIV(
                                    DIV('Thumbnail', _class='form-box-header text-label'),
                                    DIV(
                                        DIV('Drag an image here', _class='text-muted dragdrophint yesdragdrop'),
                                        DIV('Drag & drop not supported', _class='text-muted dragdrophint nodragdrop hidden'),
                                        _id='{0}-holder'.format(mode), _class='holder'
                                        ),
                                    DIV(
                                        INPUT(_id='{0}-uploadfile'.format(mode), _name='thumbnail', _class='manualupload', _type='file'),
                                        thumbnail_btn,
                                        _class='manualupload-div'
                                        ),
                                    DIV('File API & FileReader API not supported',
                                        _class='filereader'
                                        ),
                                    DIV('XHR2 FormData is not supported', _class='formdata'),
                                    DIV('XHR2 upload progress is not supported', _class='progress'),
                                    TAG.progress(0,
                                                 _id='{0}-uploadprogress'.format(mode),
                                                 _class='uploadprogress hidden',
                                                 _min=0, _max=100, _value=0
                                                 ),
                                    DIV(#INPUT(_id='{0}-thumbnail-input'.format(mode), _type='hidden'),INPUT(_id='thumbnail-add', _class='btn btn-default hidden', _type='button', _value='Upload'),DIV(_id='thumbnail-drop', _class='droppable'),
                                        _class='inside'
                                        ),
                                    _id='{0}-thumbnail'.format(mode),
                                    _class='form-box'
                                    ),
                                DIV(
                                    DIV('Branch ', SPAN(_class='fa fa-link'), ' Category', _class='form-box-header text-label'),
                                    DIV(
                                        DIV(branch_select, _class='form-group'),
                                        DIV(category_select, _class='form-group'),
                                        EM('Select category for the element', _class='text-muted'),
                                        _class='inside'
                                        ),
                                    _class='form-box'
                                    ),
                                DIV(
                                    DIV('Tags',
                                        tag_loading,
                                        _class='form-box-header text-label'
                                        ),
                                    INPUT(_id='{0}-tag-add'.format(mode), _name='tags_add', _class='hidden'),
                                    INPUT(_id='{0}-tag-remove'.format(mode), _name='tags_remove', _class='hidden'),
                                    DIV(
                                        DIV(
                                            INPUT(**{'_id': '{0}-tag-input'.format(mode),
                                                     '_class': 'form-control typeahead tag-input',
                                                     '_type': 'text',
                                                     '_data-role':'tagsinput1'
                                                     }
                                                  ),
                                            _class='tag-control'
                                            ),
                                        DIV(
                                            EM('Only existing tags can be used'),
                                            BUTTON('Reset',
                                                   _id='{0}-tag-reset'.format(mode),
                                                   _class='btn btn-inverse btn-sm pull-right',
                                                   _type='button',
                                                   _style='margin-top:-5px;'
                                                   ),
                                            _class='text-muted',
                                            _style='margin:10px 0;'
                                            ),#DIV(_id='{0}-tag-list'.format(mode), _class='divarea'),
                                        DIV(
                                            SPAN('Most used tags'),
                                            DIV(_id='{0}-tag-mostused'.format(mode),
                                                _class='tag-board'
                                                ),
                                            _style='margin-top:10px;'
                                            ),
                                        _class='inside'
                                        ),
                                    _class='form-box'
                                    ),
                                _class='right-part'
                                ),
                            DIV(
                                DIV(''),
                                _class='bottom-part'
                                ),
                            _class='form-body-content'
                            ),
                        _class='form-body'
                        ),
                    _class='form-area'
                    ),
                _id='form-{0}'.format(mode),
                _name='form-{0}'.format(mode)
                )
    
    return form

# DEPRECATED
@auth.requires_login()
def retireElement():
    """Retire an element (not delete)
    """
    element_id = int(request.vars.elementid)
    db(db.xelements_element.id==element_id).update(retired=1)

@auth.requires_login()
def deleteElement():
    """Delete an element
    """
    THUMB_DIR = '/xv_archive/elements/thumbs/'
    MOVIE_DIR = '/xv_archive/elements/movies/'
    
    row = db(db.xelements_element.id==int(request.vars.elementid)).select().first()
    if row:
        # delete thumbnail and video file
        try:
            thumbfile = os.path.join(THUMB_DIR, row.thumbnail)
            os.remove(thumbfile)
            
        except Exception, e:
            pass
        try:
            videofile = os.path.join(MOVIE_DIR, row.videofile)
            os.remove(videofile)
        except Exception,e:
            pass
        db(db.xelements_element.id==int(request.vars.elementid)).delete()

@auth.requires_login()
def updateElements():
    """Bulk update elements
    """
    #logger.debug(request.vars)
    
    ids = map(int, request.vars.ids.split(','))
    resolution = request.vars.resolution
    cutlength = request.vars.cutlength
    colourspace = request.vars.colourspace
    camera = request.vars.camera
    alpha = request.vars.alpha
    stereo = request.vars.stereo
    source = request.vars.source
    notes = request.vars.notes
    categoryid = request.vars.categoryid
    
    if ids:
        data = {}
        
        if resolution:
            data['resolution'] = resolution
            m = re.match('(\d+)x(\d+)', resolution)
            if m:
                data['width'] = int(m.group(1))
                data['height'] = int(m.group(2))
                
        if cutlength:
            data['cut_length'] = cutlength
        if colourspace:
            data['colourspace'] = colourspace
        if camera:
            data['camera'] = camera
        if alpha:
            data['alpha'] = alpha
        if stereo:
            data['stereo'] = stereo
        if source:
            data['source'] = source
        if notes:
            data['internal_notes'] = notes
        if categoryid:
            data['category_id'] = categoryid
        
        if data:
            data['date_updated'] = datetime.now()
            ret = db(db.xelements_element.id.belongs(ids)).update(**data)
            logger.debug('Elements update: {0} - {1}'.format(','.join(str(x) for x in ids), ret))
        
        if request.vars.tags:
            tagids = list(set(map(int, request.vars.tags.split(','))))
            db(db.xelements_tagmap.element_id.belongs(ids)).delete()
            
            tag_data = []
            for eid in ids:
                tag_data.extend(map(lambda x: {'element_id':eid, 'tag_id':x}, tagids))
            tag_ret = db.xelements_tagmap.bulk_insert(tag_data)
            
    return ''
    
@auth.requires_login()
def quickUpdateElement():
    """Quick update element
    """
    THUMB_DIR = '/xv_archive/elements/thumbs/'
    
    element_id = int(request.vars.elementid)
    element_name = request.vars.name
    element_code = request.vars.code
    resolution = request.vars.resolution
    cutlength = request.vars.cutlength
    if not cutlength or cutlength == 'null':
        cutlength = 0
    
    colourspace = request.vars.colourspace
    camera = request.vars.camera
    alpha = request.vars.alpha
    stereo = request.vars.stereo
    source = request.vars.source
    notes = request.vars.notes
    categoryid = request.vars.categoryid
    
    fields = {'name':element_name,
              'element_code':element_code,
              'resolution':resolution,
              'cut_length':cutlength,
              'colourspace':colourspace,
              'camera':camera,
              'alpha':alpha,
              'stereo':request.vars.stereo,
              'category_id':categoryid,
              'source':source,
              'internal_notes':notes,
              'date_updated':datetime.now()
              }
    
    m = re.match('(\d+)x(\d+)', resolution)
    if m:
        fields['width'] = int(m.group(1))
        fields['height'] = int(m.group(2))
        
    ret = db(db.xelements_element.id==element_id).update(**fields)
    logger.debug('Element update: {0} - {1}'.format(element_id, ret))
    
    tags_add = request.vars.tags_add # '3,5,8'
    tags_remove = request.vars.tags_remove
    
    elementTagUpdate(element_id, tags_add, tags_remove)
    
    return ''
    
@auth.requires_login()
def createUpdateElement():
    """Create or update element
    """
    MOVIE_DIR = '/xv_archive/elements/movies/'
    THUMB_DIR = '/xv_archive/elements/thumbs/'
    
    element_name = request.vars.name
    element_code = request.vars.code
    videofile = request.vars.videofile
    resolution = request.vars.resolution.lower()
    cutlength = request.vars.length
    if not cutlength or cutlength == 'null':
        cutlength = 0
    
    colourspace = request.vars.colourspace
    camera = request.vars.camera
    source = request.vars.source
    alpha = request.vars.alpha
    stereo = request.vars.stereo
    filepath = request.vars.linuxpath
    qtpath = request.vars.qtpath
    notes = request.vars.notes
    categoryid = request.vars.categoryid
    
    d = datetime.now()
    
    fields = {'name':element_name,
              'element_code':element_code,
              'resolution':resolution,
              'cut_length':cutlength,
              'colourspace':colourspace,
              'camera':camera,
              'source':source,
              'alpha':alpha,
              'stereo':stereo,
              'file_path':filepath,
              'qt_path':qtpath,
              'internal_notes':notes,
              'category_id':categoryid,
              'date_updated':d,
              }
    logger.debug(videofile)
    # do not allow null video
    if videofile:
        fields['videofile'] = videofile
    
    m = re.match('(\d+)x(\d+)', resolution)
    if m:
        fields['width'] = int(m.group(1))
        fields['height'] = int(m.group(2))
        
    element_fullname = '{0}X{1}'.format(element_name, element_code)
    
    if request.vars.thumbnail:
        fileitem = request.vars.thumbnail[1] # ['', FieldStorage()]
        if fileitem != 'undefined':
            uploadname = fileitem.filename
            _, ext = os.path.splitext(uploadname)
            thumbname = '{0}{1}'.format(element_fullname, ext)
            thumbpath = os.path.join(THUMB_DIR, thumbname)
            with open(thumbpath, 'wb') as fout:
                fout.write(fileitem.file.read())
            fields['thumbnail'] = thumbname
    
    if request.vars.videofile:
        fileitem = request.vars.videofile[1] # ['', FieldStorage()]
        if fileitem != 'undefined':
            uploadname = fileitem.filename
            _, ext = os.path.splitext(uploadname)
            videoname = '{0}{1}'.format(element_fullname, ext)
            vidpath = os.path.join(MOVIE_DIR, videoname)
            with open(vidpath, 'wb') as fout:
                fout.write(fileitem.file.read())
            fields['videofile'] = videoname
    
    if request.vars.elementid:
        # Update element
        new_element = False
        element_id = int(request.vars.elementid)
        ret = db(db.xelements_element.id==element_id).update(**fields)
        logger.debug('Element updated: ')
        logger.debug(ret)
    else:
        # Create element
        new_element = True
        fields['date_created'] = d
        ret = db.xelements_element.insert(**fields)
        element_id = ret
        logger.debug('Element created: ')
        logger.debug(ret)
        
        # update ticker
        link = A(STRONG(element_fullname), _href=URL('detail','index',args=[element_id])).xml()
        news = '{0} {1} added element {2}'.format(auth.user.first_name, auth.user.last_name, link)
        addXelementsUpdate(element_id, 'element', news)
        
    # update Tags
    tags_add = request.vars.tags_add # '3,5,8'
    tags_remove = request.vars.tags_remove
    
    if element_id:
        elementTagUpdate(element_id, tags_add, tags_remove)
        
    return ''

@auth.requires_login()
def elementTagUpdate(element_id, tags_add=[], tags_remove=[]):
    """Add or delete tags
    @param element_id: element id (int)
    @param tags_add: list of tag strings to be added to the element
    @param tags_remove: list of tag strings to be removed from the element
    """
    if tags_add:
        # find out existing tags and new tags that need to be created first
        tag_names = tags_add.split(',')
        rows = db(db.xelements_tag.name.belongs(tag_names)).select()
        tag_ids_add = [x.id for x in rows]
        existing_tags = [x.name for x in rows]
        new_tags = set(tag_names) - set(existing_tags)
        if new_tags:
            # create new tags
            """
            bulk_new = [{'name':n, 'code':n} for n in new_tags]
            new_tag_ids = db.xelements_tag.bulk_insert(bulk_new)
            tag_ids_add.extend(new_tag_ids)
            """
            for new_tag in new_tags:
                try:
                    tid = db.xelements_tag.insert(name=new_tag, code=new_tag)
                    tag_ids_add.append(tid)
                except Exception, e:
                    logger.error("Failed to create tag '{0}'".format(new_tag))
                
        if tag_ids_add:
            tag_adds = [{'element_id':element_id, 'tag_id':t} for t in tag_ids_add]
            db.xelements_tagmap.bulk_insert(tag_adds)
            
    if tags_remove:
        tagdels = db(db.xelements_tag.name.belongs(tags_remove.split(','))).select(db.xelements_tag.id)
        if tagdels:
            tag_ids_remove = [d.id for d in tagdels]
            db((db.xelements_tagmap.element_id==element_id) & \
               (db.xelements_tagmap.tag_id.belongs(tag_ids_remove))).delete()
               
    return ''

def elementsTableFrame(name='elements'):
    
    thcells = [
               TH('Name'),
               TH('Category'),
               TH('Resolution'),
               TH('Length'),
               TH('Colourspace'),
               TH('Alpha'),
               TH('Updated'),
               TH('element id'),
               TH('branch id'),
               TH('category id'),
               TH('linux path'),
               TH('qt path'),
               TH('notes'),
               TH('thumb'),
               TH('video'),
               TH('stereo'),
               TH('source'),
               TH('camera'),
               ]
    
    theader = [TH(INPUT(_id='check-all-rows', _class='dt-checkbox', _type='checkbox'), _class='th-center')] + thcells
    tfooter = [TH('')] + thcells
    
    table = TABLE(
                  THEAD(TR(*theader)),
                  TFOOT(TR(*tfooter)),
                  _id='{0}-table'.format(name),
                  _class='table table-striped table-bordered dataTable'
                  )
    return table
    
def elementsTable():
    
    columns = [
               'checkbox',
               'xelements_element.name',
               'xelements_category.name',
               'xelements_element.resolution',
               'xelements_element.cut_length',
               'xelements_element.colourspace',
               'xelements_element.alpha',
               'xelements_element.date_updated',
               'xelements_element.id',
               'xelements_branch.id',
               'xelements_category.id',
               'xelements_element.file_path',
               'xelements_element.qt_path',
               'xelements_element.internal_notes',
               'xelements_element.thumbnail',
               'xelements_element.videofile',
               'xelements_element.stereo',
               'xelements_element.source',
               'xelements_element.camera',
               ]
    
    result = DataTablesServer(request.vars, columns, 'xelements_element.id', 'element').output_result()
    
    return simplejson.dumps(result)

def elements():
    """
    """
    page = ''
    element_id = None
    if request.get_vars:
        element_id = request.get_vars.get('id')
    
    # get element data for edit link navigation
    edata = None
    if element_id:
        row = db(db.xelements_element.id==element_id).select().first()
        if row:
            edata = row.as_dict()
            brow = db((db.xelements_category.id==edata['category_id']) & (db.xelements_branch.id==db.xelements_category.branch_id)).select(db.xelements_branch.id).first()
            edata['branch_id'] = brow.id
    
    etable = elementsTableFrame()
    
    add_form = elementForm()
    edit_form = elementForm('edit')
    
    row_menu = DIV(
                   SPAN(
                        A('Edit',
                          **{'_href': '#edit',
                             '_title': 'Edit this element',
                             '_data-elementid': 'ELEMENTID',
                             '_data-elementdata': 'ELEMENTDATA',
                             }
                          ),
                        ' | ',
                        _class='row-edit'
                        ),
                   SPAN(
                        A('Quick Edit',
                          **{'_href': '#',
                             '_class': 'quickedit',
                             '_title': 'Quick Edit element',
                             '_data-elementid': 'ELEMENTID',
                             '_data-elementdata': 'ELEMENTDATA',
                             }
                          ),
                        ' | ',
                        _class='row-edit'
                        ),
                   SPAN(
                        A('Delete', _href='#ELEMENTID', _title='Delete this element', _class='text-danger delete-item'),
                        ' | ',
                        _class='row-delete'
                        ),
                   SPAN(
                        A('View', _href=URL('detail', 'index', args=['ELEMENTID']), _title='View this element', _target='_blank'),
                        _class='row-view'
                        ),
                   _class='row-menu'
                   )
    
    category_opts = []
    for category in getCategories():
        category_opts.append(OPTION(category.name.upper(), _value=category.id))
    
    edit_inline = TR(
                     TD(
                        DIV(
                            H4('quick edit', _class='inline-header'),
                            INPUT(_class='inline-edit-element-id hidden'),
                            DIV(
                                SPAN('Basename', _class='inline-label'),
                                SPAN(
                                     INPUT(_class='form-control inline-edit-element-name inline-name-input input-sm', _type='text'),
                                     _class='inline-input'
                                     ),
                                _class='inline-group'
                                ),
                            DIV(
                                SPAN('Code', _class='inline-label'),
                                SPAN(
                                     INPUT(_class='form-control inline-edit-element-code inline-name-input input-sm', _type='text'),
                                     _class='inline-input'
                                     ),
                                _class='inline-group'
                                ),
                            DIV(
                                SPAN('Resolution', _class='inline-label'),
                                SPAN(
                                    INPUT(_class='form-control inline-edit-element-resolution input-sm', _type='text'),
                                    _class='inline-input'
                                    ),
                                _class='inline-group'
                                ),
                            DIV(
                                SPAN('Length', _class='inline-label'),
                                SPAN(
                                    INPUT(_class='form-control inline-edit-element-cutlength input-sm', _type='text'),
                                    _class='inline-input'
                                    ),
                                _class='inline-group'
                                ),
                            DIV(
                                SPAN('Colourspace', _class='inline-label'),
                                SPAN(
                                    INPUT(_class='form-control inline-edit-element-colourspace input-sm', _type='text'),
                                    _class='inline-input'
                                    ),
                                _class='inline-group'
                                ),
                            DIV(
                                SPAN('Camera', _class='inline-label'),
                                SPAN(
                                    INPUT(_class='form-control inline-edit-element-camera input-sm', _type='text'),
                                    _class='inline-input'
                                    ),
                                _class='inline-group'
                                ),
                            DIV(
                                SPAN('Source', _class='inline-label'),
                                SPAN(
                                    INPUT(_class='form-control inline-edit-element-source input-sm', _type='text'),
                                    _class='inline-input'
                                    ),
                                _class='inline-group'
                                ),
                            _class='inline-edit-col inline-col-left',
                            ),
                        DIV(
                            DIV(
                                SPAN('Notes', _class='inline-label'),
                                DIV(
                                    TEXTAREA(_class='form-control inline-edit-element-notes input-sm'),
                                    _style='clear:both',
                                    ),
                                _class='inline-group'
                                ),
                            DIV(
                                SPAN('Category', _class='inline-label'),
                                SPAN(
                                     SELECT(*category_opts, _class='form-control input-sm inline-edit-category-select'),
                                     _class='inline-input'
                                     ),
                                _class='inline-group'
                                ),
                            DIV(
                                SPAN('Alpha', _class='inline-label'),
                                SPAN(
                                     SELECT(
                                            OPTION('No', _value=0),
                                            OPTION('Yes', _value=1),
                                            _class='form-control inline-edit-element-alpha input-sm',
                                            ),
                                     _class='inline-input'
                                     ),
                                _class='inline-group'
                                ),
                            DIV(
                                SPAN('Stereo', _class='inline-label'),
                                SPAN(
                                     SELECT(
                                            OPTION('No', _value=0),
                                            OPTION('Yes', _value=1),
                                            _class='form-control inline-edit-element-stereo input-sm',
                                            ),
                                     _class='inline-input'
                                     ),
                                _class='inline-group'
                                ),
                            _class='inline-edit-col inline-col-middle',
                            ),
                        DIV(
                            DIV(
                                DIV(
                                    SPAN('Tags', _class='inline-label'),
                                    SPAN(_class='fa fa-spin fa-refresh pull-right tag-loading', _style='line-height:2;'),
                                    ),
                                INPUT(_class='inline-edit-tag-add hidden', _name='tags_add'),
                                INPUT(_class='inline-edit-tag-remove hidden', _name='tags_remove'),
                                INPUT(
                                      **{'_class':'form-control inline-edit-element-tags input-sm',
                                         '_type':'text',
                                         '_data-role':'tagsinput1'
                                         }
                                      
                                      ),
                                _id='inline-edit-tag',
                                _class='inline-group'
                                ),
                            _class='inline-edit-col inline-col-middle',
                            ),
                        DIV(
                            BUTTON('Cancel', _class='btn btn-default btn-xs inline-edit-cancel'),
                            BUTTON('Update', _class='btn btn-primary btn-xs pull-right inline-edit-update'),
                            _class='inline-edit-btns'
                            ),
                        _colspan=8,
                        _class='',
                        ),
                      _class='inline-edit-row'
                      )
    
    category_opts.insert(0, OPTION('- No Change -', _value=''))
    
    edit_bulk = TR(
                     TD(
                        DIV(
                            H4('Bulk Edit ', SMALL('Leave blank for no change'), _class='inline-header'),
                            SELECT(_class='form-control bulk-edit-element-id', _multiple=True),
                            _class='inline-edit-col inline-col-left',
                            ),
                        DIV(
                            DIV(
                                SPAN('Notes', _class='inline-label'),
                                DIV(
                                    TEXTAREA(_class='form-control bulk-edit-element-notes input-sm', _placeholder='- No Change -'),
                                    _style='clear:both',
                                    ),
                                _class='inline-group'
                                ),
                            DIV(
                                SPAN('Category', _class='inline-label'),
                                SPAN(
                                     SELECT(*category_opts, _class='form-control input-sm bulk-edit-category-select'),
                                     _class='inline-input'
                                     ),
                                _class='inline-group'
                                ),
                            DIV(
                                SPAN('Alpha', _class='inline-label'),
                                SPAN(
                                     SELECT(
                                            OPTION('- No Change -', _value=''),
                                            OPTION('No', _value=0),
                                            OPTION('Yes', _value=1),
                                            _class='form-control bulk-edit-element-alpha input-sm',
                                            ),
                                     _class='inline-input'
                                     ),
                                _class='inline-group'
                                ),
                            DIV(
                                SPAN('Stereo', _class='inline-label'),
                                SPAN(
                                     SELECT(
                                            OPTION('- No Change -', _value=''),
                                            OPTION('No', _value=0),
                                            OPTION('Yes', _value=1),
                                            _class='form-control bulk-edit-element-stereo input-sm',
                                            ),
                                     _class='inline-input'
                                     ),
                                _class='inline-group'
                                ),
                            _class='inline-edit-col inline-col-middle',
                            ),
                        DIV(
                            DIV(
                                DIV(SPAN('Tags', _class='inline-label')),
                                INPUT(_class='bulk-edit-tag-add hidden', _name='tags_add'),
                                INPUT(_class='bulk-edit-tag-remove hidden', _name='tags_remove'),
                                INPUT(_class='form-control bulk-edit-element-tags input-sm', _type='text'),
                                _class='inline-group'
                                ),
                            DIV(
                                SPAN('Resolution', _class='inline-label'),
                                SPAN(
                                    INPUT(_class='form-control bulk-edit-element-resolution input-sm', _type='text', _placeholder='- No Change -'),
                                    _class='inline-input'
                                    ),
                                _class='inline-group'
                                ),
                            DIV(
                                SPAN('Length', _class='inline-label'),
                                SPAN(
                                    INPUT(_class='form-control bulk-edit-element-cutlength input-sm', _type='text', _placeholder='- No Change -'),
                                    _class='inline-input'
                                    ),
                                _class='inline-group'
                                ),
                            DIV(
                                SPAN('Colourspace', _class='inline-label'),
                                SPAN(
                                    INPUT(_class='form-control bulk-edit-element-colourspace input-sm', _type='text', _placeholder='- No Change -'),
                                    _class='inline-input'
                                    ),
                                _class='inline-group'
                                ),
                            DIV(
                                SPAN('Camera', _class='inline-label'),
                                SPAN(
                                    INPUT(_class='form-control inline-edit-element-camera input-sm', _type='text', _placeholder='- No Change -'),
                                    _class='inline-input'
                                    ),
                                _class='inline-group'
                                ),
                            DIV(
                                SPAN('Source', _class='inline-label'),
                                SPAN(
                                    INPUT(_class='form-control inline-edit-element-source input-sm', _type='text', _placeholder='- No Change -'),
                                    _class='inline-input'
                                    ),
                                _class='inline-group'
                                ),
                            _class='inline-edit-col inline-col-middle',
                            ),
                        DIV(
                            BUTTON('Cancel', _class='btn btn-default btn-xs bulk-edit-cancel'),
                            BUTTON('Update', _class='btn btn-primary btn-xs pull-right bulk-edit-update'),
                            _class='inline-edit-btns'
                            ),
                        _colspan=8,
                        _class='',
                        ),
                      _class='bulk-edit-row'
                      )
    
    menu = buildMenu('elements')
    
    # Tags
    #tag_list = db(db.xelements_tag.id>0).select(orderby=db.xelements_tag.name).as_list()
    tag_list = []
    for row in db(db.xelements_tag.id>0).select(orderby=db.xelements_tag.name):
        tag_list.append({'name':row.name})
    
    return dict(menu=menu,
                page=page,
                table=etable,
                rowmenu=row_menu,
                tag_list=tag_list,
                addform=add_form,
                editform=edit_form,
                editinline=edit_inline,
                editbulk=edit_bulk,
                elementdata=edata,
                )

@auth.requires_login()
def deleteCategory():
    """Delete Category - move child Elements to default Category
    """
    categoryid = int(request.vars.categoryid)
    # first update all child categories to default branch - DEFAULT_BRANCH
    u = db(db.xelements_element.category_id==categoryid).update(category_id=DEFAULT_CATEGORY)
    # returns 1 if update successful
    
    d = db(db.xelements_category.id==categoryid).delete()
    # returns 1 if update successful
    return ''

@auth.requires_login()
def updateCategories():
    """Bulk update Categories
    """
    ids = map(int, request.vars.ids.split(','))
    branch_id = request.vars.branchid
    colour = request.vars.colour.replace('#','')
    
    data = {}
    if branch_id:
        data['branch_id'] = int(branch_id)
    if colour:
        data['colour'] = colour
    
    if data:
        db(db.xelements_category.id.belongs(ids)).update(**data)
    
    return ''

@auth.requires_login()
def createUpdateCategory():
    """Create or update Category
    """
    name = request.vars.name
    branchid = int(request.vars.branchid)
    colour = request.vars.colour.replace('#','')
    
    msg = ''
    
    if request.vars.categoryid:
        # Update Category
        category_id = int(request.vars.categoryid)
        ret = db(db.xelements_category.id==category_id).update(name=name,
                                                               branch_id=branchid,
                                                               colour=colour
                                                               )
        msg = 'Category updated.'
        logger.debug(msg)
        logger.debug(ret)
    else:
        # Create category
        existing = db((db.xelements_category.name==name) & (db.xelements_branch.id==branchid)).select()
        if len(existing):
            return simplejson.dumps({'error':1, 'msg':'Category already exists'})
        
        ret = db.xelements_category.insert(name=name,
                                           branch_id=branchid,
                                           colour=colour
                                           )
        msg = 'Category created: {0}'.format(ret)
        logger.debug(msg)
        
        # update ticker
        link = A(STRONG(name), _href='{0}{1}'.format(URL('default','index'), '#!/category/{0}'.format(ret))).xml()
        news = '{0} {1} created category {2}'.format(auth.user.first_name, auth.user.last_name, link)
        addXelementsUpdate(ret, 'category', news)
        
    return simplejson.dumps({'error':0, 'msg':msg})
    
def categoriesTableFrame(name='categories'):
    """
    """
    thcells = [
               TH('Name'),
               TH('Colour'),
               TH('Branch'),
               TH('Elements'),
               TH('category id'),
               TH('branch id'),
               ]
    
    theader = [TH(INPUT(_id='check-all-rows', _class='dt-checkbox', _type='checkbox'), _class='th-center')] + thcells
    tfooter = [TH('')] + thcells
    
    table = TABLE(
                  THEAD(TR(*theader)),
                  TFOOT(TR(*tfooter)),
                  _id='{0}-table'.format(name),
                  _class='table table-striped table-bordered dataTable'
                  )
    return table
    
def categoriesTable():
    """
    """
    columns = [
               'checkbox',
               'xelements_category.name',
               'xelements_category.colour',
               'xelements_branch.name',
               'COUNT(xelements_element.id)',
               'xelements_category.id',
               'xelements_branch.id',
               ]
    
    result = DataTablesServer(request.vars, columns, 'xelements_category.id', 'category').output_result()
    
    return simplejson.dumps(result)

def categoryForm(mode='new'):
    """
    """
    if mode == 'new':
        submit_btn = BUTTON('Add New Category', _id='category-create', _class='btn btn-primary category-form-submit')
    else:
        submit_btn = BUTTON('Update', _id='category-update', _class='btn btn-info category-form-submit')
    
    branch_opts = [OPTION('Select a Branch...', _value='')]
    for branch in getBranches():
        branch_opts.append(OPTION(branch.name.upper(), _value=branch.id))
    
    form = FORM(
                DIV(
                    LABEL('Name', _class='text-label', _for='name'),
                    INPUT(**{'_name':'name',
                             '_id':'{0}-name'.format(mode),
                             '_class':'form-control nameinput',
                             '_placeholder':'{0} category name'.format(mode),
                             '_type':'text',
                             '_data-orig':'',
                             }
                          ),
                    _class='form-group'
                    ),
                DIV(
                    LABEL('Branch', _class='text-label', _for='name'),
                    SELECT(*branch_opts,
                           **{'_id':'{0}-branch'.format(mode),
                              '_name':'branchid',
                              '_class':'branch-select mode-{0} form-control'.format(mode),
                              '_data-orig':'',
                              }
                           ),
                    _class='form-group'
                    ),
                DIV(
                    LABEL('Colour', _class='text-label', _for='name'),
                    DIV(
                        INPUT(**{'_name':'colour',
                                 '_id':'{0}-colour'.format(mode),
                                 '_class':'form-control',
                                 '_placeholder':'hex colour',
                                 '_type':'text',
                                 '_data-orig':'',
                                 '_value': '#e32020',
                                 }
                              ),
                        SPAN(I(), _class="input-group-addon"),
                        _class='input-group colourpicker'
                        ),
                    _class='form-group'
                    ),
                submit_btn,
                _id='category-form-{0}'.format(mode),
                _name='category-form-{0}'.format(mode)
                )
    return form

def group():
    """
    """
    if len(request.args) > 0:
        page = 'group-{0}'.format(request.args[0])
    else:
        page = 'group-home'
    menu = buildMenu('group')
    
    ctable = categoriesTableFrame()
    
    row_menu = DIV(
                   SPAN(
                        A('Quick Edit',
                          **{'_href': '#edit',
                             '_title': 'Edit this element',
                             '_data-categoryid': 'TARGETID',
                             '_data-categorydata': 'TARGETDATA',
                             }
                          ),
                        ' | ',
                        _class='row-edit'
                        ),
                   SPAN(
                        A('Delete', _href='#TARGETID', _title='Delete this category', _class='text-danger delete-item'),
                        ' | ',
                        _class='row-delete'
                        ),
                   SPAN(
                        A('View', _href=URL('default', 'index', args=['category', 'TARGETID']), _title='View this category', _target='_blank'),
                        _class='row-view'
                        ),
                   _class='row-menu'
                   )
    
    row_menu_default = DIV(
                           SPAN(
                                SPAN('Edit', _title='Cannot edit default category'),
                                ' | ',
                                _class='row-edit'
                                ),
                           SPAN(
                                SPAN('Delete', _title='Cannot delete default category'),
                                ' | ',
                                _class='row-delete'
                                ),
                           SPAN(
                                A('View', _href=URL('default', 'index', args=['category','TARGETID']), _title='View this branch', _target='_blank'),
                                _class='row-view'
                                ),
                           _class='row-menu'
                           )
    
    branch_opts = []
    for branch in getBranches():
        branch_opts.append(OPTION(branch.name.upper(), _value=branch.id))
        
    edit_inline = TR(
                     TD(
                        DIV(
                            INPUT(_class='form-control inline-edit-category-name', _type='text'),
                            _class='inline-edit-col inline-col-left',
                            ),
                        DIV(
                            DIV(
                                INPUT(_class='form-control',
                                      _type='text',
                                      _placeholder='hex colour',
                                      _value='',
                                      ),
                                SPAN(I(), _class="input-group-addon"),
                                _class='input-group inline-edit-category-colour'
                                ),
                            _class='inline-edit-col inline-col-narrow',
                            ),
                        DIV(
                            SELECT(*branch_opts, _class='form-control inline-edit-branch-select'),
                            _class='inline-edit-col inline-col-wide',
                            ),
                        DIV(
                            BUTTON('Cancel', _class='btn btn-default btn-xs inline-edit-cancel'),
                            BUTTON('Update', _class='btn btn-primary btn-xs pull-right inline-edit-update'),
                            _class='inline-edit-btns'
                            ),
                        _colspan=5,
                        ),
                      _class='inline-edit-row'
                      )
    
    branch_opts.insert(0, OPTION('- No Change -', _value=''))
    # bulk edit
    edit_bulk = TR(
                     TD(
                        DIV(
                            SELECT(_class='form-control bulk-edit-category-id', _multiple=True),
                            _class='inline-edit-col inline-col-left',
                            ),
                        DIV(
                            INPUT(_class='bulk-edit-colour-enable', _type='checkbox'),
                            DIV(
                                INPUT(_class='form-control',
                                      _type='text',
                                      _placeholder='hex colour',
                                      _value='',
                                      _disabled=True,
                                      ),
                                SPAN(I(), _class="input-group-addon"),
                                _class='input-group bulk-edit-category-colour'
                                ),
                            _class='inline-edit-col inline-col-narrow',
                            ),
                        DIV(
                            SELECT(*branch_opts, _class='form-control bulk-edit-branch-select'),
                            _class='inline-edit-col inline-col-wide',
                            ),
                        DIV(
                            BUTTON('Cancel', _class='btn btn-default btn-xs bulk-edit-cancel'),
                            BUTTON('Update', _class='btn btn-primary btn-xs pull-right bulk-edit-update'),
                            _class='inline-edit-btns'
                            ),
                        _colspan=5,
                        ),
                      _class='bulk-edit-row'
                      )
    
    
    add_form = categoryForm()
    
    return dict(menu=menu,
                page=page,
                table=ctable,
                rowmenu=row_menu,
                rowmenudefault=row_menu_default,
                addform=add_form,
                editbulk=edit_bulk,
                editinline=edit_inline,
                defaultval='Uncategorized',
                defaultid=52,
                )

@auth.requires_login()
def deleteBranch():
    """Delete Branch - move child Categories to default Branch
    """
    branchid = int(request.vars.branchid)
    # first update all child categories to default branch - DEFAULT_BRANCH
    u = db(db.xelements_category.branch_id==branchid).update(branch_id=DEFAULT_BRANCH)
    # returns 1 if update successful
    
    d = db(db.xelements_branch.id==branchid).delete()
    # returns 1 if update successful
    
    return ''
    
@auth.requires_login()
def createUpdateBranch():
    """Create or update Branch
    """
    name = request.vars.name
    msg = ''
    
    if request.vars.branchid:
        # Update
        branch_id = int(request.vars.branchid)
        ret = db(db.xelements_branch.id==branch_id).update(name=name)
        if ret:
            msg = 'Branch updated.'
        else:
            msg = 'Failed to update Branch.'
        logger.debug(msg)
        logger.debug(ret)
    else:
        # Create category
        existing = db(db.xelements_branch.name==name).select()
        if len(existing):
            return simplejson.dumps({'error':1, 'msg':'Branch with same name already exists'})
        
        ret = db.xelements_branch.insert(name=name)
        msg = 'Branch created: {0}'.format(ret)
        logger.debug(msg)
        
        # update ticker
        link = A(STRONG(name), _href='{0}{1}'.format(URL('default','index'), '#!/branch/{0}'.format(ret))).xml()
        news = '{0} {1} created branch {2}'.format(auth.user.first_name, auth.user.last_name, link)
        addXelementsUpdate(ret, 'branch', news)
        
    return simplejson.dumps({'error':0, 'msg':msg})
    
def branchesTableFrame(name='branches'):
    """
    """
    thcells = [
               TH('Name'),
               TH('Categories'),
               TH('id'),
               ]
    
    theader = [TH(INPUT(_id='check-all-rows', _class='dt-checkbox', _type='checkbox'), _class='th-center')] + thcells
    tfooter = [TH('')] + thcells
    
    table = TABLE(
                  THEAD(TR(*theader)),
                  TFOOT(TR(*tfooter)),
                  _id='{0}-table'.format(name),
                  _class='table table-striped table-bordered dataTable'
                  )
    return table
    
def branchesTable():
    """
    """
    columns = [
               'checkbox',
               'xelements_branch.name',
               'COUNT(xelements_category.id)',
               'xelements_branch.id',
               ]
    
    result = DataTablesServer(request.vars, columns, 'xelements_branch.id', 'branch').output_result()
    
    return simplejson.dumps(result)
    
    
def branches():
    """
    """
    page = 'group-branches'
    menu = buildMenu('branches')
    
    btable = branchesTableFrame()
    
    row_menu = DIV(
                   SPAN(
                        A('Quick Edit',
                          **{'_href': '#',
                             '_title': 'Edit this branch',
                             '_data-branchid': 'TARGETID',
                             '_data-branchdata': 'TARGETDATA',
                             }
                          ),
                        ' | ',
                        _class='row-edit'
                        ),
                   SPAN(
                        A('Delete', _href='#TARGETID', _title='Delete this branch', _class='text-danger delete-item'),
                        ' | ',
                        _class='row-delete'
                        ),
                   SPAN(
                        A('View', _href=URL('default', 'index', args=['branch','TARGETID']), _title='View this branch', _target='_blank'),
                        _class='row-view'
                        ),
                   _class='row-menu'
                   )
    
    row_menu_default = DIV(
                           SPAN(
                                SPAN('Edit', _title='Cannot edit default branch'),
                                ' | ',
                                _class='row-edit'
                                ),
                           SPAN(
                                SPAN('Delete', _title='Cannot delete default branch'),
                                ' | ',
                                _class='row-delete'
                                ),
                           SPAN(
                                A('View', _href=URL('default', 'index', args=['branch','TARGETID']), _title='View this branch', _target='_blank'),
                                _class='row-view'
                                ),
                           _class='row-menu'
                           )
    
    edit_inline = TR(
                     TD(
                        DIV(
                            INPUT(_class='form-control input-sm inline-edit-branch-name', _type='text'),
                            _class='inline-edit-col inline-col-left',
                            ),
                        DIV(
                            BUTTON('Cancel', _class='btn btn-default btn-xs inline-edit-cancel'),
                            BUTTON('Update', _class='btn btn-primary btn-xs pull-right inline-edit-update'),
                            _class='inline-edit-btns'
                            ),
                        _colspan=3,
                        ),
                      _class='inline-edit-row'
                      )
    
    return dict(menu=menu,
                page=page,
                table=btable,
                rowmenu=row_menu,
                rowmenudefault=row_menu_default,
                editinline=edit_inline,
                defaultval='Unspecified',
                defaultid=14,
                )

def sanitizeCode(name):
    """
    """
    code = name.lower()
    q = re.compile('"')
    a = re.compile('\&')
    s = re.compile('\s+')
    return s.sub('_', a.sub('n', q.sub('', code))).lower()
    
def deleteTag():
    """Delete Tag
    """
    tagid = int(request.vars.id)
    d = db(db.xelements_tag.id==tagid).delete()
    # returns 1 if update successful
    return ''
    
def deleteTags():
    """Delete Tags
    """
    tagids = map(int, request.vars.ids.split(','))
    d = db(db.xelements_tag.id.belongs(tagids)).delete()
    # returns 1 if update successful
    return ''
    
def createUpdateTag():
    """Create or update Tag
    """
    name = request.vars.name
    msg = ''
    
    if request.vars.id:
        # Update
        tag_id = int(request.vars.id)
        code = sanitizeCode(name)
        ret = db(db.xelements_tag.id==tag_id).update(name=name, code=code)
        if ret:
            msg = 'Tag updated.'
        else:
            msg = 'Failed to update Tag.'
        logger.debug(msg)
        logger.debug(ret)
    else:
        # Create tag
        existing = db(db.xelements_tag.name==name).select()
        if len(existing):
            return simplejson.dumps({'error':1, 'msg':'Tag with same name already exists'})
        
        code = sanitizeCode(name)
        ret = db.xelements_tag.insert(name=name, code=code)
        msg = 'Tag created: {0}'.format(ret)
        logger.debug(msg)
        
    return simplejson.dumps({'error':0, 'msg':msg})
    
def tagsTableFrame(name='tags'):
    """
    """
    thcells = [
               TH('Name'),
               TH('Count'),
               TH('branch id'),
               TH('code')
               ]
    
    theader = [TH(INPUT(_id='check-all-rows', _class='dt-checkbox', _type='checkbox'), _class='th-center')] + thcells
    tfooter = [TH('')] + thcells
    table = TABLE(
                  THEAD(TR(*theader)),
                  TFOOT(TR(*tfooter)),
                  _id='{0}-table'.format(name),
                  _class='table table-striped table-bordered dataTable'
                  )
    return table
    
def tagsTable():
    """
    """
    columns = [
               'checkbox',
               'xelements_tag.name',
               'COUNT(xelements_tagmap.id)',
               'xelements_tag.id',
               'xelements_tag.code',
               ]
    
    result = DataTablesServer(request.vars, columns, 'xelements_tag.id', 'tag').output_result()
    
    return simplejson.dumps(result)

def tags():
    """
    """
    menu = buildMenu('tags')
    
    ttable = tagsTableFrame()
    
    row_menu = DIV(
                   SPAN(
                        A('Quick Edit',
                          **{'_href': '#edit',
                             '_title': 'Edit this tag',
                             '_data-targetid': 'TARGETID',
                             '_data-targetdata': 'TARGETDATA',
                             }
                          ),
                        ' | ',
                        _class='row-edit'
                        ),
                   SPAN(
                        A('Delete', _href='#TARGETID', _title='Delete this tag', _class='text-danger delete-item'),
                        ' | ',
                        _class='row-delete'
                        ),
                   SPAN(
                        A('View', _href=URL('default', 'index', args=['category', 'TARGETID']), _title='View this tag', _target='_blank'),
                        _class='row-view'
                        ),
                   _class='row-menu'
                   )
    
    row_menu_default = DIV(
                           SPAN(
                                SPAN('Edit', _title='Cannot edit default tag'),
                                ' | ',
                                _class='row-edit'
                                ),
                           SPAN(
                                SPAN('Delete', _title='Cannot delete default tag'),
                                ' | ',
                                _class='row-delete'
                                ),
                           SPAN(
                                A('View', _href=URL('default', 'index', args=['tag','TARGETID']), _title='View this tag', _target='_blank'),
                                _class='row-view'
                                ),
                           _class='row-menu'
                           )
    
    edit_inline = TR(
                     TD(
                        DIV(
                            INPUT(_class='form-control input-sm inline-edit-target-name', _type='text'),
                            _class='inline-edit-col inline-col-left',
                            ),
                        DIV(
                            BUTTON('Cancel', _class='btn btn-default btn-xs inline-edit-cancel'),
                            BUTTON('Update', _class='btn btn-primary btn-xs pull-right inline-edit-update'),
                            _class='inline-edit-btns'
                            ),
                        _colspan='3',
                        ),
                      _class='inline-edit-row'
                      )
    
    return dict(menu=menu,
                page='tags-home',
                table=ttable,
                rowmenu=row_menu,
                rowmenudefault=row_menu_default,
                editinline=edit_inline,
                defaultval='Uncategorized'
                )

'''
TESTING


class DataTablesServer:
    """Ajax data server for Datatables
    """
    def __init__( self, request, columns, index, collection):
        
        self.columns = columns
        self.index = index
        
        # table - element, branch, category, tag
        self.collection = collection
         
        # values specified by the datatable for filtering, sorting, paging
        self.request_values = request
        
        # results from the db
        self.result_data = None
         
        # total in the table after filtering
        self.cardinality_filtered = 0
        
        # total in the table unfiltered
        self.cadinality = 0
        
        self.run_queries()
        
    def run_queries(self):
        """
        """
        #db = current.db
        
        # pages has 'start' and 'length' attributes
        pages = self.paging()
        
        # the term you entered into the datatable search
        filtering = self.filtering()
        
        # the document field you chose to sort
        sorting = self.sorting()
        
        limit = (pages['start'], pages['start'] + pages['length'])
        
        if self.collection == 'element':
            query = (db.xelements_element.category_id==db.xelements_category.id) & \
                    (db.xelements_category.branch_id==db.xelements_branch.id) & \
                    (db.xelements_element.retired==0)
            
            if filtering['or']:
                query &= filtering['or']
            
            self.cardinality_filtered = db(query).count()
            
            rows = db(query).select(limitby=limit, orderby=sorting)
            
        elif self.collection == 'category':
            query = (db.xelements_branch.id==db.xelements_category.branch_id)
            filtered = db(query).select(db.xelements_category.id,
                                        left=db.xelements_element.on(db.xelements_element.category_id==db.xelements_category.id),
                                        groupby=db.xelements_category.id,
                                        )
            self.cardinality_filtered = len(filtered)
            
            if filtering['or']:
                query &= filtering['or']
            
            count = db.xelements_element.id.count()
            rows = db(query).select(db.xelements_branch.id,
                                db.xelements_branch.name,
                                db.xelements_category.id,
                                db.xelements_category.name,
                                db.xelements_category.colour,
                                count,
                                left=db.xelements_element.on(db.xelements_element.category_id==db.xelements_category.id),
                                groupby=db.xelements_category.id,
                                limitby=limit,
                                orderby=sorting,
                                )
            
        elif self.collection == 'branch':
            query = (db.xelements_branch.id>0)
            filtered = db(query).select(db.xelements_branch.id, groupby=db.xelements_branch.id)
            self.cardinality_filtered = len(filtered)
            
            if filtering['or']:
                query &= filtering['or']
                
            count = db.xelements_category.id.count()
            rows = db(query).select(db.xelements_branch.id,
                                    db.xelements_branch.name,
                                    count,
                                    left=db.xelements_category.on(db.xelements_category.branch_id==db.xelements_branch.id),
                                    limitby=limit, orderby=sorting,
                                    groupby=db.xelements_branch.id,
                                    )
            
        elif self.collection == 'tag':
            query = (db.xelements_tag.id>0)
            filtered = db(query).select(db.xelements_tag.id,groupby=db.xelements_tag.id)
            self.cardinality_filtered = len(filtered)
            
            if filtering['or']:
                query &= filtering['or']
            
            count = db.xelements_tagmap.id.count()
            rows = db(query).select(db.xelements_tag.id,
                                    db.xelements_tag.name,
                                    db.xelements_tag.code,
                                    count,
                                    left=db.xelements_tagmap.on(db.xelements_tagmap.tag_id==db.xelements_tag.id),
                                    limitby=limit, orderby=sorting,
                                    groupby=db.xelements_tag.id,
                                    )
            
        else:
            self.result_data = []
            self.cardinality_filtered = 0
            self.cardinality = 0
            return
        
        self.result_data = rows.as_list()
        self.cardinality = len(self.result_data)
        
    def filtering(self):
        """
        """
        #db = current.db
        # build your filter spec
        filter = {'or':None, 'and':None}
        
        if self.request_values.has_key('search[value]'):
            search_val = self.request_values['search[value]']
            if search_val != '':
                
                search_string = '%{0}%'.format(search_val)
                
                # the term put into search is logically concatenated with 'or' between all columns
                or_filter_on_all_columns = None
                
                for i in range( len(self.columns) ):
                    if self.request_values['columns[{0}][searchable]'.format(i)] == 'false':
                        continue
                    table_name, col_name = self.request_values['columns[{0}][name]'.format(i)].split('.')
                    if or_filter_on_all_columns:
                        or_filter_on_all_columns |= db[table_name][col_name].like(search_string)
                    else:
                        or_filter_on_all_columns = db[table_name][col_name].like(search_string)
                        
                filter['or'] = or_filter_on_all_columns
        return filter
        
    def sorting(self):
        """
        """
        #db = current.db
        
        order_dict = {'asc': 1, 'desc': -1}
        ordering = None
        
        if (self.request_values['order[0][column]'] > -1):
            for i in range(len(self.columns)):
                if not self.request_values.has_key('order[{0}][column]'.format(i)):
                    break
                    
                order_col = int(self.request_values['order[{0}][column]'.format(i)])
                order_dir = self.request_values['order[{0}][dir]'.format(i)]
                
                if self.request_values['columns[{0}][orderable]'.format(order_col)] == 'false':
                    continue
                    
                if self.request_values['columns[{0}][name]'.format(order_col)].startswith('COUNT('):
                    col_name = self.request_values['columns[{0}][name]'.format(order_col)]
                    if ordering:
                        if order_dir == 'asc':
                            ordering |= col_name
                        else:
                            ordering |= '~'+col_name
                    else:
                        if order_dir == 'asc':
                            ordering = col_name
                        else:
                            ordering = '~'+col_name
                            
                else:
                    table_name, col_name = self.request_values['columns[{0}][name]'.format(order_col)].split('.')
                    
                    if ordering:
                        if order_dir == 'asc':
                            ordering |= db[table_name][col_name]
                        else:
                            ordering |= ~db[table_name][col_name]
                    else:
                        if order_dir == 'asc':
                            ordering = db[table_name][col_name]
                        else:
                            ordering = ~db[table_name][col_name]
                    
        return ordering
        
    def paging(self):
        """
        """
        pages = {'start':0, 'length':0}
        if (self.request_values['start'] != "" ) and (self.request_values['length'] != -1 ):
            pages['start'] = int(self.request_values['start'])
            pages['length'] = int(self.request_values['length'])
        return pages
        
    def output_result(self):
        """
        DT_RowId
        """
        output = {}
        output['draw'] = int(self.request_values['draw'])
        output['recordsTotal'] = self.cardinality
        output['recordsFiltered'] = self.cardinality_filtered
        
        checkbox = '<input type="checkbox" class="dt-checkbox row-checkbox">'
        
        data = []
        
        for row in self.result_data:
            x = self.index.split('.')
            aaData_row = {'DT_RowId':row[x[0]][x[1]]}
            
            for i in range( len(self.columns) ):
                column = self.columns[i].replace('xelements_','').replace('.','_')
                
                if column == 'checkbox':
                    aaData_row[column] = checkbox
                    continue
                
                if self.columns[i].startswith('COUNT('):
                    column = 'count'
                    t = '_extra'
                    c = self.columns[i]
                else:
                    t, c = self.columns[i].split('.') # xelements_element.name
                val = row[t][c]
                
                if t == 'xelements_element' and c == 'name':
                    val = '{0}X{1}'.format(row[t][c], row[t]['element_code'])
                elif c == 'date_updated':
                    if hasattr(val, 'isoformat'):
                        val = val.strftime('%b %d %Y %I:%M %P')
                
                aaData_row[column] = val
                
            data.append(aaData_row)
            
        output['data'] = data
        
        return output
        
'''