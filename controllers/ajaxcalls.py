from utils import *
import gluon.contrib.simplejson
import re
#from _socketmodule import AF_APPLETALK

import logging
import logging.config
logging.config.fileConfig('logging.conf')
logger = logging.getLogger("web2py.app.%s" %request.application)
logger.setLevel(logging.DEBUG)

mail = auth.settings.mailer
mail.settings.server = 'mail.com'
mail.settings.sender = 'noreply@mail.com'
mail.settings.login = 'admin:pass'

def getElementNames():
    """Return element names, id for autocomplete
    rain
    rainX
    rainX05
    """
    pat = re.compile('(\w+)X([\d]*)')
    result = []
    val = request.vars.term
    if val:
        m = pat.match(val)
        if m:
            name = m.group(1)
            element_code = m.group(2)
            q = (db.xelements_category.id==db.xelements_element.category_id) & (db.xelements_element.name==name)
            if element_code:
                q &= (db.xelements_element.element_code.contains(element_code))
        else:
            # doesn't contain X joiner
            q = (db.xelements_element.name.contains(val)) & (db.xelements_category.id==db.xelements_element.category_id)
            
        for row in db(q).select(orderby=db.xelements_category.name|db.xelements_element.name):
            name = '{0}X{1}'.format(row.xelements_element.name, row.xelements_element.element_code)
            result.append({'label':name, 'value':row.xelements_element.id, 'category':row.xelements_category.name})
            
    return gluon.contrib.simplejson.dumps(result)

def getUsernames():
    """Return user names, id for autocomplete
    """
    pat = re.compile('(\w+)X([\d]*)')
    result = []
    val = request.vars.term
    if val:
        q = """SELECT a.id,a.first_name,a.last_name,a.username FROM auth_user AS a
        INNER JOIN
        (SELECT username, MAX(id) AS mid FROM auth_user GROUP BY username) AS g
        ON g.username=a.username AND g.mid=a.id
        WHERE a.first_name LIKE '%{0}%' OR a.last_name LIKE '%{0}%' OR a.username LIKE '%{0}%' ORDER BY a.first_name, a.last_name;""".format(val)
        
        rows = db.executesql(q)
        for row in rows:
            name = '{0} {1}'.format(row[1], row[2])
            email = '{0}@mrxfx.com'.format(row[3])
            result.append({'label':name, 'value':email})
            
    return gluon.contrib.simplejson.dumps(result)

def getResolutionUpperLimit(w):
    resx = [1,480,800,1024,1280,1600,1920,2048,4096,9999]
    #resx = RESOLUTION_X
    for x in resx:
        if x > w:
            return x
    return resx[-1]

@auth.requires_login()
def filteredGrid():
    """Return elements
    
    @return: elements grid
    """
    name = request.vars.name
    source = request.vars.source
    tags = map(int, filter(lambda x:x, request.vars.tags.split(',')))
    alpha = request.vars.alpha == '1'
    resolution = filter(lambda x:x, request.vars.resolution.split(','))
    colourspace = filter(lambda x:x, request.vars.colourspace.split(','))
    faves = request.vars.faves == '1'
    
    query = (db.xelements_element.category_id==db.xelements_category.id) & \
            (db.xelements_category.branch_id==db.xelements_branch.id)
    
    if name:
        query &= (db.xelements_element.name.contains(name))
        
    if source:
        query &= (db.xelements_element.source.contains(source))
        
    if tags:
        tagrows = db(db.xelements_tagmap.tag_id.belongs(tags)).select(db.xelements_tagmap.element_id)
        element_ids = tuple([t.element_id for t in tagrows])
        query &= (db.xelements_element.id.belongs(element_ids))
        
    if alpha:
        query &= (db.xelements_element.alpha==1)
        
    if resolution:
        #query &= (db.xelements_element.resolution.belongs(resolution))
        first_res = int(resolution[0])
        upper = getResolutionUpperLimit(first_res)
        rquery = ((db.xelements_element.width>=first_res) & (db.xelements_element.width<upper))
        for x in resolution[1:]:
            upper = getResolutionUpperLimit(int(x))
            rquery |= ((db.xelements_element.width>=x) & (db.xelements_element.width<upper))
        if rquery:
            query &= rquery
            
    if colourspace:
        pass
    
    if faves:
        fav_element_ids = set()
        for row in db(db.xelements_playlist.favourite==1).select(db.xelements_playlist.element_ids):
            fav_element_ids = fav_element_ids.union(set(row.element_ids.split(',')))
            
        if fav_element_ids:
            query &= (db.xelements_element.id.belongs(list(fav_element_ids)))
    
    rows = db(query).select(orderby=db.xelements_element.name|db.xelements_element.element_code)
    
    fav_count = countFavourites()
    data = prepElements(rows, request.folder, fav_count)
    
    result = griddle(data, gid='search-ul')
    
    return result.xml()
    
