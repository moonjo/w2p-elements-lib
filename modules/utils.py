
import os
import re
import time
from datetime import datetime
from collections import defaultdict
from gluon.html import *
from gluon import current

WEBSOCKET_IP = '192.168.1.1:8080'
WEBSOCKET_KEY = 'dkfoAWO1l'
WEBSOCKET_GROUP = 'xelements'

MSGLIMIT = 10
ENTITY_NAME = 15
ENTITY_FULLNAME = 28

VIDEO_WIDTH = 360
VIDEO_HEIGHT = 203
HISTORY_LENGTH = 10
HISTORY_EXPIRE = 30 * (24 * 3600)

RESOLUTION_X = [1,480,800,1024,1280,1600,1920,2048,4096,9999]

def countFavourites():
    """Count favourited Elements
    """
    db = current.db
    
    fav_count = defaultdict(int)
    for row in db(db.xelements_playlist.favourite==1).select(db.xelements_playlist.element_ids):
        eids = map(int, filter(lambda x:x, row.element_ids.split(',')))
        for eid in eids:
            fav_count[eid] += 1
    return fav_count

def prepElements(dbrows, request_folder, favs={}):
    """Preapre element data
    """
    THUMB_DIR = '{0}static/archive/elements/thumbs/'.format(request_folder)
    MOVIE_DIR = '{0}static/archive/elements/movies/'.format(request_folder)
    
    def getThumbnail(filename):
        if filename:
            i = os.path.join(THUMB_DIR, row.xelements_element.thumbnail)
            if os.path.isfile(i):
                return URL('static', os.path.join('archive/elements/thumbs', filename))
        return URL('static', 'images/nothumb.jpg')
    
    def getVideo(filename):
        if filename:
            m = os.path.join(MOVIE_DIR, row.xelements_element.videofile)
            if os.path.isfile(m):
                return URL('static', os.path.join('archive/elements/movies', filename))
        return URL('static', 'images/novideo.jpg')
    
    db = current.db
    
    elements = []
    for row in dbrows:
        element_name = '{0}X{1}'.format(row.xelements_element.name, row.xelements_element.element_code)
        image_filename = element_name
        movie_filename = element_name
        addy = [(row.xelements_branch.name, row.xelements_branch.id, 'branch'), (row.xelements_category.name, row.xelements_category.id, 'category'), element_name]
        
        # tag search
        tags = []
        tagrows = db((db.xelements_tagmap.element_id==row.xelements_element.id) & \
                     (db.xelements_tag.id==db.xelements_tagmap.tag_id)).select()
        for tagrow in tagrows:
            #tags.append((tagrow.xelements_tag.name, tagrow.xelements_tag.id))
            #tags.append(tagrow.xelements_tag.name)
            tags.append(tagrow.xelements_tag.id)
        
        isrc = getThumbnail(row.xelements_element.thumbnail)
        msrc = getVideo(row.xelements_element.videofile)
        
        num_favourited = favs.get(row.xelements_element.id, 0)
        
        element = {'id': row.xelements_element.id,
                   'name': element_name,
                   'internal_notes': row.xelements_element.internal_notes,
                   'cut_length': row.xelements_element.cut_length,
                   'stereo': row.xelements_element.stereo,
                   'hdpreview_required': row.xelements_element.hdpreview_required,
                   'resolution': row.xelements_element.resolution,
                   'filepath': row.xelements_element.file_path,
                   'qt_path': row.xelements_element.qt_path,
                   'mostusedin': row.xelements_element.mostusedin,
                   'source': row.xelements_element.source,
                   'branch_id': row.xelements_branch.id,
                   'branch': row.xelements_branch.name,
                   'category_id': row.xelements_element.category_id,
                   'category': row.xelements_category.name,
                   'image': isrc,
                   'movie': msrc,
                   'colour': row.xelements_category.colour,
                   'alpha': row.xelements_element.alpha,
                   'camera': row.xelements_element.camera,
                   'colourspace': row.xelements_element.colourspace,
                   'date_updated': row.xelements_element.date_updated,
                   'date_created': row.xelements_element.date_created,
                   'tag_list': tags,
                   'address': addy,
                   'favourited': num_favourited,
                   'file_type': '',#'file_type': row.xelements_filetype.name,
                   'status': '',
                   }
        elements.append(element)
    return elements

