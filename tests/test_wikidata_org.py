"""
This file contains tests that connect to the live, "real", production
wikidata.org site. It probably shouldn't be run by default, and *DEFINATELY*
should do only read-only operations without logging in.

It requires the 'nose' python package. To run it, just enter this directory and
do:
    
    $ nosetests

If there are errors it can be helpful to debug with:

    $ nosetests --pdb
"""

from nose.tools import *
from nose.plugins.skip import SkipTest
import unittest

from bbb import *


class TestWikidataOrg(unittest.TestCase):

    @classmethod
    def setUp(cls):
        cls.srv = WikibaseServer(
            api_url="https://www.wikidata.org/w/api.php",
            lang="en",
            auth=None)
        try:
            cls.srv.check()
        except WikibaseException:
            raise SkipTest("Couldn't connect wikidata.org")

    def test_low_level(self):
        self.srv._get("wbgetclaims", dict(entity="Q42"))

