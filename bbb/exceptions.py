
import re

class WikibaseException(Exception):
    """Generic base class for Wikibase API errors"""

    def __init__(self, err):
        self.error = err

    def __repr__(self):
        return self.__unicode__()

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return self.error

class WikibaseAccountError(WikibaseException):

    def __init__(self, user, error):
        self.user = user
        self.error = error

    def __unicode__(self):
        return "User '%s' had error: %s" % (self.user, self.error)

class WikibaseAPIError(WikibaseException):

    def __init__(self, code, info, action):
        self.code = code
        self.info = info
        self.action = action

    def __unicode__(self):
        return "Wikibase server returned error for action '%s': %s" % (
            self.action, self.code)

class MissingEntityError(WikibaseException):

    def __init__(self, id=None, title=None, info=None):
        self.what = "Entity"
        self.id = id
        self.title = title
        if info:
            found_id = re.search("\(Invalid id: (.*)\)", info)
            if found_id:
                self.id = found_id.groups()[0]
            found_title = re.search("\(Invalid title: (.*)\)", info)
            if found_title:
                self.title = found_title.groups()[0]

    def __unicode__(self):
        if self.id:
            return "Couldn't find %s with id: %s" % (self.what, self.id)
        elif self.title:
            return "Couldn't find %s with title: %s" % (self.what, self.title)
        else:
            return "Couldn't find %s (unknown)" % self.what

class MissingItemError(MissingEntityError):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.what = "Item"

class MissingPropertyError(MissingEntityError):
    pass

class APITimeoutError(WikibaseException):

    def __init__(self, query):
        self.query

    def __unicode__(self):
        return "HTTP (or HTTPS) request timed out: %s" % self.query
