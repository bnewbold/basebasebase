"""
This file contains tests that connect to a local wikibase install (eg, in a
vagrant env).

It requires the 'nose' python package. To run it, just enter this directory and
do:
    
    $ nosetests

If there are errors it can be helpful to debug with:

    $ nosetests --pdb
"""

from nose.tools import *
from nose.plugins.skip import SkipTest
import unittest
import random

from bbb import *

TEST_SERVER_URL = "http://wikidata.wiki.local.wmftest.net:8080/w/api.php"
TEST_SERVER_USER = "TestBaseBot"
TEST_SERVER_PASSWD = "TestBaseBot123" # I know, right?

class TestWikidataOrg(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.srv = WikibaseServer(
            api_url=TEST_SERVER_URL,
            lang="en",
            auth=None)
        try:
            cls.srv.check()
        except WikibaseException:
            raise SkipTest("Couldn't connect to local dev wikibase server")

        cls.srv.login(TEST_SERVER_USER, TEST_SERVER_PASSWD,
                        force_http=True)

        cls.srv.check()

    def setUp(self):
        #self.srv.logout()
        #self.srv.login(TEST_SERVER_USER, TEST_SERVER_PASSWD, force_http=True)
        pass    # TODO:

    def test_logout_login(self):
        self.srv.logout()
        self.srv.check()
        self.srv.login(TEST_SERVER_USER, TEST_SERVER_PASSWD, force_http=True)
        self.srv.check()

    def test_force_http(self):
        tsrv = WikibaseServer("http://example.com/w/api.php")
        with assert_raises(WikibaseException):
            tsrv.login("fake", "fake")

    def test_low_level(self):
        self.srv._get("wbgetclaims", dict(entity="Q3"))

    def test_api_warnings(self):
        with warnings.catch_warnings(record=True) as warns:
            self.srv._get("wbparsevalue",
                dict(datatype="time", values="now",
                    dummy_non_existant_param="THIS"))

            assert_equals(len(warns), 1)
            print(warns[0])
            print(str(warns[0].message))
            assert "Unrecognized parameter" in str(warns[0].message)

    def test_bad_pass(self):
        self.srv.logout()
        with assert_raises(WikibaseAccountError):
            self.srv.login(TEST_SERVER_USER, TEST_SERVER_PASSWD+"BADBAD", force_http=True)

    def test_get_item(self):
        item = self.srv.get_item("Coffee")
        item = self.srv.get_item("Q2")
        item = self.srv.get_item(2)

    def test_get_property(self):
        raise SkipTest("UNIMPLEMENTED")
        item = self.srv.get_property("Mass")
        item = self.srv.get_property(pid="P2")
        item = self.srv.get_property(pid=2)

    def test_find_items(self):
        raise SkipTest("UNIMPLEMENTED")
        l = self.srv.find_items("love", limit=5)
        l = self.srv.find_items("robot", limit=5)
        l = self.srv.find_items("Imposible_String_" + random.randint(10e19, 10e20), limit=5)
        assert len(l) == 0

    def test_create_item(self):
        raise SkipTest("UNIMPLEMENTED")
        item = WikibaseItem("QWERTY Layout")
        self.srv.create(thing)
        item.add(WikibaseStatement(
            "Inventor", "Christopher Latham Sholes", datatype="item",
            qualifiers={'year_of_invention': 1860},
            refs=['http://www.smithsonianmag.com/arts-culture/fact-of-fiction-the-legend-of-the-qwerty-keyboard-49863249/']))
        self.srv.save(item)

