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

MAIN_PAGE_FOOTER_TEMPLATE = """\
    <p>Hello %s</p>
    <a href="%s">%s</a>
  </body>
</html>
"""

class Vote(ndb.Model):
    username = ndb.UserProperty(required=True)
    updown = ndb.IntegerProperty(required=True)
    
class Question(ndb.Model):
    author = ndb.UserProperty(required=True)
    content = ndb.TextProperty(required=True)
    createdate = ndb.DateTimeProperty(auto_now_add=True)
    modifydate = ndb.DateTimeProperty(auto_now=True)
    tags = ndb.StringProperty(repeated=True)
    shortcontent = ndb.ComputedProperty(lambda self: self.content[:500])
    votes = ndb.StructuredProperty(Vote, repeated=True)
    score = ndb.IntegerProperty()


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
            self.response.write(QUESTIONDISPLAY_HTML % (question.content, question.key.urlsafe()))
        
        
        
        
        self.response.write('<div><a href=/question>Add Question</a></div>')
        
        self.response.write(MAIN_PAGE_FOOTER_TEMPLATE % (nickname, url, url_linktext))

class QuestionView(webapp2.RequestHandler):
    def get(self):
        self.response.write('<html><body>')
        question_link = self.request.get('question')
        question_key = ndb.Key(urlsafe=question_link)
        
        question = question_key.get()
        
        self.response.write('<p>%s</p>' % question.content)
                
        self.response.write('</body></html>')


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
                
        
app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/question', QuestionHandler),
    ('/view', QuestionView)
], debug=True)
