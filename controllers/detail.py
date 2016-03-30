"""

Element detail view

"""
import os
import re
from collections import defaultdict
import gluon.contrib.simplejson
import logging
import logging.config

logging.config.fileConfig('logging.conf')
logger = logging.getLogger("web2py.app.%s" %request.application)
logger.setLevel(logging.DEBUG)
from utils import *

@auth.requires_login()
def index():
    """
    """
    if (len(request.args)) == 0:
        redirect(URL(c='default', f='index'))
    else:
        element_id = request.args[0]
        if element_id == 'undefined' or not element_id:
            redirect(URL(c='default', f='index'))
    
    fav_ids = getFavourites()
    plist_ids = getPlaylist()
    
    # check if current element is a favourite
    try:
        element_id = int(element_id)
        if element_id in fav_ids:
            is_favourite = True
        else:
            is_favourite = False
            
        if element_id in plist_ids:
            in_playlist = True
        else:
            in_playlist = False
    except ValueError:
        is_favourite = False
        in_playlist = False
    
    history_ids = updateHistory(element_id) # update history cookie
    if history_ids:
        history_ids = map(int, history_ids) # int cast
    
    data = getElementData(element_id)
    if not data:
        redirect(URL(c='default', f='error'))
    
    nav_panel = buildNavPanel()
    detail_panel = detailPanel(data, is_favourite, in_playlist)
    video_player = videoPlayer(data)
    
    tags = getTags(element_id)
    tag_panel = tagPanel(tags)
    
    # build address
    addy_sep = SPAN(I(_class='fa fa-lg fa-angle-right'), _class='address-delimiter')
    apath = [addy_sep]
    for addy in data['address']:
        if isinstance(addy, tuple):
            alink = URL('') + '#!/{0}/{1}'.format(addy[2], addy[1])
            apath.extend([A(SPAN(addy[0], _class='address-span'), _href=alink), addy_sep])
        else:
            apath.append(SPAN(addy))
            
    address = SPAN(apath, _id='address')
    #c = clippy()
    
    ptemp = previewTemplate()
    
    return dict(message=element_id,
                navpanel=nav_panel,
                detailpanel=detail_panel,
                videoplayer=video_player,
                tagpanel=tag_panel,
                address=address,
                element_id=element_id,
                is_favourite=is_favourite,
                previewtemplate=ptemp,
                )

