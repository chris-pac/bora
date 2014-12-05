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
import cgi
import os
import urllib
import jinja2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
# [END imports]

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
# [END models]

class MainHandler(webapp2.RequestHandler):
    def post(self):
        self.handlePostGet('post')
    def get(self):
        self.handlePostGet()    
    
    def handlePostGet(self, methodtype='get'):    
        user = users.get_current_user()
        curs = Cursor(urlsafe=self.request.get('next'))
        
        questions_query = Question.query().order(-Question.modifydate)
        questions, next_curs, more = questions_query.fetch_page(1, start_cursor=curs)

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

        template = JINJA_ENVIRONMENT.get_template('main.html')
        self.response.write(template.render(template_values))

class QuestionView(webapp2.RequestHandler):
    def get(self, question_link):
        user = users.get_current_user()
        question_key = ndb.Key(urlsafe=question_link)
        
        question = question_key.get()
        answers_query = Answer.query(ancestor=question.key)
        answers = answers_query.fetch(10)
        
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
            'question': question,
            'answers': answers,
            'user_ok': user_ok,
            'user_nickname': nickname,
            'user_url': url,
            'user_url_linktext': url_linktext
        }
        
        template = JINJA_ENVIRONMENT.get_template('questionView.html')
        self.response.write(template.render(template_values))


class QuestionHandler(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('questionCreate.html')
        self.response.write(template.render())
        
    def post(self):
        user = users.get_current_user()
        
        if user:
            question = Question()
            question.author = users.get_current_user()
            question.content = self.request.get('content')
            
            question.put()
        else:
            self.redirect(users.create_login_url(self.request.uri))
            
        self.redirect('/')    

class AnswerHandler(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        question_link = self.request.get('question')
        
        if user:
            answer = Answer(parent=ndb.Key(urlsafe=question_link))
            answer.author = users.get_current_user()
            answer.content = self.request.get('content')
            answer.put()
        else:
            self.redirect(users.create_login_url(self.request.uri))
        
        self.redirect('/view/' + question_link)

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
        
app = webapp2.WSGIApplication([
    webapp2.Route('/', handler=MainHandler),
    webapp2.Route('/question', handler=QuestionHandler),
    webapp2.Route('/view/<question_link>', handler=QuestionView),
    webapp2.Route('/answer', handler=AnswerHandler),
    webapp2.Route(r'/vote/<updown:(up|down)>/<entity_link>', handler=VoteHandler)
], debug=True)

