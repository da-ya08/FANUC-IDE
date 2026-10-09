import tkinter as tk, os, json, shutil, subprocess, sys, configparser
from tkinter.ttk import Progressbar, Combobox, Treeview, Button, Scrollbar, Label, Entry
from tkinter import filedialog, messagebox, Menu, simpledialog
from src.ftp_settings import  FTPSettingsWindow
from src.ls_settings import LSSettingsWindow
from src.conf import LANGUAGES, CURRENT_LANGUAGE, SINTAX_WORDS
from ftplib import FTP
from threading import Thread
from datetime import datetime

class FANUCE_IDE:
    def __init__(self, root):
        self.files_queue = []
        self.buffer_header, self.buffer_asser, self.target_server_name, self.CURRENT_FILE = '', '', '', ''
        self.target_server, self.all_servers, self.ls_info = {}, {}, {}
        self.del_stoppers = [' ', ',', '.', '!', '?', ';', ':', '-', '(', ')', '\\', '/', '=']
        self.keywords = SINTAX_WORDS['keywords']
        self.logic = SINTAX_WORDS['logic']
        self.data = SINTAX_WORDS['data']
        self.point = SINTAX_WORDS['point']
        self.filter_server_files = tk.IntVar(value=1)
        self.is_modified = False
        self.is_karel = False
        self.is_temp = False
        self.backuping = False
        self.language = 'en'
        self.cache_folder = f'{os.environ['LOCALAPPDATA']}\\FANUC-IDE'
        self.SERVERS_FILE = f'{self.cache_folder}\\servers_list.json'

        self.root = root
        self.root.title('FANUC IDE')
        self.root.minsize(width=600, height=400) 
        self.PROJECT_DIRICTORY = '\\'.join(__file__.split('\\')[:-1])
        self.CURRENT_DIRICTORY = self.PROJECT_DIRICTORY
        os.chdir(self.PROJECT_DIRICTORY)
        self.root.iconbitmap(f'{self.PROJECT_DIRICTORY}\\resources\\icon.ico')
        if not os.path.exists(f'{self.cache_folder}\\cache.json'):
            self._create_config_file()
        with open(f'{self.cache_folder}\\cache.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.CURRENT_DIRICTORY = data['path']
            self.language = data['lang']
            self.root.geometry(data['geo'])
        self.check_robot_ini(self.cache_folder, self.PROJECT_DIRICTORY)

        ''' Главное окно '''
        toolbar = tk.Frame(self.root, height=20)
        toolbar.pack(side='top', fill='x')

        self.status_frame = tk.Frame(self.root, height=20, borderwidth=1, relief='groove')
        self.status_frame.pack(side='bottom', fill='x')
        self.status_label = tk.Label(self.status_frame)
        self.status_label.pack(side='left', fill='x')
        self.download_progress_bar = Progressbar(self.status_frame, orient='horizontal', length=150)
        self.show_info(text='DA_YA product')

        main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=4)
        main_paned.pack(expand=True, fill='both')

        left_paned = tk.PanedWindow(main_paned, orient=tk.VERTICAL, sashrelief=tk.RAISED, sashwidth=4)
        main_paned.add(left_paned, minsize=220)
        right_frame = tk.Frame(main_paned)  
        main_paned.add(right_frame)

        '''Левая часть'''
        # Меню-бар
        servers_menubar = tk.Frame(left_paned, height=20)
        left_paned.add(servers_menubar, minsize=20)
        tk.Label(servers_menubar, text=f'{self.translate('robot')}:').pack(side=tk.LEFT, expand=False, padx=2)
        self.server_combobox = Combobox(servers_menubar, state='readonly')
        self.server_combobox.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        self.server_combobox.bind('<<ComboboxSelected>>', self._on_server_selected)
        self.ftp_settings_but = Button(servers_menubar, width=4, text='⚙', command=self.show_ftp_settings)
        self.ftp_settings_but.pack(side=tk.RIGHT, padx=2, expand=False)
        files_paned = tk.PanedWindow(left_paned, orient=tk.VERTICAL, sashrelief=tk.RAISED)
        left_paned.add(files_paned, minsize=100)  # Основная область с разделителем
        # Панель файлового дерева
        file_tree_frame = tk.Frame(files_paned)
        file_tree_frame.pack(expand=True, fill='both')
        tree_scroll = Scrollbar(file_tree_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_tree = Treeview(
            file_tree_frame,
            yscrollcommand=tree_scroll.set,
            show='tree',
            selectmode='browse'
        )
        self.file_tree.pack(expand=True, fill='both', padx=2, pady=2)
        tree_scroll.config(command=self.file_tree.yview)
        self.file_tree.bind('<Double-1>', self._temp_open_file)
        files_paned.add(file_tree_frame, minsize=100)
        # Локальные файлы        
        local_file_tree_frame = tk.Frame(files_paned)
        local_file_tree_frame.pack(expand=True, fill='both')
        self.local_nav_frame = tk.Frame(local_file_tree_frame)
        self.local_nav_frame.pack(fill='x')

        self.local_path_label = Label(self.local_nav_frame, text=self.CURRENT_DIRICTORY)
        self.local_path_label.pack(side='left', fill='x', expand=True)
        local_tree_scroll = Scrollbar(local_file_tree_frame)
        local_tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.local_file_tree = Treeview(
            local_file_tree_frame,
            yscrollcommand=local_tree_scroll.set,
            show='tree',
            selectmode='browse'
        )
        self.local_file_tree.pack(expand=True, fill='both', padx=2, pady=2)
        local_tree_scroll.config(command=self.local_file_tree.yview)
        self.local_file_tree.bind('<Double-1>', self._on_local_file_double_click)
        files_paned.add(local_file_tree_frame, minsize=100)
        self.file_tree.tag_configure('folder', foreground='blue')
        self.file_tree.tag_configure('file', foreground='black')
        self.local_file_tree.tag_configure('back', foreground='#000000')
        self.local_file_tree.tag_configure('folder', foreground='#303030')
        self.local_file_tree.tag_configure('file', foreground='#424242')

        '''Правая часть'''
        # Меню кода
        menu_code_frame = tk.Frame(right_frame, height=20)
        menu_code_frame.pack(side=tk.TOP, fill=tk.X)
        self.CURRENT_FILE_path_menubar = tk.Label(
            menu_code_frame, 
            justify='left', 
            font=('Calibri', 10), 
            cursor='arrow', 
            text=self.translate('menubar_code')
        )
        self.CURRENT_FILE_path_menubar.pack(side=tk.LEFT, fill=tk.X)
        search_button = Button(menu_code_frame,
                                      text='🔎',
                                      width=5)
        search_button.pack(fill='none', side='right')

        # Область кода
        code_frame = tk.Frame(right_frame)
        code_frame.pack(expand=True, fill='both')
        self.scrollbarY = tk.Scrollbar(code_frame)
        self.text_area = tk.Text(
            code_frame, 
            yscrollcommand=self.scrollbarY.set,
            wrap=tk.NONE, 
            pady=2,
            font=('Consolas', 12),
            width=80, 
            height=25,
            state='disabled'
        )
        self.search_bar = SearchBar(self.text_area, self.translate, self)
        search_button.config(command=self.search_bar.show)
        self.line_numbers = tk.Text(
            code_frame,
            width=4,
            padx=3,
            pady=2,
            takefocus=0,
            border=0,
            font=('Consolas', 12),
            background='lightgray',
            foreground='gray',
            state='disabled'
        )
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        self.scrollbarY.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_area.pack(side=tk.LEFT, expand=True, fill='both')

        # Toolbar
        t_toolbar = tk.Frame(toolbar, height=20)
        t_toolbar.pack(side='left', fill='x')
        self.new_file_button = Button(t_toolbar,
                                      text=f'📃{self.translate('new')}',
                                      command=self.new_file)
        self.new_file_button.pack(fill='none', side='left')
        self.open_button = Button(t_toolbar,
                                      text=f'📁{self.translate('open')}',
                                      command=self.open_file)
        self.open_button.pack(fill='none', side='left')
        self.toolbar_save_button = Button(t_toolbar,
                                      text=f'💾{self.translate('save')}',
                                      command=self.save_file)
        self.toolbar_save_button.pack(fill='none', side='left')
        tk.Frame(t_toolbar, background='gray', width=2, height=20).pack(fill='none', side='left')
        self.toolbar_send_button = Button(t_toolbar,
                                      text=f'📤{self.translate('send')}',
                                      command=self.send_file,
                                      state='disable')
        self.toolbar_send_button.pack(fill='none', side='left')
        self.toolbar_compile_button = Button(t_toolbar,
                                      text=f'🛠{self.translate('compile')}',
                                      command=self.copmile_karel,
                                      state='disable')
        self.toolbar_compile_button.pack(fill='none', side='left')
        
        tr_toolbar = tk.Frame(toolbar, height=20)
        tr_toolbar.pack(side='right', fill='x')
        tk.Frame(tr_toolbar, background='gray', width=2, height=20).pack(fill='none', side='left')
        self.toolbar_backup_button = Button(tr_toolbar,
                                                text=f'🗃{self.translate('r_backup')}',
                                                command=self.robot_backup,
                                                state='enable')
        self.toolbar_backup_button.pack(fill='none', side='right')

        self.text_area.bind('<KeyPress>', self.new_input)
        self.text_area.bind('<KeyRelease>', self.update_line_numbers)
        # Настраиваем тег для подсветки
        self.text_area.tag_config('comments',
                                  foreground='black',      # цвет текста
                                  background='#f0ff6a',        # цвет фона
                                  font=('Consolas', 10, 'italic'))  # шрифт
        self.text_area.tag_configure('keywords', foreground='#FA8A0B', font=('bold'))
        self.text_area.tag_configure('logic', foreground='#BA7AC7', font=('bold'))
        self.text_area.tag_configure('ON', foreground='#00c020', font=('bold'))
        self.text_area.tag_configure('OFF', foreground='#910000', font=('bold'))
        self.text_area.tag_configure('data', foreground='#278fb8')
        self.text_area.tag_configure('point', foreground='#3337ff')
        self.root.protocol('WM_DELETE_WINDOW', self.on_close)  # Обработка закрытия окна
        # Настройка прокрутки
        self.text_area.config(yscrollcommand=self.sync_scroll)
        self.line_numbers.config(yscrollcommand=self.sync_scroll)
        self.scrollbarY.config(command=self.on_scrollbar_y)
        self.update_local_files()
        self.update_server_list()
        self.create_menu()
        self._setup_context_menus()
        if len(sys.argv) > 1:
            self.open_file(sys.argv[1])


    def highlight_code(self, event=None, find=''):
        # Удаляем все теги подсветки
        self.text_area.tag_remove('comments', "1.0", tk.END)
        self.text_area.tag_remove('search', "1.0", tk.END)
        self.text_area.tag_remove('sel', "1.0", tk.END)
        self.text_area.tag_remove('keywords', "1.0", tk.END)
        self.text_area.tag_remove('logic', "1.0", tk.END)
        self.text_area.tag_remove('data', "1.0", tk.END)
        self.text_area.tag_remove('point', "1.0", tk.END)
        self.text_area.tag_remove('ON', "1.0", tk.END)
        self.text_area.tag_remove('OFF', "1.0", tk.END)
        # Получаем весь текст
        content = self.text_area.get("1.0", tk.END)
        lines = content.splitlines()
        for line_num, line in enumerate(lines, start=1):
            for word in self.keywords:
                if word in line:
                    start = f'{line_num}.{line.index(word)}'
                    end = f'{start}+{len(word)}c'
                    self.text_area.tag_add("keywords", start, end)
            for word in self.logic:
                if word in line:
                    start = f'{line_num}.{line.index(word)}'
                    end = f'{start}+{len(word)}c'
                    self.text_area.tag_add("logic", start, end)
            for word in self.point:
                if word in line and line.index(word) <= 2:
                    start = f'{line_num}.{line.index(word)}'
                    end = f'{start}+{len(word)}c'
                    self.text_area.tag_add("point", start, end)
            if '=ON' in line:
                start = f'{line_num}.{line.index('=ON')+1}'
                end = f'{start}+{len('=ON')-1}c'
                self.text_area.tag_add("ON", start, end)
            if '=OFF' in line:
                start = f'{line_num}.{line.index('=OFF')+1}'
                end = f'{start}+{len('=OFF')-1}c'
                self.text_area.tag_add("OFF", start, end)
            if '!' in line and line.index('!') < 3:
                # Координаты начала и конца строки
                start = f"{line_num}.{line.index('!')}"
                end = f"{line_num}.{len(line)}"
                # Применяем тег к строке
                self.text_area.tag_add("comments", start, end)
        if find:
            start = '1.0'
            count = 0
            while True:
                pos = self.text_area.search(find, start, stopindex='end', nocase=True)
                if not pos:
                    break
                # Вычисляем конец найденного фрагмента
                end = f"{pos}+{len(find)}c"
                self.text_area.tag_remove('comments', pos, end)
                self.text_area.tag_add('search', pos, end)
                start = end
                count += 1
    
    def create_menu(self):
        menubar = tk.Menu(self.root)
        edit_menu = tk.Menu(menubar, tearoff=0)
        # Меню "Файл"
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label=self.translate('new'), command=self.new_file)
        file_menu.add_command(label=self.translate('open'), command=self.open_file)
        file_menu.add_separator()
        file_menu.add_command(label=self.translate('save'), command=self.save_file, state=tk.DISABLED)
        file_menu.add_command(label=self.translate('save_as'), command=self.save_file_as)
        file_menu.add_command(label=self.translate('change_dir'), command=self._change_def_dir)
        file_menu.add_separator()
        file_menu.add_command(label=self.translate('exit'), command=self.on_close)
        menubar.add_cascade(label=self.translate('file'), menu=file_menu)
        # LS
        ls_menu = tk.Menu(edit_menu, tearoff=0)
        ls_menu.add_command(label=self.translate('config_file'), command=self.open_ls_settings)
        # KL
        kl_menu = tk.Menu(edit_menu, tearoff=0)
        kl_menu.add_command(label=self.translate('compile'), command=self.copmile_karel)
        # Редактировать
        edit_menu.add_cascade(label='LS', state='disabled', menu=ls_menu)
        edit_menu.add_cascade(label='KL', state='disabled', menu=kl_menu)
        menubar.add_cascade(label=self.translate('edit_m'), menu=edit_menu)
        # Робот
        robot_menu = tk.Menu(menubar, tearoff=0)
        robot_menu.add_command(label=self.translate('r_backup'), command=self.robot_backup)
        menubar.add_cascade(label=self.translate('robot'), menu=robot_menu)
        # Язык
        lang_menu = tk.Menu(menubar, tearoff=0)
        lang_menu.add_command(label="English", command=lambda: self.set_language('en'))
        lang_menu.add_command(label="Русский", command=lambda: self.set_language('ru'))
        menubar.add_cascade(label=self.translate('lang_menu'), menu=lang_menu)
        self.root.config(menu=menubar)
        self.file_menu = file_menu
        self.edit_menu = edit_menu
        self.new_file_button.config(text=f'📃{self.translate('new')}')
        self.open_button.config(text=f'📁{self.translate('open')}')
        self.toolbar_send_button.config(text=f'📤{self.translate('send')}')
    
    def _setup_context_menus(self):
        self._add_text_context_menu(self.text_area)
        self._add_tree_context_menu(self.file_tree)
        self._add_local_tree_context_menu(self.local_file_tree)

    def _add_text_context_menu(self, text_widget):
        """Добавляет контекстное меню для Text виджетов"""
        menu = Menu(text_widget, tearoff=0)
        menu.add_command(label=self.translate('copy'), command=lambda: text_widget.event_generate("<<Copy>>"))
        menu.add_command(label=self.translate('paste'), command=lambda: text_widget.event_generate("<<Paste>>"))
        menu.add_command(label=self.translate('cut'), command=lambda: text_widget.event_generate("<<Cut>>"))
        menu.add_separator()
        menu.add_command(label=self.translate('select_all'), 
                       command=lambda: text_widget.tag_add("sel", "1.0", "end"))

        # Привязка к правой кнопке мыши
        text_widget.bind('<Button-3>', lambda e: menu.tk_popup(e.x_root, e.y_root))

        # Добавляем горячие клавиши
        text_widget.bind('<Control-c>', lambda e: text_widget.event_generate("<<Copy>>"))
        text_widget.bind('<Control-x>', lambda e: text_widget.event_generate("<<Cut>>"))
        text_widget.bind('<Control-a>', lambda e: text_widget.tag_add("sel", "1.0", "end"))
        text_widget.bind('<Control-s>', self.save_file)
    
    def _add_tree_context_menu(self, widget):
        menu = Menu(widget, tearoff=0)
        menu.add_command(label=self.translate('open'), command=self._temp_open_file)
        menu.add_command(label=self.translate('dnld'), command=self._download_and_open_file)
        menu.add_command(label=self.translate('del'), command=self._delete_selected_file)
        menu.add_separator()
        menu.add_command(label=self.translate('refresh'), command=self.refresh_file_list)
        menu.add_checkbutton(label=self.translate('filter'), command=self.refresh_file_list, variable=self.filter_server_files)
        widget.bind('<Button-3>', lambda e: menu.tk_popup(e.x_root, e.y_root))
    
    def _add_local_tree_context_menu(self, widget):
        menu = Menu(widget, tearoff=0)
        menu.add_command(label=self.translate('open'), command=self._on_local_file_double_click)
        menu.add_command(label=self.translate('send'), command=self._send_local_file)
        menu.add_command(label=self.translate('del'), command=self._delete_selected_local_file)
        menu.add_separator()
        menu.add_command(label=self.translate('open_folder'), command=self._open_local_folder)
        menu.add_command(label=self.translate('create_folder'), command=self._create_folder)
        menu.add_command(label=self.translate('refresh'), command=self.update_local_files)
        widget.bind('<Button-3>', lambda e: menu.tk_popup(e.x_root, e.y_root))
    
    def robot_backup(self, event=''):
        """Создание резервной копии робота"""
        selected_name = self.server_combobox.get()
        if not selected_name:
            self.show_info(self.translate('no_select_server'), 1, True)
            return
        selected_dir = filedialog.askdirectory(title='Backup папка',
                                               initialdir=self.CURRENT_DIRICTORY).replace('/', '\\')
        if not selected_dir:
            return
        selected_dir = selected_dir+f'\\{selected_name}_{datetime.now().strftime('%d%m%Y_%H%M')}\\'
        target_server = self.all_servers[selected_name]
        self.download_progress_bar.pack(fill='none', side='right')
        self.root.after(100, self.tread_service)
        self.backuping = True
        tread = Thread(target=self.tread_backup,
                       args=(target_server, selected_dir),
                       daemon=True)
        tread.start()
        

    def tread_backup(self, server, dir):
        total_files = 0
        fact_files = 0
        ftp = FTP(timeout=5, encoding='cp1251')
        try:
            ftp.connect(server['adress'])
            login = server['login'] if server['login'] else 'admin'
            ftp.login(login, server['pass'])
            files = ftp.nlst()
            extensions = ['.va']  # NEНужные расширения
            files = [f for f in files if any(not f.lower().endswith(ext) for ext in extensions)]
            os.makedirs(os.path.dirname(dir))
            total_files = len(files)
            for file in files:
                try:
                    if file[-1:-3:-1].lower() == 'av':
                        continue
                    with open(f'{dir}\\{file}', 'wb+') as f:
                        ftp.retrbinary(f"RETR {file}", f.write)
                        fact_files += 1
                    self.files_queue.append(f'{self.translate('downloaded')}{fact_files}/{total_files}')
                    self.download_progress_bar.config(value=fact_files/total_files*100)
                except Exception as e:
                    self.show_info(f'{self.translate('connection_error')}: {e}', 2, True)
        except Exception as e:
            self.show_info(f'{self.translate('connection_error')}: {e}', 2, True)
            ftp.quit()
            return
        ftp.quit()
        self.show_info(f'{self.translate('downloaded')}{fact_files}/{total_files}', 0, True)
        self.download_progress_bar.pack_forget()
        self.download_progress_bar.config(value=0)
        self.files_queue = []
        self.backuping = False
    
    def _change_def_dir(self):
        while True:
            selected_dir = filedialog.askdirectory(title="Выберите папку для проектов",
                                                   initialdir='\\'.join(self.PROJECT_DIRICTORY.split('\\')[:-1]))
            if not selected_dir:  # Пользователь отменил выбор
                return
            try:
                self.CURRENT_DIRICTORY = selected_dir.replace('/', '\\')
                self._save_settings(self.CURRENT_DIRICTORY)
                self._open_local_folder(self.CURRENT_DIRICTORY)
                break
            except Exception as e:
                self.show_info(self.translate('cant_save_here'), 1, True)
                
    def _create_config_file(self):
        while True:
            selected_dir = filedialog.askdirectory(title="Выберите папку для проектов",
                                                   initialdir='\\'.join(self.PROJECT_DIRICTORY.split('\\')[:-1]))
            if not selected_dir:  # Пользователь отменил выбор
                try:
                    if self.CURRENT_DIRICTORY:
                        break
                except:
                    pass
                response = messagebox.askquestion("Выход",
                                                  "Папка не выбрана. Выйти из программы?",
                                                  icon='warning')
                if response == 'yes':
                    self.on_close()
                    exit()
                else:
                    continue
            try:
                selected_dir = selected_dir.replace('/', '\\')
                test_file = os.path.join(selected_dir, 'test_write.tmp')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                os.makedirs(f'{self.cache_folder}', exist_ok=True)
                with open(f'{self.cache_folder}\\cache.json', 'w', encoding='utf-8') as f:
                    json.dump({'path': selected_dir, 
                               'lang': CURRENT_LANGUAGE,
                               'geo': '650x750'},
                                f)
                break
            except Exception as e:
                messagebox.showerror(self.translate('err'),
                                     f"Невозможно записать в выбранную папку:\n{str(e)}\n\nВыберите другую папку.")    

    def _save_settings(self, new_path=''):
        with open(f'{self.cache_folder}\\cache.json', 'r+', encoding='utf-8') as f:
            temp_path = new_path if new_path else json.load(f)['path']
            f.seek(0)
            f.truncate()
            json.dump({'path': temp_path, 
                       'lang': self.language,
                       'geo': f'{self.root.geometry()}'}, 
                       f)

    def copmile_karel(self):
        if not self.CURRENT_FILE:
            return
        self.save_file()
        try:
            os.chdir('\\'.join(self.CURRENT_FILE.split('\\')[:-1]))
            result = subprocess.run(
                [f'{self.PROJECT_DIRICTORY}\\src\\ktrans.exe', f'{self.CURRENT_FILE}', '/config' , f'{self.cache_folder}\\robot.ini'],
                capture_output=True,
                text=True,
                check=True)
            self.show_info(self.translate('compile_success'))
            messagebox.showinfo(self.translate('compile_success'),
                                result.stdout)
            self.update_local_files()
            self.toolbar_compile_button.config(text=self.translate('compiled'))
            self.toolbar_compile_button.config(state='disable')
            self.toolbar_send_button.config(state='enable')
        except Exception as e:
            messagebox.showerror(self.translate('compilation_error'),
                                 e.stdout) # type: ignore
            self.toolbar_send_button.config(state='disable')
        os.chdir(self.PROJECT_DIRICTORY)
    
    def show_info(self, text:str, lvl=0, need_message=False):
        """Show message
        
        :param text (str): text of message
        :param lvl (int): level of message
            =0: INFO
            =1: WARNING
            =2: ERROR
        :param need_message (bool): need show window?
        :return bool: True if writing is successful, False otherwise
        """
        levels = ['INFO:', 'WARN:', 'ERROR:']
        self.status_label.config(text=f'{levels[lvl]} {text}')
        if lvl == 0 and need_message:
            messagebox.showinfo(levels[lvl], text)
        elif lvl == 1 and need_message:
            messagebox.showwarning(levels[lvl], text)
        elif lvl == 2 and need_message:
            messagebox.showerror(levels[lvl], text)
    
    def send_file(self, file=''):
        if not self.target_server_name:
            self.show_info(self.translate('no_select_server'), need_message=True)
            return
        if not self.CURRENT_FILE and not file:
            self.show_info(self.translate('no_file'), need_message=True)
            return
        tmp_path = file if file else self.CURRENT_FILE
        tmp_path = tmp_path.replace('/', '\\')
        if tmp_path.split('\\')[-1].split('.')[-1].lower() == 'kl':
            tmp_path = f'{tmp_path[:-2]}pc'
        if os.path.isdir(tmp_path):
            self.show_info(self.translate('cant_send_folder'), 1, True)
            return
        if not messagebox.askyesno(self.translate('send_confirm'),
                                   f'{self.translate('u_sure_to_send')}: {tmp_path}\n{self.translate('to_server')}: {self.target_server_name}?',
                                   icon='question'):
            return
        ftp = FTP(timeout=7, encoding='cp1251')
        try:
            ftp.connect(self.target_server['adress'])
            log = self.target_server['login'] if self.target_server['login'] else 'admin'
            ftp.login(log, self.target_server['pass'])
            ftp.voidcmd('TYPE I')
            with open(tmp_path, 'rb') as s_file:
                if not self.is_karel and tmp_path == self.CURRENT_FILE:
                    ftp.storbinary(f'STOR {self.ls_info['name'].lower()}.ls', s_file)
                else:
                    ftp.storbinary(f'STOR {tmp_path.split('\\')[-1]}', s_file) 
            self.refresh_file_list()
            self.show_info(f'{self.translate('sending_file')} {tmp_path.split('\\')[-1]} {self.translate('was_success')}!')
        except Exception as e:
            try:
                ftp = FTP(timeout=7, encoding='cp1251')
                ftp.connect(self.target_server['adress'])
                log = self.target_server['login'] if self.target_server['login'] else 'admin'
                ftp.login(log, self.target_server['pass'])
                ftp.voidcmd('TYPE I')
                with open(tmp_path, 'rb') as s_file:
                    if not self.is_karel and tmp_path == self.CURRENT_FILE:
                        ftp.storbinary(f'STOR {self.ls_info['name'].lower()}.ls', s_file)
                    else:
                        ftp.storbinary(f'STOR {tmp_path.split('\\')[-1]}', s_file) 
                self.refresh_file_list()
                self.show_info(f'{self.translate('sending_file')} {tmp_path.split('\\')[-1]} {self.translate('was_success')}!')
            except:
                self.show_info(f'{self.translate('couldnt_send_file')}: {e}', 2, True)
        ftp.quit()

    def _local_nav_back(self):
        """Переходит в родительскую папку для локальных файлов"""
        parent = os.path.dirname(self.CURRENT_DIRICTORY.rstrip('/\\'))
        if os.path.exists(parent):
            self.CURRENT_DIRICTORY = parent
            self.update_local_files()
            self.local_path_label.config(text=self.CURRENT_DIRICTORY)
            self.CURRENT_DIRICTORY = parent
        
    def check_robot_ini(self, cache_dir, project_dir):
        if not os.path.exists(f'{self.cache_folder}\\robot.ini'):
            self._create_robot_ini(cache_dir, project_dir)
        else:
            try:
                config = configparser.ConfigParser()
                config.read(f'{self.cache_folder}\\robot.ini')
                path = config["WinOLPC_Util"]["Robot"]
                if not self.PROJECT_DIRICTORY in path:
                    self._create_robot_ini(cache_dir, project_dir)
            except:
                self._create_robot_ini(cache_dir, project_dir)

    def _create_robot_ini(self, cache_dir, project_dir):
        with open(f'{cache_dir}\\robot.ini', 'w', encoding='utf-8') as f:
            f.write('[WinOLPC_Util]\n')
            f.write(f'Robot={project_dir}\\resources\\Robot_1\n')
            f.write('Version=V9.10-1\n')
            f.write(f'Path={project_dir}\\resources\\V910-1\\bin\n')
            f.write(f'Support={project_dir}\\resources\\Robot_1\\support\n')
            f.write(f'Output={project_dir}\\resources\\Robot_1\\output\n')
    
    def _open_local_folder(self, l_path=''):
        open_folder = l_path if l_path else filedialog.askdirectory(title=self.translate('choice_folder'),
                                              initialdir=self.CURRENT_DIRICTORY)
        if not open_folder:
            return
        self.CURRENT_DIRICTORY = open_folder
        self.update_local_files()
    
    def _create_folder(self):
        while True:
            folder_name = simpledialog.askstring(f'{self.translate('folder_name')}:',
                                                 f'{self.translate('enter_folder_name')}: ',
                                                 initialvalue='folder1')
            if folder_name is None:
                return
            if not folder_name.strip():
                self.show_info(self.translate('name_empty'), 1, True)
                continue
            try:
                os.makedirs(f'{self.CURRENT_DIRICTORY}\\{folder_name}')
            except Exception as e:
                self.show_info(f'{self.translate('cant_create_folder')}{e}', 1, True)
            self.update_local_files()
            break

    def _delete_selected_local_file(self):
        try:
            item = self.local_file_tree.selection()[0]
        except Exception as e:
            self.show_info(self.translate('no_selected_file'), 1, True)
            return
        if item:
            file = self.CURRENT_DIRICTORY + '\\' + self.local_file_tree.item(item, 'text')
            if not messagebox.askyesno('Подтверждение',
                                       f'Удалить файл: {file}?',
                                       icon='warning'):
                return
            if os.path.isdir(file):
                try:
                    os.rmdir(file)
                except:
                    shutil.rmtree(file)
            else:
                os.remove(file)
        self.update_local_files()


    def _send_local_file(self):
        item = self.local_file_tree.selection()[0]
        if item:
            name = self.local_file_tree.item(item, 'text')
            self.send_file(f'{self.CURRENT_DIRICTORY}\\{name}')

    def _delete_selected_file(self):
        selected = self.file_tree.selection()
        if not selected:
            return
        filename = self.file_tree.item(selected[0], 'text')
        if messagebox.askyesno("Подтверждение", 
                               f"Вы точно хотите удалить файл {filename}\nС сервера: {self.target_server_name}?",
                               icon='warning'):
            ftp = FTP(timeout=5, encoding='cp1251')
            try:
                ftp.connect(self.target_server['adress'])
                login = self.target_server['login'] if self.target_server['login'] else 'admin'
                ftp.login(login, self.target_server['pass'])
                ftp.delete(filename)
                self.file_tree.delete(selected[0])

            except Exception as e:
                messagebox.showerror("Error", f"Не удалось удалить файл: {e}")
            ftp.quit()

    def refresh_file_list(self):
        self._on_server_selected()
    
    def _on_server_selected(self, event=''):
        """Обрабатывает выбор сервера в Combobox"""
        selected_name = self.server_combobox.get()
        self.target_server_name = selected_name
        if selected_name in self.all_servers:
            self.target_server = self.all_servers[selected_name]
            try:
                ftp = FTP(timeout=5, encoding='cp1251')
                ftp.connect(self.target_server['adress'])
                login = self.target_server['login'] if self.target_server['login'] else 'admin'
                ftp.login(login, self.target_server['pass'])
                files = ftp.nlst()
                if self.filter_server_files.get():
                    extensions = ['.kl', '.ls']  # Нужные расширения
                    files_ = [f for f in files if any(f.lower().endswith(ext) for ext in extensions)]
                else:
                    files_ = files
            except Exception as e:
                self.show_info(f'{self.translate('connection_error')}: {e}', 2, True)
                return
            for item in self.file_tree.get_children():
                self.file_tree.delete(item)
            for name in files_:
                self.file_tree.insert('', 'end', text=name)
            self.show_info(f'{self.translate('con_success')}: {selected_name} - {len(files)} {self.translate('files')}')
            ftp.quit()
    
    def update_server_list(self):
        if hasattr(self, 'server_combobox'):
            if not os.path.exists(self.SERVERS_FILE):
                with open(self.SERVERS_FILE, 'w', encoding='utf-8') as file:
                    return
            try:
                with open(self.SERVERS_FILE, 'r', encoding='utf-8') as file:
                    self.all_servers = json.load(file)
            except Exception as e:
                if 'Expecting value' in str(e):
                    return
                self.show_info(f'{self.translate('cant_load_list')}{e}', 2, True)
                return None 
            self.server_combobox['values'] = list(self.all_servers.keys())
    
    def update_local_files(self, path=None):
        """Обновляет список локальных файлов и папок"""
        if path is None:
            path = self.CURRENT_DIRICTORY
        for item in self.local_file_tree.get_children():
            self.local_file_tree.delete(item)
        self.local_file_tree.insert('', 'end', text='<—', tags=('back',))
        try:
            items = os.listdir(path)
            # Сначала добавляем папки, потом файлы
            for name in sorted(items, key=lambda x: not os.path.isdir(os.path.join(path, x))):
                full_path = os.path.join(path, name)
                if os.path.isdir(full_path):
                    self.local_file_tree.insert('', 'end', text=f'📂{name}', values=[full_path], tags=('folder',))
                else:
                    self.local_file_tree.insert('', 'end', text=f'📃{name}', values=[full_path], tags=('file',))
        except Exception as e:
            self.show_info('Не удалось открыть папку проектов.\nВыберите новую папку:', 1, True)
            self._change_def_dir()
    
    def _on_local_file_double_click(self, event=None):
        """Обрабатывает двойной клик по локальным файлам/папкам"""
        selected = self.local_file_tree.selection()
        if not selected:
            return
        item = selected[0]
        name = self.local_file_tree.item(item, 'text')
        if name == '<—':
            self._local_nav_back()
            return
        full_path = self.local_file_tree.item(item, 'values')[0]
        if os.path.isdir(full_path):
            # Если это папка - заходим в нее
            self.CURRENT_DIRICTORY = os.path.abspath(full_path)
            self.CURRENT_DIRICTORY = full_path
            self.update_local_files(full_path)
            self.local_path_label.config(text=self.CURRENT_DIRICTORY)
        else:
            # Если это файл - открываем его
            if self.CURRENT_FILE == full_path:
                return
            self.open_file(full_path)
            self.is_temp = False
            if not self.is_karel:
                self.toolbar_send_button.config(state='enable')
        
    def _temp_open_file(self, event=None):
        item = self.file_tree.selection()[0]
        if item:
            ftp = FTP(timeout=5, encoding='cp1251')
            ftp.connect(self.target_server['adress'])
            login = self.target_server['login'] if self.target_server['login'] else 'admin'
            ftp.login(login, self.target_server['pass'])
            filename = self.file_tree.item(item, 'text')
            t_filename = f'{self.cache_folder}\\[TEMP_FILE] {filename}'
            with open(t_filename, 'wb+') as f:
                ftp.retrbinary(f"RETR {filename}", f.write)
            self.open_file(t_filename)
            self.update_file_path(custom=f'{self.target_server_name} - {t_filename}', online=1)
            os.remove(t_filename)
            ftp.quit()
            self.is_temp = True

    def _download_and_open_file(self, filename=''):
        if not filename:
            item = self.file_tree.selection()[0]
            if not item:
                return
            filename = self.file_tree.item(item, 'text')
        while True:
            file_path = filedialog.asksaveasfilename(initialdir=f'{self.CURRENT_DIRICTORY}',
                                                     filetypes=[(self.translate('all_files'), "*.*")],
                                                     initialfile=filename,
                                                     title=self.translate('dnld')).replace('/', '\\')
            if not file_path:
                return
            elif file_path:
                break
        ftp = FTP(timeout=5, encoding='cp1251')
        try:
            ftp.connect(self.target_server['adress'])
            login = self.target_server['login'] if self.target_server['login'] else 'admin'
            ftp.login(login, self.target_server['pass'])
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'wb+') as f:
                ftp.retrbinary(f"RETR {filename}", f.write)
            self.open_file(file_path)
        except Exception as e:
            messagebox.showerror(self.translate('err'), f'{self.translate('couldnt_download_file')}: {e}')
        self.update_local_files()
        ftp.quit()
        self.is_temp = False

    def set_language(self, lang_code):
        """Смена языка интерфейса"""
        self.language = lang_code
        # Пересоздаем меню
        self.create_menu()
        self.toolbar_compile_button.config(text=f'🛠{self.translate('compile')}')
        self.toolbar_backup_button.config(text=f'🗃{self.translate('r_backup')}')
        self.toolbar_send_button.config(text=f'📤{self.translate('send')}')
        self.toolbar_save_button.config(text=f'💾{self.translate('save')}')
        if self.search_bar.view:
            self.search_bar.hide()
            self.search_bar.show()
        if not self.CURRENT_FILE:
            self.CURRENT_FILE_path_menubar.config(text=self.translate('menubar_code'))
        self._setup_context_menus()

    def translate(self, key: str):
        """Получение перевода по ключу"""
        return LANGUAGES[self.language].get(key, key)

    def update_file_path(self, custom='', online=0):
        """Обновляет заголовок окна."""
        if custom:
            self.CURRENT_FILE_path_menubar.config(text=custom, background='yellow' if online else '#F2F3F4')
        elif self.CURRENT_FILE and not custom:
            self.CURRENT_FILE_path_menubar.config(text=self.CURRENT_FILE, background='#F2F3F4')

    def new_file(self):
        """Создание нового файла."""
        if self.is_modified:
            response = messagebox.askyesnocancel(self.translate('save_file'),
                                                 self.translate('quest_bef_cls'),
                                                 icon=messagebox.WARNING)
            if response is True:  # Пользователь выбрал "Сохранить"
                self.save_file()
            elif response is False:  # Пользователь выбрал "Не сохранять"
                pass
            else:
                return
        file_path = filedialog.asksaveasfilename(initialdir=self.CURRENT_DIRICTORY,
                                                 defaultextension="new_file.kl",
                                                 filetypes=[("Karel listing", "*.kl"), ("LS program", "*.ls"), (self.translate('all_files'), "*.*")])
        if file_path:
            if file_path[-1:-3:-1].lower() == 'sl':
                self.open_ls_settings()
                if not self.buffer_header:
                    self.buffer_asser = ''
                    return
                self.buffer_asser = '/POS\n/END\n'
                self.edit_menu.entryconfig('LS', state=tk.NORMAL)
                self.edit_menu.entryconfig('KL', state=tk.DISABLED)
                self.toolbar_send_button.config(state='enable')
                self.toolbar_compile_button.config(state='disable')
            elif file_path[-1:-3:-1].lower() == 'kl':
                self.edit_menu.entryconfig('LS', state=tk.DISABLED)
                self.edit_menu.entryconfig('KL', state=tk.NORMAL)
                self.toolbar_send_button.config(state='disable')
                self.toolbar_compile_button.config(state='enable')
            self.CURRENT_FILE: str = file_path
            self._save_to_file(file_path)
            self.update_file_path()  # Обновляем заголовок окна
            self.file_menu.entryconfig(self.translate('save'), state=tk.NORMAL)  # Активируем "Сохранить"
            self.text_area.config(state='normal')
            self.update_local_files()
            self.is_modified = False  # Сбрасываем флаг изменений
            self.text_area.delete("1.0", tk.END)
        else:
            self.update_file_path()
        self.is_temp = False
        
    def open_file(self, file_path=None):
        """Открывает файл и загружает его содержимое в текстовое поле."""
        if not file_path:
            file_path = filedialog.askopenfilename(
                initialdir=f'{self.CURRENT_DIRICTORY}',
                filetypes=[("LS and KAREL", "*.ls *.kl"), (self.translate('all_files'), "*.*")]
            ).replace('/', '\\')
        if self.is_modified:
            response = messagebox.askyesnocancel(
                self.translate('save_file'),
                self.translate('quest_bef_cls'),
                icon=messagebox.WARNING
            )
            if response is True:  # Пользователь выбрал "Сохранить"
                self.save_file()
            elif response is False:  # Пользователь выбрал "Не сохранять"
                pass
            # Если response is None (пользователь выбрал "Отменить"), ничего не делаем
        else:
            pass
        self.text_area.config(state='normal')
        if file_path:
            self.toolbar_send_button.config(state='disable')
            self.toolbar_compile_button.config(state='disable')
            if file_path[-1:-3:-1].lower() == 'sl':
                content = ''
                one_line = ''
                asser = ''
                header_getted = False
                text_getted = False
                try:
                    with open(file_path, "r") as file:
                        one_line = file.readline()
                        if not '/PROG' in one_line:
                            file.seek(0)
                            content = file.read()
                            self.text_area.delete("1.0", tk.END) 
                            self.text_area.insert(tk.END, content)
                            self.CURRENT_FILE = file_path  
                            self.update_file_path() 
                            self.update_line_numbers()
                            self.is_karel = False
                            self.toolbar_send_button.config(state='disable')
                            return
                        if one_line.strip().split()[-1] == 'Macro':
                            self.ls_info['macro'] = True
                            self.ls_info['name'] = one_line.strip().split()[-2]
                        else:
                            self.ls_info['macro'] = False
                            self.ls_info['name'] = one_line.strip().split()[-1]                      
                        while True:
                            one_line = file.readline()
                            if "/MN" in one_line:
                                header_getted = True
                            elif "/POS" in one_line:
                                text_getted = True
                                asser += one_line
                            elif "/END" in one_line:
                                asser += one_line
                                break
                            else:
                                if not header_getted:
                                    if 'OWNER' in one_line:
                                        self.ls_info['owner'] = one_line.strip().split()[-1].replace(';','')
                                    elif 'COMMENT' in one_line:
                                        self.ls_info['comment'] = one_line.split('"')[-2]
                                    elif 'PROTECT' in one_line:
                                        self.ls_info['protect'] = False if 'READ_WRITE' in one_line else True
                                    elif 'DEFAULT_GROUP' in one_line:
                                        self.ls_info['motion'] = True if '1,' in one_line else False
                                elif header_getted and not text_getted:
                                    content += one_line[5:]
                                    continue
                                elif header_getted and text_getted:
                                    asser += one_line
                    self.buffer_asser = asser
                    content = content[:-1]
                    content = content.replace(";", "")
                    self.text_area.delete("1.0", tk.END) 
                    self.text_area.insert(tk.END, content)
                    self.CURRENT_FILE = file_path  
                    self.update_file_path() 
                    self.file_menu.entryconfig(self.translate('save'), state=tk.NORMAL)
                    self.is_modified = False
                    self.update_line_numbers()
                    self.is_karel = False
                    self.edit_menu.entryconfig('LS', state=tk.NORMAL)
                    self.edit_menu.entryconfig('KL', state=tk.DISABLED)
                    self.toolbar_send_button.config(state='enable')
                except Exception as e:
                    self.show_info(f'{self.translate('couldnt_open_file')}: {e}', 2, True)
            elif file_path[-1:-3:-1].lower() == 'lk':
                self.ls_info = {}
                try:
                    with open(file_path, "r", encoding="utf-8") as file:
                        content = file.read()
                        self.text_area.delete("1.0", tk.END) 
                        self.text_area.insert(tk.END, content)
                        self.CURRENT_FILE = file_path 
                        self.update_file_path() 
                        self.file_menu.entryconfig(self.translate('save'), state=tk.NORMAL)
                        self.is_modified = False
                        self.update_line_numbers()
                        self.toolbar_compile_button.config(text=f'🛠{self.translate('compile')}')
                        self.toolbar_compile_button.config(state='enable')
                        self.toolbar_send_button.config(state='disable')
                        self.is_karel = True
                        self.edit_menu.entryconfig('LS', state=tk.DISABLED)
                        self.edit_menu.entryconfig('KL', state=tk.NORMAL)
                except Exception as e:
                    self.show_info(f'{self.translate('couldnt_open_file')}: {e}', 2, True)
            else:
                self.ls_info = {}
                try:
                    with open(file_path, "r", encoding="utf-8") as file:
                        content = file.read()
                        self.text_area.delete("1.0", tk.END) 
                        self.text_area.insert(tk.END, content)
                        self.CURRENT_FILE = file_path 
                        self.update_file_path() 
                        self.file_menu.entryconfig(self.translate('save'), state=tk.NORMAL)
                        self.is_modified = False
                        self.update_line_numbers()
                        self.toolbar_compile_button.config(text=f'🛠{self.translate('compile')}')
                        self.toolbar_compile_button.config(state='disable')
                        self.toolbar_send_button.config(state='disable')
                        self.is_karel = False
                        self.edit_menu.entryconfig('LS', state=tk.DISABLED)
                        self.edit_menu.entryconfig('KL', state=tk.DISABLED)
                except Exception as e:
                    self.show_info(f'{self.translate('couldnt_open_file')}: {e}', 2, True)
        self.highlight_code()

    def save_file(self, event=None):
        """Сохраняет файл, если он уже существует, иначе вызывает 'Сохранить как'."""
        if self.CURRENT_FILE and not self.is_temp:
            self._save_to_file(self.CURRENT_FILE)
        else:
            if self.save_file_as():
                self.is_temp = False

    def save_file_as(self): 
        """Открывает диалог сохранения файла и сохраняет текст."""
        if self.CURRENT_FILE[-1:-3:-1].lower() == 'sl':
            if self.is_temp:
                file_path = filedialog.asksaveasfilename(
                    defaultextension="ls kl",
                    initialfile=f'{self.CURRENT_FILE.split('\\')[-1][12:-1]}s',
                    filetypes=[("LS prog", "*.ls"), (self.translate('all_files'), "*.*")]
                )
            else:
                file_path = filedialog.asksaveasfilename(
                    defaultextension="ls kl",
                    initialfile=self.CURRENT_FILE.split('\\')[-1],
                    filetypes=[("LS prog", "*.ls"), (self.translate('all_files'), "*.*")]
                )
        elif self.CURRENT_FILE[-1:-3:-1].lower() == 'lk':
            file_path = filedialog.asksaveasfilename(
                defaultextension="kl",
                initialfile=self.CURRENT_FILE.split('\\')[-1],
                filetypes=[("Karel", "*.kl"), (self.translate('all_files'), "*.*")]
            )
        else:
            file_path = filedialog.asksaveasfilename(
                initialfile=self.CURRENT_FILE.split('\\')[-1],
                filetypes=[(self.translate('all_files'), f'*.{self.CURRENT_FILE.split('\\')[-1].split('.')[-1]}')]
            )
        if file_path:
            self.CURRENT_FILE = file_path.replace('/', '\\')
            self._save_to_file(file_path)
            self.update_file_path() 
            self.file_menu.entryconfig(self.translate('save'), state=tk.NORMAL)
            self.is_modified = False
            return True
        return False

    def _save_to_file(self, file_path):
        """Сохраняет текст в указанный файл."""
        if self.ls_info and self.CURRENT_FILE[-1:-3:-1].lower() == 'sl':
            text_to_save = self._header_generate()
            temp = self.text_area.get("1.0", tk.END)
            text = self.text_area.get("1.0", tk.END).split("\n")[:-1]
            temp = ""
            for i, line in enumerate(text):
                t = "    " + str(i+1)
                temp += t[abs(4-len(t)):] + ":" + line + "\n"
            text_to_save += temp.replace("\n", ";\n")
            text_to_save += self.buffer_asser
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(text_to_save)
            self.toolbar_send_button.config(state='enable')
        else:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(self.text_area.get("1.0", tk.END))
        self.is_modified = False 
        self.update_file_path()
        self.show_info(self.translate('saved_succ'))
        
    def _header_generate(self):
        header = f'/PROG {self.ls_info['name'].upper()}  {'Macro' if self.ls_info['macro'] else ''}\n'
        header += f'/ATTR\n'
        header += f'OWNER  = {self.ls_info['owner'].upper()};\n'
        header += f'COMMENT  = "{self.ls_info['comment']}";\n'
        header += f'PROTECT  = {'READ' if self.ls_info['protect'] else 'READ_WRITE'};\n'
        header += 'TCD:  STACK_SIZE	= 0,\n      TASK_PRIORITY	= 50,\n      TIME_SLICE	= 0,\n      BUSY_LAMP_OFF	= 0,\n      ABORT_REQUEST	= 0,\n      PAUSE_REQUEST	= 0;\n'
        header += f'DEFAULT_GROUP	= {'1' if self.ls_info['motion'] else '*'},*,*,*,*;\n'
        header += '/MN\n'
        return header

    def new_input(self, event):
        """Обработка нового ввода."""
        if not self.CURRENT_FILE or self.is_temp:
            return
        if event.keycode == 9: # 9 - tab
            self.text_area.insert(tk.INSERT, " " * 4)
            return "break"  # Предотвращает стандартное поведение Tab
        elif event.keycode == 8: # 8 - backspace
            self.is_modified = True
            if event.char == '\x7f':
                cursor_index = self.text_area.index(tk.INSERT)
                for i in range(0, 20):
                    if self.text_area.get(f"{cursor_index} - {i+1}c", f"{cursor_index} - {i}c") in self.del_stoppers:
                        self.text_area.delete(f"{cursor_index} - {i-1}c", cursor_index)
                        break
                return "continue"
            cursor_index = self.text_area.index(tk.INSERT)
            start_index = f"{cursor_index} - 4c"
            if self.text_area.get(start_index, cursor_index) == " " * 4:
                self.text_area.delete(start_index, cursor_index)
                return "break"  # Предотвращает стандартное поведение BackSpace
        elif event.keysym == 'Control_L':
            return "continue"
        else:
            self.is_modified = True
        self.update_line_numbers()
        self.update_file_path(self.CURRENT_FILE + '*')
        if self.is_karel and not self.is_temp:
            self.toolbar_compile_button.config(text=f'🛠{self.translate('compile')}')
            self.toolbar_compile_button.config(state='enable')
        elif not self.is_temp and not self.is_karel:
            self.toolbar_send_button.config(state='enable')
        self.highlight_code()

    def update_line_numbers(self, event=None):
        """Обновляет номера строк с выравниванием по правому краю"""
        self.line_numbers.config(state=tk.NORMAL)
        self.line_numbers.delete(1.0, tk.END)
        # Получаем количество строк
        lines = self.text_area.get(1.0, tk.END).count('\n')
        lines = 1 if lines == 0 else lines
        # Определяем максимальную ширину
        max_width = 4
        # Добавляем номера строк с выравниванием
        line_numbers_text = "\n".join(
            f"{i:>{max_width}}"  # Выравнивание по правому краю
            for i in range(1, lines + 1)
        )
        self.line_numbers.insert(1.0, line_numbers_text)
        self.line_numbers.config(state=tk.DISABLED)
        # Синхронизируем прокрутку
        self.line_numbers.yview_moveto(self.text_area.yview()[0])

    def show_ftp_settings(self):
        """Открывает окно настроек FTP"""
        if hasattr(self, 'ftp_window') and self.ftp_window.winfo_exists():
            self.ftp_window.lift()
            return

        self.ftp_window = FTPSettingsWindow(
            parent=self.root,
            lang=self.language,
            callback=self._ftp_settings_close,
            show_info=self.show_info)
    
    def _ftp_settings_close(self):
        self.update_server_list()
    
    def open_ls_settings(self):
        if hasattr(self, 'lss_window') and self.lss_window.winfo_exists():
            self.lss_window.lift()
            return
        self.lss_window = LSSettingsWindow(
            parent=self.root,
            lang=self.language,
            callback=self._update_ls_header,
            current_data=self.ls_info)
    
    def _update_ls_header(self, new_data):
        if new_data:
            self.ls_info = new_data if new_data else self.ls_info
        self._save_to_file(self.CURRENT_FILE)
    
    def on_close(self):
        """Обрабатывает закрытие окна."""
        try:
            self._save_settings()
            if self.is_modified:
                response = messagebox.askyesnocancel(
                    self.translate('save_file'),
                    self.translate('quest_bef_cls'),
                    icon=messagebox.WARNING
                )
                if response is True:  # Пользователь выбрал "Сохранить"
                    self.save_file()
                    self.root.destroy()
                elif response is False:  # Пользователь выбрал "Не сохранять"
                    self.root.destroy()
                # Если response is None (пользователь выбрал "Отменить"), ничего не делаем
            else:
                self.root.destroy()
        except:
            self.root.destroy()

    def sync_scroll(self, *args):
        """Синхронизирует прокрутку текста и номеров строк"""
        self.scrollbarY.set(*args)
        self.line_numbers.yview_moveto(args[0])
        self.text_area.yview_moveto(args[0])

    def on_scrollbar_y(self, *args):
        """Обработчик движения скроллбара"""
        self.text_area.yview(*args)
        self.line_numbers.yview(*args)
    
    def tread_service(self):
        if self.files_queue:
            self.show_info(self.files_queue[-1])
        if self.backuping:
            self.root.after(100, self.tread_service)