def createPlaylist():
    """
    """
    d = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    playlist_name = request.vars.playlistname
    element_ids = ','.join(map(lambda x: x.strip(), request.vars.elementids.split(','))).strip(',')
    
    ret = db.xelements_playlist.insert(user_id=auth.user_id,
                                       element_ids=element_ids,
                                       name=playlist_name,
                                       description='',
                                       date_modified=d,
                                       favourite=0,
                                       )
    return gluon.contrib.simplejson.dumps(ret)

def updatePlaylist():
    """
    """
    d = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    element_ids = ','.join(map(lambda x: x.strip(), request.vars.elementids.split(','))).strip(',')
    playlist_id = request.vars.playlistid
    
    if playlist_id == 'faves':
        ret = db.xelements_playlist.update_or_insert((db.xelements_playlist.user_id==auth.user_id) & \
                                                     (db.xelements_playlist.favourite==1),
                                                     user_id=auth.user_id,
                                                     element_ids=element_ids,
                                                     description='',
                                                     date_modified=d,
                                                     favourite=1,
                                                     )
    else:
        ret = db(db.xelements_playlist.id==int(playlist_id)).update(element_ids=element_ids,
                                                                    description='',
                                                                    date_modified=d,
                                                                    favourite=0,
                                                                    )
    return gluon.contrib.simplejson.dumps(ret)

def renamePlaylist():
    playlist_id = request.vars.pid
    newname = request.vars.name
    if playlist_id and newname:
        db(db.xelements_playlist.id==playlist_id).update(name=newname,date_modified=datetime.now())
    return ''

def deletePlaylist():
    """
    """
    d = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    playlist_id = request.vars.playlistid
    
    if playlist_id == 'faves':
        # clear element_ids
        db((db.xelements_playlist.user_id==auth.user_id) & (db.xelements_playlist.favourite==1)).update(element_ids='',date_modified=d)
    else:
        # delete row
        db(db.xelements_playlist.id==int(playlist_id)).delete()
        
    return ''

def addPlaylist():
    """
    """
    element_id = request.vars.elementid
    ret = 0
    # find out if this user has existing favourites
    rows = db(db.xelements_playlist.user_id==auth.user_id).select(db.xelements_playlist.playlist)
    if rows:
        playids = ''
        if rows[0].playlist:
            tmp = rows[0].playlist.split(',')
            if not element_id in tmp:
                playids = rows[0].playlist + ',' + element_id 
        else:
            playids = element_id
        
        playids = playids.strip(',')
        if playids:
            ret = db(db.xelements_playlist.user_id==auth.user_id).update(playlist=playids)
    else:
        playids = element_id.strip(',')
        if playids:
            ret = db.xelements_playlist.insert(user_id=auth.user_id,
                                               favourites='',
                                               playlist=playids)
    if ret:
        # update playidspane
        return plistPane(map(int, playids.split(','))).xml()
        
    return ''