def resolutionClass(res):
    w,_ = map(int, res.lower().split('x'))
    resx = [1,320,480,640,800,1024,1280,1600,1920,2048,9999]
    #resx = RESOLUTION_X
    
    a = resx[0]
    for x in resx:
        if w >= x:
            a = x
    return a
    
def griddle(elements, mode='main', gid='grid-ul'):
    """Return UL grid
    """
    lis = []
    
    if mode == 'main':
        ul_class = 'grid-ul'
        li_class = 'grid-li'
        thumb_class = 'grid-thumbnail'
    else:
        ul_class = 'mini-grid-ul'
        li_class = 'mini-grid-li'
        thumb_class = 'panel-thumbnail'
    
    for element in elements:
        eid = element.get('id')
        name = element.get('name')
        category = element.get('category', 'unknown')
        clip = element.get('video_lores')
        cutlength = element.get('cut_length')
        filepath = element.get('filepath', '')
        alpha = element.get('alpha', '')
        desc = element.get('description', '')
        favourited = element.get('favourited', 0)
        source = element.get('source', '')
        
        if element.get('resolution'):
            resolution = 'resolution-{0}'.format(element.get('resolution'))
            resclass = 'resolution-{0}'.format(resolutionClass(element.get('resolution')))
        else:
            resolution = 'resolution-unknown'
            resclass = resolution
            
        colourcode = '#{0}'.format(element.get('colour'))
        if 3 < contrast_ratio("#333", colourcode):
            fontcolour = '#333'
        else:
            fontcolour = '#ddd'
            
        image_src = element['image']
        
        #tagvals = element['tag_list']
        tagvals = ['tag-{0}'.format(t) for t in element['tag_list']]
        
        fc = [resclass] + tagvals
        filter_class = ' '.join(fc)
        
        #movie_src = URL('static', 'test.mov')
        #movie_src = URL('static', 'archive/strain/movies/106_051_035_comp_v004_h264.mov')
        #movie_src = URL('static', 'archive/elements/movies/{0}'.format(element.get('movie','nomovie.mp4'))
        movie_src = element.get('movie','nomovie.mp4')
        
        favourite_btn = I(_class='favourite-add fa fa-star-o header-icon-btn',
                          _title='Add to Favourite'
                          )
        playlist_btn = I(_class='playlist-add fa fa-plus header-icon-btn',
                         _title='Add to Playlist'
                         )
        
        if mode == 'playlist':
            playlist_btn = I(_class='playlist-remove fa fa-minus header-icon-btn',
                             _title='Remove from Playlist'
                             )
        if mode == 'faves':
            favourite_btn = I(_class='favourite-remove fa fa-star header-icon-btn',
                              _title='Remove from Favourite'
                              )
            playlist_btn = SPAN()
            
        category_clean = re.sub('\s+|\s*&\s*', '_', category)
        li_id = '{0}-{1}'.format(category_clean, eid)
        
        lis.append(LI(
                      A(
                        DIV(IMG(**{'_class': 'lazy',
                                   '_data-original': image_src,
                                   }),
                            DIV(_class='preview-holder'),
                            **{'_class': thumb_class,
                               '_data-video': movie_src,
                               '_data-resolution': resolution,
                               '_data-length': cutlength,
                               '_data-desc': desc,
                               }
                            ),
                        DIV(
                            SPAN(name, _class='grid-name', _title=name, _style='color:{0}'.format(fontcolour)),
                            SPAN(favourite_btn,
                                 playlist_btn,
                                 **{'_class': 'grid-btns pull-right',
                                    '_data-elementid': eid,
                                    }
                                 ),
                            _class='grid-label'
                            ),
                        _href=URL(c='detail', f='index', args=[eid]),
                        ),
                      INPUT(_class='hidden element-file-path', _value=filepath),
                      **{'_id': li_id,
                         '_class': '{0} {1}'.format(li_class, filter_class),
                         '_style': 'background-color:{0}'.format(colourcode),
                         '_data-elementid': eid,
                         '_data-alpha': alpha,
                         '_data-source': source,
                         '_data-favourited': favourited,
                         }
                      )
                   )
    return UL(lis, _id=gid, _class=ul_class)

