# -*- coding: utf-8 -*-
from MySQLdb.constants.FIELD_TYPE import VARCHAR, DATE

#########################################################################
## This scaffolding model makes your app work on Google App Engine too
## File is released under public domain and you can use without limitations
#########################################################################

## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
# request.requires_https()

if not request.env.web2py_runtime_gae:
    ## if NOT running on Google App Engine use SQLite or other DB
    db = DAL('sqlite://xelements.sqlite')
    #session.connect(request, response, db=db, masterapp='xview')
else:
    ## connect to Google BigTable (optional 'google:datastore://namespace')
    db = DAL('google:datastore')
    ## store sessions and tickets there
    session.connect(request, response, db=db)
    ## or store session in Memcache, Redis, etc.
    ## from gluon.contrib.memdb import MEMDB
    ## from google.appengine.api.memcache import Client
    ## session.connect(request, response, db = MEMDB(Client()))

## by default give a view/generic.extension to all actions from localhost
## none otherwise. a pattern can be 'controller/function.extension'
response.generic_patterns = ['*'] if request.is_local else []
## (optional) optimize handling of static files
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'

#########################################################################
## Here is sample code if you need for
## - email capabilities
## - authentication (registration, login, logout, ... )
## - authorization (role based authorization)
## - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
## - old style crud actions
## (more options discussed in gluon/tools.py)
#########################################################################

from gluon.tools import Auth, Crud, Service, PluginManager, prettydate
auth = Auth(db, cas_provider=URL('xcas', 'default', 'user', args=['cas'], scheme=True, host=True))
crud, service, plugins = Crud(db), Service(), PluginManager()

## create all tables needed by auth if not custom tables
#auth.settings.login_url = URL(a='xview', c='default', f='user', args=['login'])

auth.define_tables(username=True, signature=False)

## configure email
mail = auth.settings.mailer
mail.settings.server = 'logging' or 'mail.com'
mail.settings.sender = 'systems@mail.com'
mail.settings.login = 'admin:pass'

## configure auth policy
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True
auth.settings.actions_disabled.append('register')

one_day = 3600 * 24
auth.settings.expiration = one_day # seconds * hours * days
auth.settings.long_expiration = one_day * 7 # seconds * hours * days
auth.settings.remember_me_form = True

#auth.settings.extra_fields['auth_user'] = [
#    Field('shotgun_id', length=255),
#]

## if you need to use OpenID, Facebook, MySpace, Twitter, Linkedin, etc.
## register with janrain.com, write your domain:api_key in private/janrain.key
from gluon.contrib.login_methods.rpx_account import use_janrain
use_janrain(auth, filename='private/janrain.key')

#########################################################################
## Define your tables below (or better in another model file) for example
##
## >>> db.define_table('mytable',Field('myfield','string'))
##
## Fields can be 'string','text','password','integer','double','boolean'
##       'date','time','datetime','blob','upload', 'reference TABLENAME'
## There is an implicit 'id integer autoincrement' field
## Consult manual for more options, validators, etc.
##
## More API examples for controllers:
##
## >>> db.mytable.insert(myfield='value')
## >>> rows=db(db.mytable.myfield=='value').select(db.mytable.ALL)
## >>> for row in rows: print row.id, row.myfield
#########################################################################

## after defining tables, uncomment below to enable auditing
# auth.enable_record_versioning(db)

db.define_table('xelements_filetype',
    Field('name', length=25),
    #migrate=False,
    )

db.define_table('xelements_branch',
    Field('name', length=25),
    Field('colour', length=12),
    Field('ordering', 'integer'),
    #migrate=False,
    )

db.define_table('xelements_category',
    Field('name', length=25),
    Field('colour', length=12),
    Field('branch_id', db.xelements_branch),
    Field('ordering', 'integer'),
    #migrate=False,
    )

db.define_table('xelements_element',
    Field('name', length=64),
    Field('element_code', length=10),
    Field('category_id', db.xelements_category),
    Field('file_type_id', db.xelements_filetype),
    Field('file_path', length=255),
    Field('internal_notes', length=255),
    Field('cut_length', 'integer'),
    Field('old_length', 'integer'),
    Field('stereo', 'integer'),
    Field('hdpreview_required', 'integer'),
    Field('webmovie', 'integer'),
    Field('resolution', length=25),
    Field('width', 'integer'),
    Field('height', 'integer'),
    Field('file_type', length=10),
    Field('qt_path', length=255),
    Field('pblast_path', length=255),
    Field('wcam_path', length=255),
    Field('mostusedin', length=64),
    Field('colourspace', length=128),
    Field('camera', length=128),
    Field('alpha', 'integer'),
    Field('source', length=128),
    Field('date_updated', 'datetime'),
    Field('date_created', 'datetime'),
    Field('description', length=255),
    Field('thumbnail', length=128),
    Field('videofile', length=128),
    Field('retired', 'integer', default=0),
    #migrate=False,
    )

db.define_table('xelements_comment',
    Field('element_id', db.xelements_element, label='Element'),
    Field('username', length=64, label='Poster'),
    Field('date_added', 'datetime'),
    Field('content', 'text'),
    Field('parent_id', 'reference xelements_comment', label='Reply To'),
    Field('priority', 'integer', default=0),
    #migrate=False
    )

db.define_table('xelements_playlist',
    Field('name', length=64),
    Field('description', length=128),
    Field('user_id', db.auth_user),
    Field('element_ids', 'text'),
    Field('favourite', 'integer', default=0),
    Field('date_modified', 'datetime'),
    #migrate=False,
    )

db.define_table('xelements_tag',
    Field('name', length=64),
    Field('code', length=64),
    Field('frequency', 'integer', default=0),
    #migrate=False,
    )

db.define_table('xelements_tagmap',
    Field('element_id', db.xelements_element),
    Field('tag_id', db.xelements_tag),
    #migrate=False,
    )

db.define_table('xelements_type',
    Field('name', length=25),
    migrate=False,
    )

db.define_table('xelements_news',
    Field('type_id', db.xelements_type, label='Object Type'),
    Field('target_id', 'integer'),
    Field('user_id', db.auth_user),
    Field('content', 'text'),
    Field('date_created', 'datetime'),
    )

from gluon import current
current.auth = auth
current.db = db
