#!/usr/bin/env python
#
# Created by Chris Pac on 12/4/14.
# Copyright (c) 2014 Chris Pac. All rights reserved.
#

# [START imports]
import webapp2
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.datastore.datastore_query import Cursor
#import cgi
import os
import sys
#import urllib
import re
from itertools import imap
from jinja2 import Markup, escape
import jinja2
import time
import mimetypes
from email.Utils import formatdate
# [END imports]

# [START jinja]
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

# Initial code copied from jinja source code
# Copyright (c) 2009 by the Jinja Team, see AUTHORS for more details.
#
# Modified to Detect Images
#
_letters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
_digits = '0123456789'
PY2 = sys.version_info[0] == 2
if not PY2:
    text_type = str 
else:
    text_type = unicode
         
_word_split_re = re.compile(r'(\s+)')
_punctuation_re = re.compile(
    '^(?P<lead>(?:%s)*)(?P<middle>.*?)(?P<trail>(?:%s)*)$' % (
        '|'.join(imap(re.escape, ('(', '<', '&lt;'))),
        '|'.join(imap(re.escape, ('.', ',', ')', '>', '\n', '&gt;')))
    )
)

_simple_email_re = re.compile(r'^\S+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+$')

def do_urlize_ext(text, trim_url_limit=None, nofollow=False, target=None):
    """Converts any URLs in text into clickable links. Works on http://,
    https:// and www. links. Links can have trailing punctuation (periods,
    commas, close-parens) and leading punctuation (opening parens) and
    it'll still do the right thing.
    
    Converts image URLs into image links.
    
    If trim_url_limit is not None, the URLs in link text will be limited
    to trim_url_limit characters.
    If nofollow is True, the URLs in link text will get a rel="nofollow"
    attribute.
    If target is not None, a target attribute will be added to the link.
    """
        
    trim_url = lambda x, limit=trim_url_limit: limit is not None \
                         and (x[:limit] + (len(x) >=limit and '...'
                         or '')) or x
    words = _word_split_re.split(text_type(escape(text)))
    nofollow_attr = nofollow and ' rel="nofollow"' or ''
    if target is not None and isinstance(target, string_types):
        target_attr = ' target="%s"' % target
    else:
        target_attr = ''
    for i, word in enumerate(words):
        match = _punctuation_re.match(word)
        if match:
            lead, middle, trail = match.groups()
            if middle.startswith('www.'):
                if (middle.endswith('.jpg') or
                    middle.endswith('.png') or
                    middle.endswith('.gif') or
                    middle.endswith('#image')
                    ):
                    middle = '<img src="http://%s"%s%s></img>' % (middle,
                        nofollow_attr, target_attr)
                else:
                    middle = '<a href="http://%s"%s%s>%s</a>' % (middle,
                        nofollow_attr, target_attr, trim_url(middle))                
                 
            if ('@' not in middle and
                not middle.startswith('http://') and
                not middle.startswith('https://') and
                len(middle) > 0 and
                middle[0] in _letters + _digits):
                if (middle.endswith('.org') or
                    middle.endswith('.net') or
                    middle.endswith('.com')
                    ):
                    middle = '<a href="http://%s"%s%s>%s</a>' % (middle,
                        nofollow_attr, target_attr, trim_url(middle))                    
                elif (middle.endswith('.jpg') or
                    middle.endswith('.png') or
                    middle.endswith('.gif') or
                    middle.endswith('#image')
                    ):
                    middle = '<img src="http://%s"%s%s></img>' % (middle,
                        nofollow_attr, target_attr)
            if middle.startswith('http://') or \
               middle.startswith('https://'):
                if (middle.endswith('.jpg') or
                    middle.endswith('.png') or
                    middle.endswith('.gif') or
                    middle.endswith('#image')
                    ):
                    middle = '<img src="%s"%s%s></img>' % (middle,
                        nofollow_attr, target_attr)
                else:
                    middle = '<a href="%s"%s%s>%s</a>' % (middle,
                        nofollow_attr, target_attr, trim_url(middle))
            if '@' in middle and not middle.startswith('www.') and \
               not ':' in middle and _simple_email_re.match(middle):
                middle = '<a href="mailto:%s">%s</a>' % (middle, middle)
            if lead + middle + trail != word:
                words[i] = lead + middle + trail
                
    if JINJA_ENVIRONMENT.autoescape:
        return Markup(u''.join(words))
    else:
        return u''.join(words)