def buildNavPanel(element_id=None):
    """
    """
    is_favourite = False
    in_playlist = False
    
    plists = getPlaylists()
    
    plist_ids = []
    fav_ids = []
    for plist in plists:
        if plist['element_ids']:
            eids = csvToList(plist['element_ids'])
            if plist['favourite'] == 1:
                fav_ids = eids
            else:
                plist_ids.extend(eids)
                
    # check if current element is a favourite
    if element_id:
        if int(element_id) in fav_ids:
            is_favourite = True
            
        if int(element_id) in plist_ids:
            in_playlist = True
            
        # update history cookie
    history_ids = updateHistory(element_id)
    if history_ids:
        # int cast
        try:
            history_ids = map(int, history_ids)
        except:
            history_ids = []
            
    plist_pane = plistPane(plists, fav_ids, plist_ids)
    hist_pane = historyPane(history_ids)
    nav_panel = navPanel(plist_pane, hist_pane)
    return nav_panel

def plistPane(playlists=[], fav_ids=[], plist_ids=[]):
    """Playlist pane
    """
    db = current.db
    request = current.request
    
    # build playlist tabs
    playlist_opts = []
    favlist_id = ''
    
    if not playlists:
        tabcontent = DIV(
                         DIV(UL(_class='mini-grid-ul'),
                             _id='tab-playlist-faves',
                             _class='tab-pane active'
                             ),
                         _id='playlist-tabs',
                         _class='tab-content'
                         )
    else:
        # favourites
        fav_rows = db((db.xelements_element.id.belongs(fav_ids)) & \
                      (db.xelements_element.category_id==db.xelements_category.id) & \
                      (db.xelements_category.branch_id==db.xelements_branch.id)).select()
        
        fav_elements = sorted(prepElements(fav_rows, request.folder), key=lambda k:fav_ids.index(k['id']))
        fav_ul = griddle(fav_elements, mode='faves', gid='')
        tabs = [DIV(fav_ul, _id='tab-playlist-faves', _class='tab-pane active')]
        
        # rest of playlists
        for playlist in playlists:
            if playlist['favourite'] == 1:
                favlist_id = playlist['id']
                continue
            
            p_ids = csvToList(playlist['element_ids'])
            p_rows = db((db.xelements_element.id.belongs(p_ids)) & \
                        (db.xelements_element.category_id==db.xelements_category.id) & \
                        (db.xelements_category.branch_id==db.xelements_branch.id)).select()
            
            p_elements = sorted(prepElements(p_rows, request.folder), key=lambda k:p_ids.index(k['id']))
            p_tab_id = 'playlist-{0}'.format(playlist['id'])
            p_ul = griddle(p_elements, mode='playlist', gid='')
            
            tabs.append(DIV(p_ul, _id='tab-{0}'.format(p_tab_id), _class='tab-pane'))
            playlist_opts.append(OPTION(playlist['name'], **{'_data-target':'#tab-{0}'.format(p_tab_id),'_data-playlistid':playlist['id'],'_data-toggle':'tab'}))
            
        tabcontent = DIV(tabs, _id='playlist-tabs', _class='tab-content')
    
    playlist_opts.insert(0, OPTION('Faves', **{'_data-target':'#tab-playlist-faves','_data-playlistid':favlist_id,'_data-toggle':'tab', '_selected':True}))
    
    playlist_base_btns = DIV(
                            SELECT(playlist_opts,
                                   _id='playlist-select',
                                   _class='form-control',
                                   _style='border-top-left-radius:0;'
                                   ),
                            SPAN(
                                 I(_class='fa fa-trash'),
                                 _id='playlist-delete',
                                 _class='input-group-addon playlist-ctrl-btn',
                                 _style='border-left:0;',
                                 _title='Delete Playlist'
                                 ),
                             SPAN(
                                 I(_class='fa fa-share-alt'),
                                 _id='playlist-share',
                                 _class='input-group-addon playlist-ctrl-btn',
                                 _style='border-left:0;',
                                 _title='Share Playlist'
                                 ),
                            SPAN(
                                 I(_class='fa fa-copy'),
                                 _id='playlist-copy',
                                 _class='input-group-addon playlist-ctrl-btn',
                                 _style='border-left:0;',
                                 _title='Copy Filepaths'
                                 ),
                            SPAN(
                                 I(_class='fa fa-plus'),
                                 _id='playlist-new',
                                 _class='input-group-addon playlist-ctrl-btn',
                                 _title='New Playlist'
                                 ),
                            _id='playlist-base-ctrl',
                            _class='input-group'
                            )
    
    playlist_create_btns = DIV(
                               INPUT(_id='playlist-newname',
                                     _class='form-control',
                                     _placeholder='New Playlist..'
                                     ),
                               SPAN(
                                    I(_class='fa fa-check text-success'),
                                    _id='playlist-create',
                                    _class='input-group-addon playlist-ctrl-btn',
                                    _style='border-left:0;'
                                    ),
                               SPAN(
                                    I(_class='fa fa-times text-danger'),
                                    _id='playlist-cancel',
                                    _class='input-group-addon playlist-ctrl-btn',
                                    ),
                               _id='playlist-create-ctrl',
                               _class='input-group hidden'
                               )
    
    pane = DIV(
               DIV(
                   playlist_base_btns,
                   playlist_create_btns,
                   ),
               DIV(tabcontent, _id='div-plist', _class='ul-pane'),
               _class='playlist-panel'
               )
    
    return pane

