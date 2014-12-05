#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
from google.appengine.api import users
from google.appengine.ext import ndb
import cgi
import urllib

QUESTIONCREATE_PAGE_HTML = """\
<html>
  <body>
    <form action="/question" method="post">
      <div><p>What is your question?</p></div>
      <div><textarea autofocus required name=content rows=20 cols=80></textarea></div>
       <div><input type="submit" value="Create"></div>
    </form>
  </body>
</html>
"""


QUESTIONDISPLAY_HTML = """\
<div style="width:500px;border-style:ridge;padding: 5">
<p>%s</p>
<a href="/view?question=%s">View</a>
</div>
"""

QUESTIONDISPLAY_VOTE_HTML = """\
<html><body>
<a href=/>Back to Questions</a><br></br>
<div style="width:500px;border-style:ridge;padding: 5">
<div>
    <p style="float:left"><b>%s</b></p>
    <p style="float:right">%s
        <a href=/vote?id=%s&value=up><input type=button value='Up'></input></a>
        <a href=/vote?id=%s&value=down><input type=button value='Down'></input></a>
    </p>
</div>
<div style="clear:both"></div>
<hr style="border-style:solid">
"""
ANSWERDISPLAY_VOTE_HTML = """\
<div>
    <p style="float:left">%s</p>
    <p style="float:right">%s
        <a href=/vote?id=%s&value=up><input type=button value='Up'></input></a>
        <a href=/vote?id=%s&value=down><input type=button value='Down'></input></a>
    </p>
</div>
<div style="clear:both"></div>
<hr style="border-style:dashed">
"""
QUESTIONDISPLAY_VOTE_FOOTER_HTML = """\
<div>
    <form action=/answer method=post>
        <p>What is your answer?</p>
        <textarea required name=content rows=20 cols=68></textarea>
        <input type=submit value=Submit></input>
        <input type=hidden name=question value=%s></input>
    </form>
</div>
</div></body></html>
"""

MAIN_PAGE_FOOTER_TEMPLATE = """\
    <p>Hello %s</p>
    <a href="%s">%s</a>
  </body>
</html>
"""

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


class MainHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        self.response.write('<html><body>')
        nickname = "Guest"
        
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            nickname = user.nickname()
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
        
        questions_query = Question.query().order(-Question.modifydate)
        
        questions = questions_query.fetch(10)
        
        for question in questions:
            self.response.write(QUESTIONDISPLAY_HTML % (question.shortcontent, question.key.urlsafe()))        
        
        
        self.response.write('<div><a href=/question>Add Question</a></div>')
        
        self.response.write(MAIN_PAGE_FOOTER_TEMPLATE % (nickname, url, url_linktext))

class QuestionView(webapp2.RequestHandler):
    def get(self):
        question_link = self.request.get('question')
        question_key = ndb.Key(urlsafe=question_link)
        
        question = question_key.get()
        
        
        self.response.write(QUESTIONDISPLAY_VOTE_HTML % (question.content, question.score, question.key.urlsafe(), question.key.urlsafe()))
        
        answers_query = Answer.query(ancestor=question.key)
        answers = answers_query.fetch(10)
        for answer in answers:
            self.response.write(ANSWERDISPLAY_VOTE_HTML % (answer.content, answer.score, answer.key.urlsafe(), answer.key.urlsafe()))
            
        
        self.response.write(QUESTIONDISPLAY_VOTE_FOOTER_HTML % question.key.urlsafe())


class QuestionHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write(QUESTIONCREATE_PAGE_HTML)
        
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
        
        self.redirect('/view?question=' + question_link)

class VoteHandler(webapp2.RequestHandler):
    def get(self):
        myentity_link = self.request.get('id')
        updown = self.request.get('value')
        vote1 = -1
                
        if updown == 'up':
            vote1 = 1
        
        self.response.write(vote1)
        
        user = users.get_current_user()
        
        if user:
            myentity_key = ndb.Key(urlsafe=myentity_link)
            myentity = myentity_key.get()
            if myentity:
                founduser = False   
                for vote in myentity.votes:
                    #self.response.write(vote)
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
    ('/', MainHandler),
    ('/question', QuestionHandler),
    ('/view', QuestionView),
    ('/answer', AnswerHandler),
    ('/vote', VoteHandler)
], debug=True)
