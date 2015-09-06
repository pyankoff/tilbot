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
import sys
sys.path.insert(0, 'tweepy.zip')
sys.path.insert(0, 'requests_oauthlib.zip')
sys.path.insert(0, 'requests.zip')
sys.path.insert(0, 'oauthlib.zip')

import webapp2
import tweepy
from google.appengine.ext import db
import ConfigParser

class LastTweet(db.Model):
  last_id = db.IntegerProperty()

class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write('Hello world!')

class til(webapp2.RequestHandler):
    def get(self):
        # create bot
        config = ConfigParser.RawConfigParser()
        config.read('settings.cfg')

        # http://dev.twitter.com/apps/myappid
        CONSUMER_KEY = config.get('Twitter OAuth', 'CONSUMER_KEY')
        CONSUMER_SECRET = config.get('Twitter OAuth', 'CONSUMER_SECRET')
        # http://dev.twitter.com/apps/myappid/my_token
        ACCESS_TOKEN_KEY = config.get('Twitter OAuth', 'ACCESS_TOKEN_KEY')
        ACCESS_TOKEN_SECRET = config.get('Twitter OAuth', 'ACCESS_TOKEN_SECRET')

        auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        auth.set_access_token(ACCESS_TOKEN_KEY, ACCESS_TOKEN_SECRET)
        api = tweepy.API(auth)

        # your hashtag or search query and tweet language (empty = all languages)
        hashtag = "#TIL"
        tweetLanguage = "en"


        # retrieve last savepoint if available
        try:
            lastTweet = LastTweet.all().get()
            savepoint = lastTweet.last_id
            print "savepoint: ", savepoint
        except:
            savepoint = ""
            print "No savepoint found. Trying to get 30 results"

        timelineIterator = tweepy.Cursor(api.search, q=hashtag, \
            since_id=savepoint, lang=tweetLanguage).items(50)

        # put everything into a list to be able to sort/filter
        timeline = []
        for status in timelineIterator:
            timeline.append(status)

        try:
            last_tweet_id = timeline[0].id
        except IndexError:
            last_tweet_id = savepoint

        # filter @replies/blacklisted words & users out and reverse timeline
        timeline = filter(lambda status: status.text[0] != "@", timeline)
        timeline.reverse()

        tw_counter = 0
        err_counter = 0

        # iterate the timeline and retweet
        for status in timeline:
            try:
                # print "(%(date)s) %(name)s: %(message)s\n" % \
                #     { "date" : status.created_at,
                #     "name" : status.author.screen_name.encode('utf-8'),
                #     "message" : status.text.encode('utf-8') }
                print status.text.encode('utf-8')

                api.retweet(status.id)
                status.author.follow()
                tw_counter += 1
            except tweepy.error.TweepError as e:
                # just in case tweet got deleted in the meantime or already retweeted
                err_counter += 1
                #print e
                continue

        print "Finished. %d Tweets retweeted, %d errors occured." % (tw_counter, err_counter)

        # write last retweeted tweet id to file
        if lastTweet:
            lastTweet.delete()

        lastTweet = LastTweet(last_id=last_tweet_id)
        lastTweet.put()
        self.response.write("Finished. %d Tweets retweeted, %d errors occured. Last tweet id %d" % (tw_counter, err_counter, last_tweet_id))


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/til', til)
], debug=True)