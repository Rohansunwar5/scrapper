#!/usr/bin/env python
print('If you get error "ImportError: No module named \'six\'" install six:\n'+\
    '$ sudo pip install six')
print('To enable your free eval account and get CUSTOMER, YOURZONE and ' + \
    'YOURPASS, please contact sales@brightdata.com')
import sys
if sys.version_info[0]==2:
    import six
    from six.moves.urllib import request
    opener = request.build_opener(
        request.ProxyHandler(
            {'http': 'http://brd-customer-hl_462c03c7-zone-residential:kq76938zwll1@brd.superproxy.io:22225',
            'https': 'http://brd-customer-hl_462c03c7-zone-residential:kq76938zwll1@brd.superproxy.io:22225'}))
    print(opener.open('http://geo.brdtest.com/mygeo.json').read())
if sys.version_info[0]==3:
    import urllib.request
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler(
            {'http': 'http://brd-customer-hl_462c03c7-zone-residential:kq76938zwll1@brd.superproxy.io:22225',
            'https': 'http://brd-customer-hl_462c03c7-zone-residential:kq76938zwll1@brd.superproxy.io:22225'}))
    print(opener.open('http://geo.brdtest.com/mygeo.json').read())