from tkinter import messagebox, Label
from .conf import LANGUAGES

class Service:
    def __init__(
            self,
            language: str
        ) -> None:

        self.status_label: Label
        self.language = language
        
    def translate(self, key: str):
        """Получение перевода по ключу"""
        return LANGUAGES[self.language].get(key, key)

    def show_info(self, text:str, lvl=0, need_message=False) -> None:
        """Show message

        :param text (str): text of message
        :param lvl (int): level of message
            =0: INFO
            =1: WARNING
            =2: ERROR
        :param need_message (bool): need show window?
        """
        levels = ['INFO:', 'WARN:', 'ERROR:']
        self.status_label.config(text=f'{levels[lvl]} {text}')
        if lvl == 0 and need_message:
            messagebox.showinfo(levels[lvl], text)
        elif lvl == 1 and need_message:
            messagebox.showwarning(levels[lvl], text)
        elif lvl == 2 and need_message:
            messagebox.showerror(levels[lvl], text)