def format_datetime(value, type='rss'):
    return formatdate(time.mktime(value.timetuple()))

JINJA_ENVIRONMENT.filters['datetime'] = format_datetime
JINJA_ENVIRONMENT.filters['urlize_ext'] = do_urlize_ext
# [END jinja]


# [START models]
class Vote(ndb.Model):
    author = ndb.UserProperty(required=True)
    updown = ndb.IntegerProperty(required=True)
    
class Question(ndb.Model):
    author = ndb.UserProperty(required=True)
    content = ndb.TextProperty(required=True)
    createdate = ndb.DateTimeProperty(auto_now_add=True)
    modifydate = ndb.DateTimeProperty(auto_now=True)
    tags = ndb.StringProperty(repeated=True)
    shortcontent = ndb.ComputedProperty(lambda self: self.content[:500])
    votes = ndb.StructuredProperty(Vote, repeated=True)
    score = ndb.IntegerProperty(default=0)

class Answer(ndb.Model):
    author = ndb.UserProperty(required=True)
    content = ndb.TextProperty(required=True)
    createdate = ndb.DateTimeProperty(auto_now_add=True)
    modifydate = ndb.DateTimeProperty(auto_now=True)
    votes = ndb.StructuredProperty(Vote, repeated=True)
    score = ndb.IntegerProperty(default=0)   
    
class Picture(ndb.Model):
    author = ndb.UserProperty(required=True)
    createdate = ndb.DateTimeProperty(auto_now_add=True)
    title = ndb.StringProperty()
    imagedata = ndb.BlobProperty(required=True, indexed=False)
    filename = ndb.StringProperty(required=True)
# [END models]

class MainHandler(webapp2.RequestHandler):
    def post(self, tag):
        self.handlePostGet('post')
    def get(self, tag):
        self.handlePostGet('get', tag)    
    
    def handlePostGet(self, methodtype='get', tag=''):    
        user = users.get_current_user()
        curs = Cursor(urlsafe=self.request.get('next'))
        
        questions_query = Question.query().order(-Question.modifydate)
        
        if tag:
            questions_query = questions_query.filter(Question.tags == tag)
        questions, next_curs, more = questions_query.fetch_page(10, start_cursor=curs)

        more_home = False
        more_url =''
        if not next_curs:
            more = False
        if more:
            more_url = next_curs.urlsafe()
        elif methodtype =='post':
            more_home = True
            more_url = '/'
        
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            nickname = user.nickname()
            user_ok = True
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
            nickname = 'Guest'
            user_ok = False
        
        template_values = {
            'questions': questions,
            'user_ok': user_ok,
            'user_nickname': nickname,
            'user_url': url,
            'user_url_linktext': url_linktext,
            'more': more,
            'more_home': more_home,
            'more_url': more_url
        }

        template = JINJA_ENVIRONMENT.get_template('templates/main.html')
        self.response.write(template.render(template_values))

