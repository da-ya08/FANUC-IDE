from ..ftp_client.FTP_client import FTPClient
from ..service import Service
from tkinter import messagebox
import os, configparser, subprocess

class Robot:
    def __init__(
            self,
            cache_dir: str,
            project_dir: str,
            service: Service
        ) -> None:

        self.SERVICE = service
        self.CACHE_FOLDER = cache_dir
        self.PROJECT_DIRICTORY = project_dir

    def _check_robot_ini(self):
        if not os.path.exists(f'{self.CACHE_FOLDER}\\robot.ini'):
            self._create_robot_ini()
        else:
            try:
                config = configparser.ConfigParser()
                config.read(f'{self.CACHE_FOLDER}\\robot.ini')
                path = '\\'.join(config["WinOLPC_Util"]["Robot"].split('\\')[0:-2])
                if self.PROJECT_DIRICTORY != path:
                    self._create_robot_ini()
            except:
                self._create_robot_ini()

    def _create_robot_ini(self):
        with open(f'{self.CACHE_FOLDER}\\robot.ini', 'w', encoding='utf-8') as f:
            f.write('[WinOLPC_Util]\n')
            f.write(f'Robot={self.PROJECT_DIRICTORY}\\resources\\Robot_1\n')
            f.write('Version=V9.10-1\n')
            f.write(f'Path={self.PROJECT_DIRICTORY}\\resources\\V910-1\\bin\n')
            f.write(f'Support={self.PROJECT_DIRICTORY}\\resources\\Robot_1\\support\n')
            f.write(f'Output={self.PROJECT_DIRICTORY}\\resources\\Robot_1\\output\n')

    def compile_karel(
            self,
            file_path: str    
        ) -> None:

        if not file_path: return
        try:
            os.chdir('\\'.join(file_path.split('\\')[:-1]))
            result = subprocess.run(
                [f'{self.PROJECT_DIRICTORY}\\src\\ktrans.exe', f'{file_path}', '/config' , f'{self.CACHE_FOLDER}\\robot.ini'],
                capture_output=True,
                text=True,
                check=True)
            self.SERVICE.show_info(self.SERVICE.translate('compiled_success'))
            messagebox.showinfo(self.SERVICE.translate('compiled_success'),
                                result.stdout)
        except Exception as e:
            messagebox.showerror(self.SERVICE.translate('compilation_error'),
                                 e.stdout) # type: ignore
        os.chdir(self.PROJECT_DIRICTORY)