import tkinter as tk, json, os
from tkinter import ttk, messagebox
from .conf import LANGUAGES

class Entry(ttk.Entry):
    def set_text(self, text):
        self.delete(0, 'end')
        self.insert(0, text)

class LSSettingsWindow(tk.Toplevel):
    def __init__(self, parent, lang, callback, current_data):
        super().__init__(parent)
        self.language = lang
        self.title(self.translate('ls_set'))
        self.geometry('310x230')
        self.minsize(300, 200)
        self.maxsize(340,250)
        self.header = current_data
        self.callback = callback
        self.protect = tk.IntVar(value=current_data['protect'])
        self.motion = tk.IntVar(value=current_data['motion'])
        self.protocol('WM_DELETE_WINDOW', self._on_close)
        self._setup_ui()

    def _setup_ui(self):
        main_paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashwidth=5)
        main_paned.pack(expand=True, fill='both', padx=5, pady=5)
        
        form_frame = tk.Frame(main_paned, padx=10, pady=10)
        form_frame.pack(expand=True, fill='both')        
        fields = [
            (self.translate('prog_name'), 'name'),
            (self.translate('owner'), 'owner'),
            (self.translate('comment'), 'comment'),
        ]
        self.entries = {}
        for i, (label_text, name) in enumerate(fields):
            tk.Label(form_frame, text=label_text).grid(row=i, column=0, sticky='e', pady=2)
            entry = Entry(form_frame, width=30, show='')
            entry.grid(row=i, column=1, sticky='ew', pady=2)
            self.entries[name] = entry
        self.entries['name'].insert(0, self.header['name'])
        self.entries['owner'].insert(0, self.header['owner'])
        self.entries['comment'].insert(0, self.header['comment'])
        
        tk.Label(form_frame, text='Защита').grid(row=3, column=0, sticky='e', pady=2)
        self.entries['protect'] = tk.Checkbutton(form_frame, anchor='w', variable=self.protect)
        self.entries['protect'].grid(row=3, column=1, sticky='ew', pady=2)
        tk.Label(form_frame, text='Движения').grid(row=4, column=0, sticky='e', pady=2)
        self.entries['motion'] = tk.Checkbutton(form_frame, anchor='w', variable=self.motion)
        self.entries['motion'].grid(row=4, column=1, sticky='ew', pady=2)

        btn_frame = tk.Frame(form_frame)
        btn_frame.grid(row=len(fields)+2, column=1, sticky='e', pady=10) 
        ttk.Button(btn_frame, text=self.translate('save'), command=self._but_save).pack(side='left')
        ttk.Button(btn_frame, text=self.translate('cancel'), command=self._cancel).pack(side='left')
    
    def _write_values(self):
        self.header['name'] = self.entries['name'].get()
        self.header['owner'] = self.entries['owner'].get()
        self.header['comment'] = self.entries['comment'].get()
        self.header['protect'] = self.protect.get()
        self.header['motion'] = self.motion.get()

    def _on_close(self):
        """Вызывается при закрытии окна"""
        answ = messagebox.askyesnocancel(self.translate('save'),
                                  self.translate('save_settings'))
        if answ is True:
            self._but_save()
        elif answ is False:
            self._cancel()

    def _cancel(self):
        if self.callback:
            self.callback(None)  # Передаем обновленные настройки
        self._close()
    
    def _but_save(self):
        if self.callback:
            self._write_values()
            self.callback(self.header)  # Передаем обновленные настройки
        self._close()
    
    def _close(self):
        self.destroy()
    
    def translate(self, key):
        """Получение перевода по ключу"""
        return LANGUAGES[self.language].get(key, key)