class QuestionView(webapp2.RequestHandler):
    def rssFeed(self, question_link):
        question_key = ndb.Key(urlsafe=question_link)
        
        question = question_key.get()
        answers_query = Answer.query(ancestor=question.key).order(-Answer.score)
        answers = answers_query.fetch(300)
        
        template_values = {
            'question': question,
            'answers': answers,
            'host_url': self.request.host_url
        }
        
        template = JINJA_ENVIRONMENT.get_template('templates/rssQuestion.html')
        self.response.write(template.render(template_values))

        
    def get(self, question_link):
        user = users.get_current_user()
        question_key = ndb.Key(urlsafe=question_link)
        
        question = question_key.get()
        answers_query = Answer.query(ancestor=question.key).order(-Answer.score)
        answers = answers_query.fetch(300)
        
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            nickname = user.nickname()
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
            nickname = 'Guest'
        
        template_values = {
            'question': question,
            'answers': answers,
            'user': user,
            'user_nickname': nickname,
            'user_url': url,
            'user_url_linktext': url_linktext
        }
        
        template = JINJA_ENVIRONMENT.get_template('templates/questionView.html')
        self.response.write(template.render(template_values))


class QuestionHandler(webapp2.RequestHandler):
    def get(self, action, entity_link):
        if action == 'create':
            self.showCreate()
        elif action == 'modify':
            self.showModify(entity_link)
        
    def showCreate(self):
        template_values = {
            'action': '/question/create',
            'action_name': 'Create',
            'heading': 'What is your question?',
            'content': ''
        }
        template = JINJA_ENVIRONMENT.get_template('templates/questionInput.html')
        self.response.write(template.render(template_values))

    def showModify(self, entity_link):
        user = users.get_current_user()
        myentity = ndb.Key(urlsafe=entity_link).get()        

        if user and myentity and myentity.author == user:
            template_values = {
                'action': '/question/modify/' + entity_link,
                'action_name': 'Modify',
                'heading': 'Make changes',
                'content': myentity.content,
                'back_link': '/view/' + entity_link,
                'tags': ', '.join(myentity.tags)
            }
            template = JINJA_ENVIRONMENT.get_template('templates/questionInput.html')
            self.response.write(template.render(template_values))
        
    def post(self, action, entity_link):
        user = users.get_current_user()
        
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
            return
        
        submitAction = self.request.get('submitButton')
        
        if submitAction == 'Upload':
            pic_link = self.handlePictureUpload(user)
            if pic_link:
                self.reloadPageOnPictureUpload(action, entity_link, pic_link)
            return
                
        if action == 'create':
            question = Question()
            question.author = user
            question.content = self.request.get('content')
            question.tags = [tag.strip() for tag in self.request.get('tags').split(',')]
            question.put()
        if action == 'modify':
            question = ndb.Key(urlsafe=entity_link).get()
            if question and question.author == user: 
                question.content = self.request.get('content')
                question.tags = [tag.strip() for tag in self.request.get('tags').split(',')]
                question.put()
           
        self.redirect('/')
        
    def handlePictureUpload(self, user):
        file_upload = self.request.POST.get('img', None)
        '''
        #FieldStorage
        print "b"
        print file_upload
        
        if file_upload == None:
            print 'none'
        print 'a'
        return
        '''
        try:
            pic = Picture()
            pic.author = user
            pic.title = self.request.get('pic_title')
            pic.imagedata = file_upload.file.read()
            pic.filename = file_upload.filename    
            pic.put()
            return pic.key.urlsafe()
        except:
            pass
            
    def reloadPageOnPictureUpload(self, action, entity_link, pic_link):
        # this whole picture upload needs to be replaced with a postback (ajax or jquery)
        
        img_link = ' ' + self.request.host_url + '/image/' + pic_link + '#image'
        
        if action == 'create':
            template_values = {
                'action': '/question/create',
                'action_name': 'Create',
                'heading': 'What is your question?',
                'content': self.request.get('content') + img_link,
                'tags': self.request.get('tags')
            }            
        elif action == 'modify':
            template_values = {
                'action': '/question/modify/' + entity_link,
                'action_name': 'Modify',
                'heading': 'Make changes',
                'content': self.request.get('content') + img_link,
                'back_link': '/view/' + entity_link,
                'tags': self.request.get('tags')
            }
        
        template = JINJA_ENVIRONMENT.get_template('templates/questionInput.html')
        self.response.write(template.render(template_values))            
        