def videoPlayer(data):
    """
    """
    file_path = data['filepath']
    if file_path:
        file_path_copy = BUTTON(**{'_class': 'copy-btn fa fa-copy',
                                   '_data-clipboard-text': file_path,
                                   '_title': 'Copy to clipboard'
                                   })
    else:
        file_path = '-'
        file_path_copy = ''
        
    internal_notes = data['internal_notes']
    if not internal_notes:
        internal_notes = '-'
        
    video_option = {'_poster': data['image'],
                    '_width': VIDEO_WIDTH,
                    '_height': VIDEO_HEIGHT,
                    '_loop': True,
                    '_controls': False,
                    '_autoplay': True,
                    }
    
    if os.path.basename(data['movie']) != 'novideo.jpg':
        video_controls = DIV(
                             DIV(
                                 DIV(
                                     SPAN(_id='video-loop', _class='fa fa-retweet video-btn text-muted', _title='Loop'),
                                     SPAN(_id='video-options', _class='fa fa-cog video-btn text-muted', _title='Settings'),
                                     SPAN(_id='video-playpause', _class='fa fa-pause video-btn text-muted'),
                                     _class='video-ctrl-left'
                                     ),
                                 DIV(
                                     INPUT(_id='video-seekbar', _type='range'),
                                     _class='video-ctrl-center',
                                     _style='padding:0;'
                                     ),
                                 DIV(
                                     SPAN('0', _id='video-time', _class='text-muted text-right'),
                                     SPAN(
                                          SPAN(_class='fa fa-square-o fa-stack-2x'),
                                          SPAN(_id='video-expand', _class='fa fa-arrows-alt fa-stack-1x', _title='2x screen'),
                                          SPAN(_id='video-orgsize', _class='fa fa-compress fa-stack-1x hidden', _title='Default screen'),
                                          _class='fa-stack text-muted video-btn pull-right',
                                          _style='margin-left:10px;font-size:0.8em;margin-right:0 !important;',
                                          ),
                                     _class='video-ctrl-right',
                                     ),
                                 _id='video-controls-top',
                                _class='form-horizontal'
                                ),
                             DIV(_id='video-title', _class='text-muted'),
                             DIV(_id='video-caption', _class='text-muted'),
                             DIV(
                                 DIV(
                                     BUTTON('Reset', _id='video-settings-reset', _class='btn btn-primary btn-xs', _style='width:80px;'),
                                     _class='form-group',
                                     _style='margin-bottom:5px;'
                                     ),
                                 DIV(
                                     LABEL('Brightness', _class='control-label col-sm-2'),
                                     DIV(
                                         INPUT(_value=1,
                                               _step=0.05,
                                               _min=0,
                                               _max=10,
                                               _id='video-brightness',
                                               _class='form-control video-setting',
                                               _type='range'
                                               ),
                                         _class='col-sm-10'
                                         ),
                                     _class='form-group'
                                     ),
                                 DIV(
                                     LABEL('Contrast', _class='control-label col-sm-2'),
                                     DIV(
                                         INPUT(_value=1,
                                               _step=0.05,
                                               _min=0,
                                               _max=10,
                                               _id='video-contrast',
                                               _class='form-control video-setting',
                                               _type='range'
                                               ),
                                         _class='col-sm-10'
                                         ),
                                     _class='form-group'
                                     ),
                                 DIV(
                                     LABEL('Saturate', _class='control-label col-sm-2'),
                                     DIV(
                                         INPUT(_value=1,
                                               _step=0.05,
                                               _min=0,
                                               _max=10,
                                               _id='video-saturate',
                                               _class='form-control video-setting',
                                               _type='range'
                                               ),
                                         _class='col-sm-10'
                                         ),
                                     _class='form-group'
                                     ),
                                 _id='video-settings',
                                 _class='collapse form-horizontal'
                                 ),
                             _id='video-controls'
                             )
    else:
        video_controls = DIV('Video Not Found', _id='video-controls', _style='color:#eee;font-size:1.2em;margin-top:5px;')
        
    vid = DIV(
              DIV(
                  VIDEO(
                        SOURCE(_src=data['movie']),
                        **video_option
                        ),
                  DIV(video_controls, _id='video-ctrl-wrapper', _style='width:720px;'),
                  _class='video-wrapper'
                  ),
              DIV(
                  DIV(
                      SPAN('File Path:',
                           file_path_copy,
                           _class='video-detail-label'
                           ),
                      SPAN(file_path,
                           _id='element-filepath',
                           _class='video-detail-info text-overflow'),
                      _class='detail-row'
                      ),
                  DIV(
                      SPAN('Notes:',
                           _class='video-detail-label'
                           ),
                      SPAN(internal_notes,
                           _class='video-detail-info info-full'
                           ),
                      _class='detail-row'
                      ),
                  _class='path-panel'
                  )
              )
    
    return vid

