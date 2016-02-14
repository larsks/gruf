class GrufError(Exception):
    '''An application error has occurred'''

    def __str__(self):
        return self.__doc__

class NoGerritRemote(GrufError):
    '''Unable to determine address of gerrit server'''

class UnknownRemoteAttribute(GrufError):
    '''The attribute you have requested is not available'''

class TooManyChanges(GrufError):
    '''Expecting one result but received many'''
