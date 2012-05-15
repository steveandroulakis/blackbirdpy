# -*- coding: utf-8 -*-
#
# Blackbirdpy - a Python implementation of Blackbird Pie, the tool
# @robinsloan uses to generate embedded HTML tweets for blog posts.
#
# See: http://media.twitter.com/blackbird-pie
#
# This Python version was written by Jeff Miller, http://twitter.com/jeffmiller
#
# Requires Python 2.6.
#
# Usage:
#
# - To generate embedded HTML for a tweet from inside a Python program:
#
#   import blackbirdpy
#   embed_html = blackbirdpy.embed_tweet_html(tweet_id)
#
# - To generate embedded HTML for a tweet from the command line:
#
#   $ python blackbirdpy.py <tweeturl>
#     e.g.
#   $ python blackbirdpy.py http://twitter.com/punchfork/status/16342628623
#
# - To run unit tests from the command line:
#
#   $ python blackbirdpy.py --unittest

import datetime
import email.utils
import json
import optparse
import re
import sys
import unittest
import urllib2

TWEET_EMBED_HTML = u'''<div class="bbpBox" id="t{id}"><blockquote><span class="twContent">{tweetText}</span><span class="twMeta"><br /><span class="twDecoration">&nbsp;&nbsp;&mdash; </span><span class="twRealName">{realName}</span><span class="twDecoration"> (</span><a href="http://twitter.com/{screenName}"><span class="twScreenName">@{screenName}</span></a><span class="twDecoration">) </span><a href="{tweetURL}"><span class="twTimeStamp">{easyTimeStamp}</span></a><span class="twDecoration"></span></span></blockquote></div>
'''

def wrap_entities(json):
  """Turn URLs and @ mentions into links. Embed Twitter native photos."""
  text = json['text']
  mentions = json['entities']['user_mentions']
  hashtags = json['entities']['hashtags']
  urls = json['entities']['urls']
  # media = json['entities']['media']
  try:
    media = json['entities']['media']
  except KeyError:
    media = []
  
  for u in urls:
    try:
      link = '<a href="' + u['expanded_url'] + '">' + u['display_url'] + '</a>'
    except (KeyError, TypeError):
      link = '<a href="' + u['url'] + '">' + u['url'] + '</a>'
    text = text.replace(u['url'], link)
  
  for m in mentions:
    text = re.sub('(?i)@' + m['screen_name'], '<a href="http://twitter.com/' +
            m['screen_name'] + '">@' + m['screen_name'] + '</a>', text, 0)

  for h in hashtags:
    text = re.sub('(?i)#' + h['text'], '<a href="http://twitter.com/search/%23' +
            h['text'] + '">#' + h['text'] + '</a>', text, 0)
  
  for m in media:
    if m['type'] == 'photo':
      link = '<br /><br /><a href="' + m['media_url'] + ':large">' +\
              '<img src="' + m['media_url'] + ':small"></a><br />'
    else:
      link = '<a href="' + m['expanded_url'] + '">' + m['display_url'] + '</a>'
    text = text.replace(m['url'], link)

  return text
    

def timestamp_string_to_datetime(text):
    """Convert a string timestamp of the form 'Wed Jun 09 18:31:55 +0000 2010'
    into a Python datetime object."""
    tm_array = email.utils.parsedate_tz(text)
    return datetime.datetime(*tm_array[:6]) - datetime.timedelta(seconds=tm_array[-1])


def easy_to_read_timestamp_string(dt):
    """Convert a Python datetime object into an easy-to-read timestamp
    string, like 'Wed Jun 16 2010'."""
    return re.sub(r'(^| +)0', r'\1', dt.strftime('%a %b %d %Y'))


def embed_tweet_html(tweet_id, extra_css=None):
    """Generate embedded HTML for a tweet, given its Twitter URL.  The
    result is formatted as a simple quote, but with span classes that
    allow it to be reformatted dynamically (through jQuery) in the style
    of Robin Sloan's Blackbird Pie.
    See: http://media.twitter.com/blackbird-pie

    The optional extra_css argument is a dictionary of CSS class names
    to CSS style text.  If provided, the extra style text will be
    included in the embedded HTML CSS.  Currently only the bbpBox
    class name is used by this feature.
    """
    api_url = 'http://api.twitter.com/1/statuses/show.json?include_entities=true&id=' + tweet_id
    api_handle = urllib2.urlopen(api_url)
    api_data = api_handle.read()
    api_handle.close()
    tweet_json = json.loads(api_data)
    
    tweet_text = wrap_entities(tweet_json).replace('\n', '<br />')

    tweet_created_datetime = timestamp_string_to_datetime(tweet_json["created_at"])
    tweet_local_datetime = tweet_created_datetime + (datetime.datetime.now() - datetime.datetime.utcnow())
    tweet_easy_timestamp = easy_to_read_timestamp_string(tweet_local_datetime)

    if extra_css is None:
        extra_css = {}
        
    tweet_url = 'https://twitter.com/#!/' + tweet_json['user']['screen_name'] + '/status/' \
        + tweet_id

    html = TWEET_EMBED_HTML.format(
        id=tweet_id,
        tweetURL=tweet_url,
        screenName=tweet_json['user']['screen_name'],
        realName=tweet_json['user']['name'],
        tweetText=tweet_text,
        source=tweet_json['source'],
        profilePic=tweet_json['user']['profile_image_url'],
        profileBackgroundColor=tweet_json['user']['profile_background_color'],
        profileBackgroundImage=tweet_json['user']['profile_background_image_url'],
        profileTextColor=tweet_json['user']['profile_text_color'],
        profileLinkColor=tweet_json['user']['profile_link_color'],
        timeStamp=tweet_json['created_at'],
        easyTimeStamp=tweet_easy_timestamp,
        utcOffset=tweet_json['user']['utc_offset'],
        bbpBoxCss=extra_css.get('bbpBox', ''),
    )
    return html


#todo: unit tests were broken due to removed functions. Have removed and should update them


if __name__ == '__main__':
    option_parser = optparse.OptionParser(usage='%prog [options] tweetid' + \
        '\n\nThis version is the @steveandroulakis edit. Takes tweet ID instead of URL.' + \
        '\n\ntweetid = 12346789 where tweet URL' \
        ' is \nhttps://twitter.com/#!/spetznatz/status/12346789')
    option_parser.add_option('--unittest', dest='unittest', action='store_true', default=False,
                             help='Run unit tests and exit (tests have been removed for now, see code)')
    options, args = option_parser.parse_args()

    if options.unittest:
        unittest.main(argv=[sys.argv[0]])
        sys.exit(0)

    if len(args) != 1:
        option_parser.print_help()
        sys.exit(1)
    
    print embed_tweet_html(args[0]).encode('utf8')