def historyPane(histids=[]):
    """
    """
    db = current.db
    request = current.request
    
    ul = UL()
    if not histids:
        if request.cookies.has_key(request.application):
            val = request.cookies[request.application].value
            if val:
                histids = csvToList(val)
    if histids:
        rows = db((db.xelements_element.id.belongs(histids)) & \
                  (db.xelements_element.category_id==db.xelements_category.id) & \
                  (db.xelements_category.branch_id==db.xelements_branch.id)).select()
                  #(db.xelements_element.file_type_id==db.xelements_filetype.id)).select()
        
        # to preserve viewed order
        orderedrows = []
        for histid in histids:
            row = rows.find(lambda row: row.xelements_element.id==histid)
            if row:
                orderedrows.append(row[0])
        
        elements = prepElements(orderedrows, request.folder)
        ul = griddle(elements, mode='detail', gid='hist-ul')
    return DIV(ul, _id='div-hist', _class='ul-pane')

def navPanel(pbpane=None, histpane=None):
    """Builds artist control panel
    
    :param tasks: dictionary of Task entities
    :returns: DIV object
    
    >>> isinstance(ctrlPanel({}, 'seank', '', True), gluon.html.DIV)
    True
    """
    if pbpane:
        playlist_pane = pbpane
    else:
        playlist_pane = DIV('playlist')
        
    if histpane:
        history_pane = histpane
    else:
        history_pane = DIV('history')
        
    ctrl_buttons = [
                    LI(
                       A(
                         I(_class='fa fa-list-ol'),
                         SPAN('Playlist', _class='side-navbar-label'),
                         **{'_id':'playlist-tab-btn',
                            '_class':'panel-menu',
                            '_href':'#',
                            '_data-target': '#tab-playlist',
                            }
                         ),
                       _id='playlist-tab-btn-li',
                       _class='li-btn active',
                       _title='Playlist',
                       ),
                    LI(
                       A(
                         I(_class='fa fa-history'),
                         SPAN('History', _class='side-navbar-label'),
                         **{'_id':'history-tab-btn',
                            '_class':'panel-menu',
                            '_href':'#',
                            '_data-target': '#tab-history',
                            }
                         ),
                       _id='history-tab-btn-li',
                       _class='li-btn',
                       _title='History',
                       ),
                    ]
    
    inner_panels = DIV(
                       DIV(
                           playlist_pane,
                           _id='tab-playlist',
                           _class='tab-panel active'
                           ),
                       DIV(history_pane,
                           _id='tab-history',
                           _class='tab-panel'
                           ),
                       _id='tab-carousel'
                       )
    
    ctrl_panel = DIV(
                     BUTTON(
                            SPAN('Toggle Menu', _class='sr-only'),
                            I(_class='fa fa-bars'),
                            **{'_class': 'side-navbar-toggle collapsed',
                               '_type': 'button',
                               '_data-toggle': 'collapse',
                               '_data-target': '#user-nav-bar'
                               }
                            ),
                     DIV(
                         SPAN('Playlist',
                           _id='panel-title',
                           _class='side-navbar-brand',
                           ),
                         _class='side-navbar-header'
                         ),
                     DIV(
                         UL(*ctrl_buttons,
                            _id='panel-btns',
                            _class='nav side-navbar-nav side-navbar-right'
                            ),
                         _id='user-nav-bar',
                         _class='side-navbar-collapse collapse'
                         ),
                     _class='container-nav'
                     )
    
    
    nav_panel = DIV(
                    DIV(ctrl_panel, _class='navbar navbar-default', _style="margin-bottom:0;"),
                    inner_panels,
                    )
    
    return nav_panel

