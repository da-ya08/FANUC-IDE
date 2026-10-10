class ConnectionError(Exception):
    '''A problem arises when connecting to the server.'''

class AuthorizationError(Exception):
    '''Incorrect login or password'''

class FilesListReceivingError(Exception):
    '''There is a problem with retrieving files from the server.'''

class FileReceivingError(Exception):
    '''There is a problem with retrieving file from the server.'''

class FileSendingError(Exception):
    '''There is a problem with sending file to the server.'''

class FileDeletingError(Exception):
    '''There is a problem with deleting file on the server.'''