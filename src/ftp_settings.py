import tkinter as tk
from tkinter import ttk, messagebox
import json, os, socket
from ftplib import FTP
from .conf import LANGUAGES

class Entry(ttk.Entry):
    def set_text(self, text):
        self.delete(0, 'end')
        self.insert(0, text)

class FTPSettingsWindow(tk.Toplevel):
    def __init__(self, parent, lang, callback):
        super().__init__(parent)
        self.title("FTP settings")
        self.geometry("800x500")
        self.minsize(600, 400)
        self.servers_list = {}
        self.servers_path = './resources/servers_list.json'
        self.selected_server = None
        self.language = lang
        self.callback = callback
        self.protocol('WM_DELETE_WINDOW', self._on_close)
        self._setup_ui()
        self._center_window()
        self.grab_set()
    
    def _center_window(self):
        """Центрирует окно относительно родительского"""
        self.update_idletasks()
        parent_x = self.master.winfo_x()
        parent_y = self.master.winfo_y()
        parent_width = self.master.winfo_width()
        parent_height = self.master.winfo_height()        
        x = parent_x + (parent_width // 2) - (800 // 2)
        y = parent_y + (parent_height // 2) - (500 // 2)        
        self.geometry(f"+{x}+{y}")
    
    def _setup_ui(self):
        """Создает интерфейс окна настроек"""
        main_paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashwidth=5)
        main_paned.pack(expand=True, fill='both', padx=5, pady=5)        
        # Левая панель - список серверов
        left_frame = tk.Frame(main_paned, width=200, bg='#f0f0f0')
        main_paned.add(left_frame)        
        # Правая панель - форма редактирования
        right_frame = tk.Frame(main_paned)
        main_paned.add(right_frame)        
        self._create_servers_list(left_frame)
        self._create_edit_form(right_frame)
    
    def _create_servers_list(self, parent):
        """Создает список серверов"""
        tk.Label(parent, text=self.translate('saved_servs'), bg='#f0f0f0', 
                font=('Arial', 10, 'bold')).pack(fill='x', padx=5, pady=5)
        self.servers_tree = ttk.Treeview(parent, show='tree', selectmode='browse')
        self.servers_tree.pack(expand=True, fill='both', padx=5, pady=5)
        btn_frame = tk.Frame(parent, bg='#f0f0f0')
        btn_frame.pack(fill='x', padx=5, pady=5)
        ttk.Button(btn_frame, text=self.translate('del'), command=self._delete_server).pack(side='left', padx=2)
        self.servers_tree.bind('<<TreeviewSelect>>', self._on_server_selected)        
        self.load_servers_list()
    
    def _create_edit_form(self, parent):
        """Создает форму редактирования"""
        form_frame = tk.Frame(parent, padx=10, pady=10)
        form_frame.pack(expand=True, fill='both')        
        # Поля формы
        fields = [
            (self.translate('con_name'), 'conn_name'),
            (self.translate('adr'), 'adress'),
            (self.translate('login'), 'login'),
            (self.translate('pass'), 'pass')
        ]        
        self.entries = {}
        for i, (label_text, name) in enumerate(fields):
            tk.Label(form_frame, text=label_text).grid(row=i, column=0, sticky='e', pady=2)
            entry = Entry(form_frame, width=30, show='')
            entry.grid(row=i, column=1, sticky='ew', pady=2)
            self.entries[name] = entry  
        # Кнопки
        btn_frame = tk.Frame(form_frame)
        btn_frame.grid(row=len(fields)+2, column=1, sticky='e', pady=10)   
        ttk.Button(btn_frame, text=self.translate('add'), command=self._add_server).pack(side='left', padx=2)     
        ttk.Button(btn_frame, text=self.translate('save'), command=self._save_settings).pack(side='right', padx=5)
        ttk.Button(btn_frame, text=self.translate('con_test'), command=self._test_connection).pack(side='right', padx=5)
    
    def _on_close(self):
        """Вызывается при закрытии окна"""
        if self.callback:
            self.callback()  # Передаем обновленные настройки
        self.destroy()
    
    def translate(self, key):
        """Получение перевода по ключу"""
        return LANGUAGES[self.language].get(key, key)

    def load_servers_list(self):
        if not os.path.exists(self.servers_path):
            return {}
        try:
            with open(self.servers_path, "r", encoding="utf-8") as file:
                self.servers_list = json.load(file)
        except Exception as e:
            print(f"Error with servers load: {e}")
            return None 
        self.update_servers_list()       

    def update_servers_list(self):
        for item in self.servers_tree.get_children():
            self.servers_tree.delete(item)
        for name in self.servers_list:
            self.servers_tree.insert('', 'end', text=name)

    def _add_server(self):
        """Добавляет новый сервер"""
        new_name = self.entries['conn_name'].get()
        adress = self.entries['adress'].get()
        login = self.entries['login'].get()
        password = self.entries['pass'].get()
        if new_name in self.servers_list:
            messagebox.showerror("Error", self.translate('serv_already'))
            return
        if not new_name or not adress:
            messagebox.showwarning(self.translate('err'), "Отсутствует имя или адрес!")
        self.servers_list[new_name] = {
            'adress': adress,
            'login': login,
            'pass': password
        }
        self.servers_tree.insert('', 'end', text=new_name)
        self.save_servers()
        self.update_servers_list()

    def save_servers(self):
        with open(self.servers_path, 'w', encoding='utf-8') as file:
            json.dump(self.servers_list, file, indent=4)
    
    def _delete_server(self):
        """Удаляет выбранный сервер"""
        selected = self.servers_tree.selection()
        if not selected:
            messagebox.showwarning(self.translate('err'), "Сервер не выбран!")            
        server_name = self.servers_tree.item(selected[0], 'text')
        if messagebox.askyesno(self.translate('confirm'), f"{self.translate('sel_serv')} '{server_name}'?"):
            self.servers_tree.delete(selected[0])
            del self.servers_list[server_name]
        self.save_servers()
        self.update_servers_list()
    
    def _on_server_selected(self, event):
        """Загружает данные выбранного сервера в форму"""
        selected = self.servers_tree.selection()
        if not selected:
            return
            
        self.selected_server = self.servers_tree.item(selected[0], 'text')
        settings = self.servers_list.get(self.selected_server, {})
        
        for name, entry in self.entries.items():
            if name == 'conn_name':
                entry.set_text(self.selected_server)
                continue
            entry.set_text(settings.get(name, ""))
    
    def _save_settings(self):
        """Сохраняет изменения сервера"""
        if not self.selected_server:
            messagebox.showwarning(self.translate('err'), "Сервер не выбран!")
            return
            
        new_settings = {
            'adress': self.entries['adress'].get(),
            'login': self.entries['login'].get(),
            'pass': self.entries['pass'].get()
        }
        
        self.servers_list[self.selected_server] = new_settings
    
    def _test_connection(self):
        """Тестирует подключение"""        
        try:
            # Получаем текущие настройки из формы
            adress = self.entries['adress'].get()
            if not adress:
                messagebox.showerror(self.translate('err'), "Не указан адрес!")
                return
            user = 'admin'
            ftp = FTP(timeout=5)
            ftp.connect(adress)
            pas = ''
            ftp.login(user, pas)

            try:
                files = []
                ftp.retrlines('LIST', files.append)
                messagebox.showinfo(
                    self.translate('success'), 
                    f"Подключение успешно!\nНайдено {len(files)} файлов в корневой директории."
                )
            except Exception as e:
                messagebox.showinfo(
                    self.translate('success'), 
                    f"Подключение установлено, но не удалось получить список файлов:\n{str(e)}"
                )
            
            # Закрываем соединение
            ftp.quit()
            
        except socket.timeout:
            messagebox.showerror(
                self.translate('err'), 
                "Таймаут подключения. Проверьте адрес сервера и сетевые настройки."
            )
        except Exception as e:
            messagebox.showerror(
                self.translate('err'), 
                f"Не удалось подключиться:\n{str(e)}"
            )