def previewTemplate():
    """Preview video template
    """
    video_type = 'video/mp4'
    pdiv = DIV(
               SPAN(
                    VIDEO(
                          SOURCE(_src='{1}', _type=video_type),
                          _class='movie-player',
                          _autoplay=False,
                          _loop=True,
                          _width=360,
                          _height=203,
                          _poster='{0}'
                          ),
                    _class='preview-span'
                    ),
               DIV(
                   SPAN('{2}', _class=''),
                   SPAN('{3}', _class='pull-right'),
                   SPAN('{4}', _class='pull-right midspan'),
                   _class='preview-title'
                   ),
               _id='preview-popup',
               _class='preview-div',
               )
    return pdiv

def getTags(element_id=None):
    """
    """
    db = current.db
    query = (db.xelements_tag.id==db.xelements_tagmap.tag_id)
    if element_id:
        query &= (db.xelements_tagmap.element_id==element_id)
    return db(query).select(db.xelements_tag.ALL)

def updateHistory(elementid=None):
    """Keep track of visited elements
    """
    request = current.request
    response = current.response
    
    if request.cookies.has_key(request.application):
        oldval = request.cookies[request.application].value
    else:
        oldval = ''
    history_ids = filter(lambda x:x, oldval.split(','))
    
    if elementid:
        elementid = str(elementid)
        if elementid in history_ids:
            history_ids.remove(elementid)
        history_ids.insert(0, elementid)
        
        while len(history_ids) > HISTORY_LENGTH:
            history_ids.pop()
        
        newval = ','.join(history_ids)
        
        response.cookies[request.application] = newval
        response.cookies[request.application]['expires'] = HISTORY_EXPIRE
        response.cookies[request.application]['path'] = '/'
    return history_ids

def getFavourites():
    """
    @return: list of int
    """
    auth = current.auth
    db = current.db
    '''
    rows = db(db.xelements_userpref.user_id==auth.user.id).select(db.xelements_userpref.favourites)
    if rows and rows[0].favourites:
        return map(int, rows[0].favourites.strip().split(','))
    return []
    '''
    rows = db((db.xelements_playlist.user_id==auth.user.id) & \
              (db.xelements_playlist.favourite==1)).select(db.xelements_playlist.ALL)
    if rows and rows[0].element_ids:
        return csvToList(rows[0].element_ids)
    return []
    
def getPlaylists():
    """
    @return: list of int
    """
    auth = current.auth
    db = current.db
    '''
    rows = db(db.xelements_userpref.user_id==auth.user.id).select(db.xelements_userpref.playlist)
    if rows and rows[0].playlist:
        return map(int, rows[0].playlist.strip().split(','))
    return []
    '''
    playlists = []
    rows = db(db.xelements_playlist.user_id==auth.user.id).select()
    for row in rows:
        playlists.append(row.as_dict())
    return playlists
    
def getPlaylist():
    """
    @return: list of int
    """
    auth = current.auth
    db = current.db
    '''
    rows = db(db.xelements_userpref.user_id==auth.user.id).select(db.xelements_userpref.playlist)
    if rows and rows[0].playlist:
        return map(int, rows[0].playlist.strip().split(','))
    return []
    '''
    rows = db((db.xelements_playlist.user_id==auth.user.id) & \
              (db.xelements_playlist.favourite==0)).select(db.xelements_playlist.ALL)
    if rows and rows[0].element_ids:
        return csvToList(rows[0].element_ids)
    return []
    
def fileCheck(filepath, wild=False):
    """Returns xview path to thumbnail image
    
    :param code: Shot/Asset code
    :param project_code: Project code
    :param wild: filename wildcard check
    :returns: xview file path
    
    >>> f = _xvImageFileCheck('ABC006', 'testing')
    """
    request = current.request
    
    img_file = '%sstatic/archive/elements/thumbs/%s.' %(request.folder, filepath)
    for ext in ['jpg', 'JPG', 'png', 'PNG']:
        if os.path.isfile(img_file + ext):
            return URL('static', 'archive/elements/thumbs/%s.%s' %(filepath, ext))
    return None

def codeformat(code):
    """Remove whitespaces and special chars (&)
    """
    a = re.compile('\&')
    s = re.compile('\s+')
    return s.sub('_', a.sub('n', code)).lower()

