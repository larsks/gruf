class GrufError(Exception):
    '''An application error has occurred'''

    def __str__(self):
        if self.__doc__:
            return self.__doc__
        else:
            return super(GrufError, self).__str__()


class NoGerritRemote(GrufError):
    '''Unable to determine address of gerrit server'''


class UnknownRemoteAttribute(GrufError):
    '''The attribute you have requested is not available'''


class TooManyChanges(GrufError):
    '''Expecting one result but received many'''


class NoFilter(GrufError):
    '''No filter is available for the specified command'''


class GerritCommandError(GrufError):
    pass