class SearchBar:
    def __init__(self, text_widget: tk.Text, translater, ide):
        self.ide = ide
        self.view = False
        self.translate = translater
        self.text = text_widget
        self.frame = tk.Frame(self.text, bg="#9E9E9E", bd=1, relief='solid')        
        # Поле ввода
        self.entry = Entry(self.frame, width=30)
        self.entry.pack(side='left', padx=5, pady=5)        
        # Кнопки
        self.btn_next = Button(self.frame, text=self.translate('find'), command=self.find_next, cursor='arrow')
        self.btn_next.pack(side='left', padx=2)
        
        # Закрыть (крестик)
        self.btn_close = Button(self.frame, text='✖', width=2, command=self.hide, cursor='arrow')
        self.btn_close.pack(side='right', padx=2)        
        # Инициализация позиции и видимости
        self.hide()        
        # Настройка тега для подсветки найденного
        self.text.tag_configure('search', background="#BAEBEC", foreground="#000000")
        self.text.tag_configure('sel', background="#4C56DF", foreground="#000000")
        
        # Привязка горячих клавиш
        self.text.bind('<Control-f>', lambda e: self.show())
        self.text.bind('<Escape>', lambda e: self.hide())
        self.entry.bind('<Escape>', lambda e: self.hide())
        # Поиск при вводе текста (опционально)
        self.entry.bind('<KeyRelease>', lambda e: self.find_all())
        self.entry.bind('<Return>', lambda e: self.find_next())
        
    def show(self):
        """Показать панель поиска"""
        # Размещаем в правом верхнем углу текстового виджета
        self.frame.place(relx=1.0, x=-5, y=5, anchor='ne')
        self.btn_next.config(text=self.translate('find'))
        self.entry.focus_set()
        self.view = True
        self.entry.delete(0, 'end')
        self.find_all()  # обновить подсветку
        
    def hide(self):
        """Скрыть панель поиска и снять подсветку"""
        self.frame.place_forget()
        self.ide.highlight_code(find='')
        self.view = False
        
    def find_all(self, no_first=False):
        """Найти все вхождения и подсветить их"""
        query = self.entry.get()
        if not query:
            return
        self.ide.highlight_code(find=query)
    
    def find_next(self):
        """Найти следующее вхождение"""
        query = self.entry.get()
        if not query:
            return        
        # Текущая позиция курсора (начало выделения или позиция вставки)
        sel_start = self.text.index('insert')
        # Ищем от текущей позиции
        pos = self.text.search(query, sel_start, stopindex='end', nocase=True)
        if not pos:
            pos = self.text.search(query, '1.0', stopindex='end', nocase=True)
        self.find_all()
        end = self.text.index(f"{pos}+{len(query)}c")
        self.text.tag_remove('comments', pos, end)
        self.text.tag_remove('search', pos, end)
        self.text.tag_add('sel', pos, end)
        self.text.see(pos)
        self.text.mark_set("insert", f'{pos}+{len(query)}c')
        self.text.focus_set()

if __name__ == "__main__":
    root = tk.Tk()
    ide = FANUCE_IDE(root)
    root.mainloop()