def csvToList(val):
    """Convert int csv string to list of ints
    """
    if not val:
        return []
    tmp = val.strip().strip(',').split(',')
    return map(int, tmp)

def print_timing(func):
    request = current.request
    
    def wrapper(*arg, **kwargs):
        t1 = time.time()
        res = func(*arg, **kwargs)
        t2 = time.time()
        border = '==='
        output = '[%s] %s  %s took %0.3f sec  %s' %(request.application.upper(), border, func.func_name, (t2-t1)*1.0, border)
        logger.debug(output)
        return res
    return wrapper

def textToHtml(txt):
    return '<pre>%s</pre>' %txt

def pretty_date(time=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """
    now = datetime.now()
    if type(time) is int:
        datetimeobj = datetime.fromtimestamp(time)
        diff = now - datetimeobj
    elif isinstance(time, datetime):
        diff = now - time
        datetimeobj = time
    elif not time:
        diff = now - now
        datetimeobj = now
        
    second_diff = diff.seconds
    day_diff = diff.days
    
    if day_diff < 0:
        return ''
    
    if day_diff == 0:
        if second_diff < 60:
            return "Just now"
        if second_diff < 120:
            return "A minute ago"
        if second_diff < 3600:
            return "%s minutes ago" % str(second_diff / 60)
        if second_diff < 7200:
            return "An hour ago"
        if second_diff < 86400:
            return "%s hours ago" % str(second_diff / 3600)
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return "%s days ago" % str(day_diff)
    if day_diff < 31:
        w = day_diff / 7
        s = 'weeks' if w > 1 else 'week'
        return "%s %s ago" %(str(w), s)
    if day_diff < 365:
        m = day_diff / 30
        s = 'months' if m > 1 else 'month'
        return "%s %s ago" %(str(m), s)
    #return datetimeobj.strftime('%b %d %Y %H:%M:%S')
    y = day_diff / 365
    s = 'years' if y > 1 else 'year'
    return "%s %s ago" %(str(y), s)

def newlineFixStr(s, empty=SPAN('').xml(), rchar=BR().xml()):
    # <br />
    if not s or s == '':
        return empty
    return re.sub(r'\r\n|\r|\n', rchar, s)

def mailman(to, subject, body):
    """ Email
    """
    auth = current.auth
    
    mail = auth.settings.mailer
    mail.settings.server = 'mail.mrxfx.com'
    mail.settings.sender = 'noreply@mrxfx.com'
    mail.settings.login = 'seank:aMjpnXGh'
    
    mail.send(to=to, subject=subject, message=body)

def roundPartial(value, precision=0.01):
    """Round to given precision. Default to one thousandth
    """
    return round(value / precision) * precision

# Contrast ratio functions
def hex_to_rgb(val):
    """Converts hex value to rgb value
    
    :param val: hex value
    :returns: rgb value
    """
    val = val.lstrip('#')
    lv = len(val)
    if lv == 3 and val[0]*lv == val:
        val = val * 2
        lv = len(val)
    return tuple(int(val[i:i+lv/3], 16) for i in range(0, lv, lv/3))

def rgb_to_hex(val):
    """Converts rgb value to hex value
    
    :param val: rgb value
    :returns: hex value
    """
    # val = 3-int-tuple
    v = tuple(map(lambda x: int(x), list(val)))
    return '#%02x%02x%02x' %v

def norm(val):
    """Normalize
    
    :param val: rgb
    :returns: normalized value
    """
    v = val / 255.0
    if v < 0.03928:
        return v / 12.92
    else:
        return ((v + 0.055) / 1.055) ** 2.4

def luminance(rgb):
    """Calculates luminance of rgb
    
    :param rgb: rgb value
    :returns: luminance
    """
    try:
        r, g, b = map(norm, rgb)
    except ValueError:
        r, g, b, a = map(norm, rgb)
        
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def contrast_ratio(fg, bg, mode='hex'):
    """Calculate contrast between 2 colour values
    
    :param fg: foreground colour - font
    :param bg: background colour
    :param mode: hex or rgb
    :returns: contrast ratio
    """
    if mode == 'hex':
        # convert hex to rgb
        c1 = hex_to_rgb(fg)
        c2 = hex_to_rgb(bg)
    else:
        c1 = fg
        c2 = bg
    l1 = luminance(c1)
    l2 = luminance(c2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    cratio = roundPartial((lighter + 0.05) / (darker + 0.05))
    return cratio