class AnswerHandler(webapp2.RequestHandler):
    def get(self, action, entity_link):
        user = users.get_current_user()
        myentity_key = ndb.Key(urlsafe=entity_link)
        myentity = myentity_key.get()       

        if user and myentity and myentity.author == user:
            template_values = {
                'action': '/answer/modify/' + entity_link,
                'action_name': 'Modify',
                'heading': 'Make changes',
                'content': myentity.content,
                'back_link': '/view/' + myentity_key.parent().urlsafe()
            }
            template = JINJA_ENVIRONMENT.get_template('templates/baseInput.html')
            self.response.write(template.render(template_values))

    def post(self, action, entity_link):
        user = users.get_current_user()
        
        if user:
            if action == 'create':
                question_link = self.request.get('question')
                answer = Answer(parent=ndb.Key(urlsafe=question_link))
                answer.author = user
                answer.content = self.request.get('content')
                answer.put()
                self.redirect('/view/' + question_link)
            elif action == 'modify':
                answer_key = ndb.Key(urlsafe=entity_link)
                answer = answer_key.get()
                if answer and answer.author == user: 
                    answer.content = self.request.get('content')
                    answer.put()
                    self.redirect('/view/' + answer_key.parent().urlsafe())
        else:
            self.redirect(users.create_login_url(self.request.uri))

class VoteHandler(webapp2.RequestHandler):
    def get(self, updown, entity_link):
        vote1 = -1
                
        if updown == 'up':
            vote1 = 1
        
        self.response.write(vote1)
        
        user = users.get_current_user()
        
        if user:
            myentity_key = ndb.Key(urlsafe=entity_link)
            myentity = myentity_key.get()
            if myentity:
                founduser = False   
                for vote in myentity.votes:
                    if vote.author == user:
                        founduser = True
                        myentity.score = myentity.score - vote.updown
                        vote.updown = vote1
                        break

                myentity.score = myentity.score + vote1
                if not founduser:
                    myentity.votes.append(Vote(author=user, updown=vote1))
                myentity.put()
        else:
            self.redirect(users.create_login_url(self.request.uri))
        
        self.redirect(self.request.referer)
            
class PictureHandler(webapp2.RequestHandler):
    def serveImage(self, picture_link):
        pic_key = ndb.Key(urlsafe=picture_link)

        if not pic_key:
            self.error(404)
            return
        
        pic = pic_key.get()
        
        if pic and pic.imagedata:
            self.response.headers['Content-Type'] = mimetypes.guess_type(pic.filename)[0]
            self.response.out.write(pic.imagedata)
        else:
            self.error(404)
            
        
app = webapp2.WSGIApplication([
    webapp2.Route(r'/tag/<tag>', handler=MainHandler),
    webapp2.Route(r'/', handler=MainHandler, defaults={'tag': ''}),
    webapp2.Route(r'/question/<action:(create|modify)>/<entity_link>', handler=QuestionHandler),
    webapp2.Route(r'/question/<action:(create|modify)>', handler=QuestionHandler, defaults={'entity_link': ''}),
    webapp2.Route('/view/<question_link>', handler=QuestionView),
    webapp2.Route(r'/answer/<action:(create|modify)>/<entity_link>', handler=AnswerHandler),
    webapp2.Route(r'/answer/<action:(create|modify)>', handler=AnswerHandler, defaults={'entity_link': ''}),
    webapp2.Route(r'/rss/<question_link>', handler=QuestionView, handler_method='rssFeed'),
    webapp2.Route(r'/vote/<updown:(up|down)>/<entity_link>', handler=VoteHandler),
    webapp2.Route('/image/<picture_link>', handler=PictureHandler, handler_method='serveImage')
], debug=True)