def removePlaylist():
    """
    """
    element_id = request.vars.elementid
    playids = ''
    ret = 0
    # find out if this user has existing favourites
    rows = db(db.xelements_playlist.user_id==auth.user_id).select(db.xelements_playlist.playlist)
    if rows:
        if rows[0].playlist:
            tmp = rows[0].playlist.split(',')
            if element_id in tmp:
                tmp.remove(element_id)
                playids = ','.join(tmp) 
        ret = db(db.xelements_playlist.user_id==auth.user_id).update(playlist=playids)
    else:
        ret = db.xelements_playlist.insert(user_id=auth.user_id,
                                           favourites='',
                                           playlist='')
    if ret:
        # update playidspane
        if playids:
            return plistPane(map(int, playids.split(','))).xml()
        else:
            return plistPane().xml()
        
    return ''

def addFavourite():
    """Create or update Favourite Playlist
    """
    p_name = request.vars.name
    desc = request.vars.desc
    element_id = request.vars.elementid
    d = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ret = 0
    # find out if this user has existing favourites
    rows = db((db.xelements_playlist.user_id==auth.user_id) & \
              (db.xelements_playlist.favourite==1)).select(db.xelements_playlist.ALL)
    if rows:
        favs = ''
        if rows[0].favourites:
            tmp = rows[0].favourites.split(',')
            if not element_id in tmp:
                favs = rows[0].favourites + ',' + element_id 
        else:
            favs = element_id
            
        if favs:
            ret = db(db.xelements_playlist.user_id==auth.user_id).update(name=p_name,
                                                                         description=desc,
                                                                         element_ids=favs,
                                                                         date_modified=d
                                                                         )
    else:
        favs = element_id
        ret = db.xelements_playlist.insert(user_id=auth.user_id,
                                           name=p_name,
                                           description=desc,
                                           element_ids=favs,
                                           date_modified=d,
                                           favourite=1
                                           )
    
    if ret:
        # update favspane
        return favsPane(map(int, favs.split(','))).xml()
    return ''

def removeFavourite():
    """
    """
    element_id = request.vars.elementid
    d = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    favs = ''
    ret = 0
    # find out if this user has existing favourites
    rows = db(db.xelements_playlist.user_id==auth.user_id).select(db.xelements_playlist.favourites)
    if rows:
        if rows[0].favourites:
            tmp = rows[0].favourites.split(',')
            if element_id in tmp:
                tmp.remove(element_id)
                favs = ','.join(tmp) 
        ret = db(db.xelements_playlist.user_id==auth.user_id).update(favourites=favs)
    else:
        ret = db.xelements_playlist.insert(user_id=auth.user_id,
                                           favourites='',
                                           playlist='')
    if ret:
        # update favspane
        if favs:
            return favsPane(map(int, favs.split(','))).xml()
        else:
            return favsPane().xml()
        
    return ''

def getComments():
    """Return comments & replies for the element
    """
    def li_comment(comment, reply=False, replies=[]):
        if reply:
            cls = 'app-reply'
            reply_icon = ''
            reply_ul = ''
            reply_input = ''
        else:
            cls = 'app-comment'
            reply_icon = SPAN(_class='fa fa-reply reply-icon', _title='Reply')
            reply_ul = UL(replies, _class='ul-reply')
            reply_input = DIV(
                              TEXTAREA(_class='form-control comment-input',
                                       _placeholder='reply to above comment',
                                       _rows=1
                                       ),
                              BUTTON('Reply',
                                     **{'_class':'btn btn-primary btn-sm reply-submit',
                                        '_data-comment':comment.id,
                                        '_data-application':comment.element_id,
                                        }
                                     ),
                              _class='reply-input collapse',
                              )
        
        content = XML(comment.content.replace('\n', '<br>'))
        
        return LI(
                  DIV(SPAN(comment.username, _class='text-muted'),
                      SPAN(
                           SMALL(comment.date_added.strftime('%b %d %Y %I:%M %p'),
                                 _class='text-italic'
                                 ),
                           _class='text-muted date-display'
                           ),
                      ),
                  P(content, reply_icon, _class='comment-body'),
                  reply_input,
                  reply_ul,
                  _class=cls,
                  _id='comment-%d' %comment.id
                  )
        
    def get_replies(pid, replies):
        filtered = filter(lambda x:x.parent_id==pid, replies)
        result = []
        for r in filtered:
            li = li_comment(r, reply=True)
            result.append(li)
        return result
    
    elementid = int(request.vars.element_id)
    
    comments = db((db.xelements_comment.element_id==elementid) & \
                  (db.xelements_comment.parent_id==None)).select(orderby=~db.xelements_comment.date_added)
    replies = db((db.xelements_comment.element_id==elementid) & \
                 (db.xelements_comment.parent_id!=None)).select(orderby=db.xelements_comment.date_added)
    
    result = ''
    for comment in comments:
        creplies = get_replies(comment.id, replies)
        li = li_comment(comment, replies=creplies)
        result += li.xml()
        
    return result

