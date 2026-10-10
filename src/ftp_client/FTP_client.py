from ftplib import FTP
from typing import Literal
from .exceptions import *

class FTPClient:
    def __init__(
            self, 
            timeout: float = 5.0, 
            encoding: str = 'cp1251'
        ) -> None:
        '''Self-writed FTP class for FANUC-IDE

        :param timeout (float): Time in seconds for attempting to connect
        :param encoding (str): The encoding of target server'''

        self.TIMEOUT = timeout
        self.ENCODING = encoding
        self.CURRENT_SERVER = ''
        self.LOGIN = ''
        self.PASSWORD = ''
        self.FTP = FTP(timeout=self.TIMEOUT, encoding=self.ENCODING)

    def connect(
            self, 
            server: str, 
            login: str = 'admin', 
            pasword: str = ''
        ) -> bool:
        '''Connection to server with login()

        :param server (str): Target server address
        :param login (str): The username for login(), default is 'admin'
        :param password (str): The password for login(), default is empty
        :return bool: True if the connection is established'''

        self.CURRENT_SERVER = server
        self.LOGIN = login
        self.PASSWORD = pasword
        self.FTP.close()
        try:
            self.FTP.connect(self.CURRENT_SERVER)
        except Exception as e:
            raise ConnectionError(e)
        
        try:    
            self.FTP.login(self.LOGIN, self.PASSWORD)
        except Exception as e:
            raise AuthorizationError(e)
        return True

    def get_files_list(
            self, 
            filter: Literal['ls', 'pc', 'tp', 'none'] = 'none'
        ) -> list[str]:
        '''Retrieving files list from the server according to the filter

        :param filter (Literal): Filter for receiving files
        :return list[str]: List of received files'''

        try:
            server_files = self.FTP.nlst()
        except Exception as e:
            raise FilesListReceivingError(e)
        if filter != 'none':
            server_files = [f for f in server_files if any(f.lower().endswith(ext) for ext in filter)]
            return server_files
        return server_files

    def download_file(
            self,
            file_name: str,
            callback: object
        ) -> bool:
        '''Retrieving file from the server
        
        :param file_name (str): The name of the target file
        :return bool: True if download is successfull'''

        try:
            self.FTP.retrbinary(f"RETR {file_name}", callback) # type: ignore
        except Exception as e:
            raise FileReceivingError(e)
        return True

    def send_file(
            self,
            file_name: str,
            content
        ) -> bool | None:
        '''Send the file to selected server
        
        :param file_name (str): The name of the target file
        :param content: The content for sending
        :return bool: True if send is successfull'''
        try:
            self.FTP.voidcmd('TYPE I')
            self.FTP.storbinary(file_name, content)
        except Exception as e:
            raise FileSendingError(e)
        return True

    def delete_file(
            self,
            file_name: str
        ) -> bool | None:
        '''Deleting file from the server
            
        :param file_name (str): The name of the target file
        :return bool: True if deleting is successful'''

        try:
            self.FTP.delete(file_name)
        except Exception as e:
            raise FileDeletingError(e)
        return True

    def disconnect(
            self
        ) -> None:

        self.FTP.close()

# test = FTPClient()
# test.connect('127.0.0.1')
# print(test.delete_file('MOVE_TEST.TP'))