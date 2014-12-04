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


MAIN_PAGE_FOOTER_TEMPLATE = """\
    <p>Hello %s</p>
    <a href="%s">%s</a>
  </body>
</html>
"""

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
        
        self.response.write(MAIN_PAGE_FOOTER_TEMPLATE % (nickname, url, url_linktext))

app = webapp2.WSGIApplication([
    ('/', MainHandler)
], debug=True)