def addComment():
    """Create comment for the element
    """
    try:
        elementid = int(request.vars.element_id)
    except ValueError:
        logger.error('Error creating Comment: invalid element ID')
        return response.json(0)
    
    body = request.vars.content
    elementname = request.vars.element_name
    
    uname = currentUser()
    d = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ret = db.xelements_comment.insert(element_id=elementid,
                                      username=uname,
                                      content=body,
                                      date_added=d
                                      )
    #logger.info("Add Comment - Application (%d) by '%s'" %(elementid, uname))
    # email notification
    commentEmail(elementid, elementname, uname, body)
    
    return response.json(ret)

def addReply():
    """Create reply for comment
    """
    try:
        elementid = int(request.vars.element_id)
    except ValueError:
        logger.error('Error creating Reply: invalid element ID')
        return response.json(0)
    try:
        commentid = int(request.vars.comment_id)
    except ValueError:
        logger.error('Error creating Reply: invalid comment ID')
        return response.json(0)
    
    body = request.vars.content
    elementname = request.vars.element_name
    
    uname = currentUser()
    d = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ret = db.xelements_comment.insert(element_id=elementid,
                                      username=uname,
                                      content=body,
                                      date_added=d,
                                      parent_id=commentid
                                      )
    #logger.info("Add Reply - Application (%d), Comment (%d) by '%s'" %(elementid, commentid, uname))
    commentEmail(elementid, elementname, uname, body, True)
    
    return response.json(ret)

def elementsTable():
    """Return elements JSON for table
    """
    return gluon.contrib.simplejson.dumps()

def currentUser():
    if auth.user.first_name and auth.user.last_name:
        return '{0} {1}'.format(auth.user.first_name, auth.user.last_name)
    return auth.user.username

def commentEmail(element_id, element_name, poster, body, reply=False):
    """Comments notificaiton
    * Recipient fixed to Andy for now
    """
    link = URL('detail','index', args=[element_id], scheme=True, host=True)
    to = 'andy@mrxfx.com'
    content = body
    
    if reply:
        subject = '[xElements] {0} replied by {1}'.format(element_name, poster)
    else:
        subject = '[xElements] {0} commented by {1}'.format(element_name, poster)
        
    if to and content:
        message = '<html><p><a href="{0}">{1}</a><p><p>{2}<p><p>{3}</p></html>'.format(link, element_name, content, poster)
        
        mailman(to, subject, message)
    return ''

@auth.requires_login()
def shareEmail():
    to = request.vars.emails.split(',')
    content = request.vars.content
    subject = '[xElements] {0} {1} shared a playlist with you!'.format(auth.user.first_name, auth.user.last_name)
    if to and content:
        message = '<html><p>{0}<p></html>'.format(content)
        
        mailman(to, subject, message)
    return ''

@auth.requires_login()
def mailman(to, subject, message):
    """ Email
    """
    sender = '{0}@mrxfx.com'.format(auth.user.username)
    mail.send(to=to, subject=subject, message=message, sender=sender)