def detailPanel(data, is_favourite=False, in_playlist=False):
    """Return Element detail page layout
    """
    category = data.get('category', 'unknown')
    category_clean = re.sub('\s+|\s*&\s*', '_', category)
    li_id = '{0}-{1}'.format(category_clean, data['id'])
    
    info_fields = ['category', 'alpha', 'colourspace', 'camera', 'source', 'date_created', 'date_updated']
    info_fields_label = {'category': 'Category',
                         'alpha': 'Alpha',
                         'colourspace': 'Colourspace',
                         'camera': 'Camera',
                         'source': 'Source',
                         'date_created': 'Added',
                         'date_updated': 'Updated',
                         }
    
    tech_fields = ['resolution', 'cut_length', 'file_type']
    tech_fields_label = {'resolution': 'Resolution',
                         'cut_length': 'Length',
                         'file_type': 'File Type',
                         }
    
    if is_favourite:
        favourite_btn = I(_id='remove-favourite',
                          _class='fa fa-star header-icon-btn',
                          _title='Remove from Favourite'
                          )
    else:
        favourite_btn = I(_id='add-favourite',
                          _class='fa fa-star-o header-icon-btn',
                          _title='Add to Favourite'
                          )
    
    if in_playlist:
        playlist_btn = I(_id='remove-playlist',
                         _class='fa fa-minus header-icon-btn',
                         _title='Remove from Playlist'
                         )
    else:
        playlist_btn = I(_id='add-playlist',
                         _class='fa fa-plus header-icon-btn',
                         _title='Add to Playlist'
                         )
    
    edit_btn = SPAN()
    if auth.has_membership('admin') or auth.has_membership('elementalist'):
        edit_btn = A('Edit', _href=URL('manage', 'elements', vars={'id':data['id']})+'#edit', _class='btn btn-danger btn-xs edit-link-btn')
        
    header = [DIV(
                  SPAN(data['name'],
                       _class='element-title'
                       ),
                  edit_btn,
                  SPAN(favourite_btn,
                       playlist_btn,
                       _class='pull-right detail-btns'
                       ),
                  **{'_class': 'element-header',
                     '_data-lid': li_id,
                     '_data-thumb': data['image'],
                     '_data-colour': data['colour'],
                     }
                  )]
    
    info_rows = []
    for info in info_fields:
        label = info_fields_label[info] + ':'
        val = data[info]
        if info in ['alpha', 'stereo', 'hdpreview_required']:
            val = 'True' if data[info] == 1 else 'False'
            
        info_rows.append(DIV(
                             SPAN(label,
                                  _class='detail-label'
                                  ),
                             SPAN(val,
                                  _class='detail-info'),
                             _class='detail-row'
                             )
                         )
        
    res = data['resolution'] if data['resolution'] else 'unknown'
    tech_rows = [DIV(
                      SPAN('Resolution',
                           _class='detail-tech-label'
                           ),
                      SPAN('Length',
                           _class='detail-tech-label'
                           ),
                      SPAN('Stereo',
                           _class='detail-tech-label'
                           ),
                      _class='detail-tech-header'
                      ),
                  DIV(
                      SPAN(res,
                           _class='detail-tech-info'
                           ),
                      SPAN(data.get('cut_length', 0),
                           _class='detail-tech-info middle'
                           ),
                      SPAN('Yes' if data['stereo'] == 1 else 'No',
                           _class='detail-tech-info'
                           ),
                      _class='detail-tech-row'
                      )]
    
    detail_rows = header + info_rows + tech_rows
    detailpanel = DIV(*detail_rows, _class='element-details')
    
    return detailpanel

def tagPanel(tags):
    """
    """
    if not tags:
        return DIV(H4(I(_class='fa fa-tags'), ' Tags'), _class='tagpan text-muted')
    
    tagitems = []
    for tag in tags:
        t = SPAN(
                 A(tag['name'],
                   _href=URL('') + '#!/tag/{0}'.format(tag['id']),
                   ),
                 _class='label label-primary tag'
                 )
        tagitems.append(t)
    
    tagpanel = DIV(
                   H4(
                      I(_class='fa fa-tags'),
                      ' Tags'
                      ),
                   *tagitems,
                   _class='tagpan text-muted'
                   )
    return tagpanel

def getElementData(element_id):
    """
    """
    if (isinstance(element_id, int)):
        rows = db((db.xelements_element.id==int(element_id)) & \
                  (db.xelements_element.category_id==db.xelements_category.id) & \
                  (db.xelements_category.branch_id==db.xelements_branch.id)).select()
    else:
        rows = []
        logger.error('Need element id (int) to retrieve data')
    
    fav_count = countFavourites()
    data = prepElements(rows, request.folder, fav_count)
    
    if data:
        return data[0]
    return {}

def getElementDataJSON(element_id):
    """
    """
    return gluon.contrib.simplejson.dumps(getElementData(element_id))

def clippy():
    """Return copy to clipboard flash button
    """
    colour = '#ffffff'
    name = 'Copy'
    
    btn = OBJECT(
                 PARAM(_name='movie', _value=URL('static', 'clippy.swf')),
                 PARAM(_name='allowScriptAccess', _value=URL('static', 'clippy.swf')),
                 PARAM(_name='quality', _value='high'),
                 PARAM(_name='scale', _value='noscale'),
                 PARAM(_name='bgcolor', _value='{0}'.format(colour)),
                 PARAM(_name='FlashVars', _value='text={0}'.format(name)),
                 EMBED(
                       _src=URL('static', 'clippy.swf'),
                       _width='110',
                       _height='14',
                       _name='clippy',
                       _quality='high',
                       _allowScriptAccess='always',
                       _type='application/x-schockwave-flash',
                       _pluginspage='http://www.macromedia.com/go/getflashplayer',
                       _bgcolor='{0}'.format(colour),
                       _FlashVars='text={0}'.format(name),
                       ),
                 _class='clippy',
                 _classid='clsid:clsid:d27cdb6e-ae6d-11cf-96b8-444553540000',
                 _width='110',
                 _height='14',
                 )
    return btn
