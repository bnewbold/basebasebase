
import requests
import time
import warnings
import dateutil.parser

from .util import *
from .exceptions import *
from .constants import *

__version__ = (0, 0, 0)

BOT_DEV_URL = "https://github.com/bnewbold/basebasebase"
BOT_DEV_EMAIL = "bnewbold@robocracy.org"
BOT_USER_AGENT = "basebasebase/%d.%d (%s; %s)" % (
    __version__[0], __version__[1], BOT_DEV_URL, BOT_DEV_EMAIL)
DEFAULT_LANG = "en"
DEFAULT_SITE = "enwiki"


class WikibaseServer:
    '''
    This class represents a Wikibase API endpoint. It isn't called a "Site"
    because that term is ambiguous in this context.
    '''

    def __init__(self, api_url, lang=DEFAULT_LANG, auth=None, is_bot=False,
                 user_agent=BOT_USER_AGENT, maxlag=5, site=DEFAULT_SITE,
                 throttle_delay=0.):
        self.api_url = str(api_url)
        self.lang = DEFAULT_LANG

        self.throttle_delay = throttle_delay
        self.site = site

        self.is_bot = is_bot
        self.session = requests.Session()
        assert(auth is None or len(auth) == 2)
        self.session.auth = auth
        self.session.headers.update({
            'User-Agent': user_agent,
            'Api-User-Agent': user_agent
        })
        if maxlag is not None:
            self.session.params['maxlag'] = int(maxlag)
        self.session.params['format'] = 'json'
        self.session.params['uselang'] = 'user'

    def __repr__(self):
        return "<WikibaseServer at %s>" % self.api_url

    def _check_api_err(self, action, resp):

        if 'warnings' in resp:
            for k in resp['warnings']:
                warnings.warn(str((k, resp['warnings'][k])), Warning)

        if 'error' in resp:
            try:
                raise WikibaseAPIError(resp['error']['code'],
                    resp['error']['info'], action)
            except KeyError:
                raise WikibaseException(resp['error'])

    def _api_call(self, method, action, params):
        params['action'] = action
        if self.throttle_delay:
            time.sleep(self.throttle_delay)
        if method.upper() == "GET":
            resp = self.session.get(self.api_url, params=params)
        elif method.upper() == "POST":
            resp = self.session.post(self.api_url, params=params)
        else:
            raise ValueError("method must be GET or POST")
        resp_json = resp.json()
        self._check_api_err(action, resp_json)
        return resp_json

    def _post(self, action, params):
        return self._api_call("POST", action, params)

    def _get(self, action, params=dict()):
        return self._api_call("GET", action, params)

    def check(self):
        # Check that wikibase API calls work (instead of just "action=query")
        self._get("wbparsevalue",
            dict(datatype="time", values="1999-12-31|now"))

    def login(self, user=None, passwd=None, is_bot=None, force_http=False):
        if user is None or passwd is None:
            raise WikibaseException("Need user and pass to attempt log-in")

        if not force_http and not self.api_url.lower().startswith("https:"):
            raise WikibaseException("Cowardly refusing to log in without https")

        if is_bot is not None:
            self.is_bot = bool(is_bot)
        self.user = user
        # not keeping password around; don't need it

        # First partially log-in to get a token...
        self.session.params.pop('assert', None)
        resp = self._post("login", dict(lgname=self.user, lgpassword=passwd))
        token = resp['login']['token']

        # Then really log-in
        resp = self._post("login", dict(lgname=self.user, lgpassword=passwd, lgtoken=token))
        result = resp['login']['result']
        if result != 'Success':
            raise WikibaseAccountError(user, result)

        if self.is_bot:
            self.session.params['assert'] = 'bot'
        else:
            self.session.params['assert'] = 'user'

        # Simple ping to check that we are actually logged in
        self._get("query")

    def logout(self):
        self.user = None
        self.session.params.pop('assert', None)
        self._get("logout")

    def _get_entities(self, query, expected, site=None, lang=None, redirects=True, as_titles=False):
        
        """
        NB: doesn't handle case of multiple sites, single title
        """

        params = {
            'sites': site or self.site,
            'languages': lang or self.lang,
            'redirects': redirects and "yes" or "no",
        }
        if as_titles:
            params['titles'] = '|'.join(query)
        else:
            params['ids'] = '|'.join(query)

        try:
            resp = self._get("wbgetentities", params)
        except WikibaseAPIError as wae:
            if wae.code == "no-such-entity":
                raise MissingEntityError(info=wae.info)
            else:
                raise wae

        if not 'success' in resp:
            raise WikibaseException("Expected 'success' in wbgetentities response")

        entities = resp['entities'].values()

        for e in entities:
            if 'missing' in e or e['type'] != expected:
                if 'title' in e:
                    raise MissingEntityError(title=e['title'])
                elif 'id' in e:
                    raise MissingEntityError(id=e['id'])
                else:
                    raise MissingEntityError()

        return entities

    def get_items(self, query, **kwargs):
        as_titles = False
        if type(query[0]) is int:
            # Convert list of ints to QIDs
            query = map(lambda x: "Q%d" % x, query)
        elif not (type(query[0]) is str and query[0][0] in "Q" and query[0][1:].isdigit()):
            # Must be list of titles
            as_titles = True

        try:
            entities = self._get_entities(query, as_titles=as_titles, expected='item', **kwargs)
        except MissingEntityError as wee:
            # Case entity error to item error
            raise MissingItemError(id=wee.id, title=wee.title)
        items = [WikibaseItem.from_json(e) for e in entities]
        return items

    def get_item(self, query, **kwargs):
        return self.get_items((query, ), **kwargs)
            

class WikibaseEntity:
    '''
    Base class for WikibaseItem and WikibaseProperty
    '''

    def __init__(self, dbid=None, rev=None, rev_timestamp=None, labels=[],
                 descriptions=[], aliases=[], statements=[], sitelinks=[]):
        self.dbid = dbid
        self.rev = rev
        self.rev_timestamp = rev_timestamp
        self.labels = labels
        self.descriptions = descriptions
        self.aliases = aliases
        self.statements = statements
        self.sitelinks = sitelinks

    @classmethod
    def from_json(cls, j):
        we = cls(
            dbid=j['id'],
            rev=j['lastrevid'],
            rev_timestamp=dateutil.parser.parse(j['modified']),
            aliases=j['aliases'],
            sitelinks=j['sitelinks'],
            descriptions=j['descriptions'],
        )
        claims = j['claims']
        for c in claims:
            we.statements.append(WikibaseStatement.from_json(c))
        return we

    def add_statement(self, statement):
        raise NotImplementedError

    def add_label(self, label):
        raise NotImplementedError

    def add_alias(self, label):
        raise NotImplementedError

class WikibaseItem(WikibaseEntity):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return "<WikibaseItem %s>" % self.qid

class WikibaseProperty(WikibaseEntity):

    def __init__(self,*args, **kwargs):
        self.datatype = kwargs.pop('datatype')
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return "<WikibaseProperty %s>" % self.pid

class WikibaseStatement:

    def __init__(self, property=None, value=None, qualifiers=[], references=[],
                 rank='normal'):
        self.property = property
        self.value = value
        self.qualifiers = qualifiers
        self.references = references
        self.rank = rank

    def __repr__(self):
        if self.property:
            return "<WikibaseStatement %s is %s>" % (self.property.pid, self.value)
        else:
            return "<WikibaseStatement (empty)>"

