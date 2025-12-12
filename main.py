import tkinter as tk, os, json, shutil, subprocess
from tkinter import filedialog, messagebox, ttk, Menu, simpledialog
from src.ftp_settings import  FTPSettingsWindow
from ftplib import FTP
from PIL import ImageTk, Image
from src.conf import LANGUAGES, CURRENT_LANGUAGE

class FANUCE_IDE:
    def __init__(self, root):
        self.root = root
        self.root.title("FANUC IDE")
        self.PROJECT_DIRICTORY = '\\'.join(__file__.split('\\')[:-1])
        os.chdir(self.PROJECT_DIRICTORY)
        self.root.iconbitmap(f'{self.PROJECT_DIRICTORY}\\resources\\icon.ico')
        self.SERVERS_FILE = f'{self.PROJECT_DIRICTORY}\\resources\\servers_list.json'
        self.CURRENT_FILE = None
        self.CURRENT_DIRICTORY = self.PROJECT_DIRICTORY
        if not os.path.exists(f'{self.PROJECT_DIRICTORY}\\cache.json'):
            self._create_config_file()
        with open(f'{self.PROJECT_DIRICTORY}\\cache.json', 'r', encoding='utf-8') as f:
            temp = json.load(f)
            self.CURRENT_DIRICTORY = temp['path']
            self.language = temp['lang']
            self.root.geometry(temp['geo'])
        if not os.path.exists(f'{self.PROJECT_DIRICTORY}\\src\\robot.ini'):
            self._create_robot_ini(self.PROJECT_DIRICTORY)
        self.buffer_header, self.buffer_asser, self.target_server_name = '', '', ''
        self.target_server, self.all_servers = {}, {}
        self.is_modified = False
        self.SysKeys = ["Control_R", "Control_L", "Alt_L", "Alt_R", "Escape", "Shift_L", "Shift_R"]
        self.del_stoppers = [" ", ",", ".", "!", "?", ";", ":", "-", "(", ")", "\\", "/", "="]
        self.is_karel = False
        self.filter_server_files = tk.IntVar(value=1)

        ''' Главное окно '''
        main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=4)
        main_paned.pack(expand=True, fill='both')
        left_paned = tk.PanedWindow(main_paned, orient=tk.VERTICAL, sashrelief=tk.RAISED, sashwidth=4)
        main_paned.add(left_paned, minsize=50, width=200) 
        right_frame = tk.Frame(main_paned)
        main_paned.add(right_frame)

        '''Левая часть'''
        # Меню-бар
        menubar_left_menu = tk.Frame(left_paned, height=20)
        left_paned.add(menubar_left_menu, minsize=20)
        self.server_combobox = ttk.Combobox(menubar_left_menu, state="readonly")
        self.server_combobox.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        self.server_combobox.bind("<<ComboboxSelected>>", self._on_server_selected)
        original_image = Image.open(f'{self.PROJECT_DIRICTORY}\\resources\\gear.png').resize((16, 16), Image.LANCZOS)
        self.gear_icon = ImageTk.PhotoImage(original_image)
        self.ftp_settings_but = ttk.Button(menubar_left_menu, image=self.gear_icon, command=self.show_ftp_settings)
        self.ftp_settings_but.image = self.gear_icon  
        self.ftp_settings_but.pack(side=tk.RIGHT, padx=2)
        # Основная левая часть (файлы + логи)
        files_paned = tk.PanedWindow(left_paned, orient=tk.VERTICAL, sashrelief=tk.RAISED)
        left_paned.add(files_paned, minsize=100)  # Основная область с разделителем
        # Панель файлового дерева
        file_tree_frame = tk.Frame(files_paned)
        file_tree_frame.pack(expand=True, fill='both')
        tree_scroll = ttk.Scrollbar(file_tree_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_tree = ttk.Treeview(
            file_tree_frame,
            yscrollcommand=tree_scroll.set,
            show='tree',
            selectmode='browse'
        )
        self.file_tree.pack(expand=True, fill='both', padx=2, pady=2)
        tree_scroll.config(command=self.file_tree.yview)
        self.file_tree.bind("<Double-1>", self._temp_open_file)
        files_paned.add(file_tree_frame, minsize=100)
        # Локальные файлы        
        local_file_tree_frame = tk.Frame(files_paned)
        local_file_tree_frame.pack(expand=True, fill='both')
        self.local_nav_frame = tk.Frame(local_file_tree_frame)
        self.local_nav_frame.pack(fill='x')

        self.local_path_label = ttk.Label(self.local_nav_frame, text=self.CURRENT_DIRICTORY)
        self.local_path_label.pack(side='left', fill='x', expand=True)
        local_tree_scroll = ttk.Scrollbar(local_file_tree_frame)
        local_tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.local_file_tree = ttk.Treeview(
            local_file_tree_frame,
            yscrollcommand=local_tree_scroll.set,
            show='tree',
            selectmode='browse'
        )
        self.local_file_tree.pack(expand=True, fill='both', padx=2, pady=2)
        local_tree_scroll.config(command=self.local_file_tree.yview)
        self.local_file_tree.bind("<Double-1>", self._on_local_file_double_click)
        files_paned.add(local_file_tree_frame, minsize=100)
        self.file_tree.tag_configure('folder', foreground='blue')
        self.file_tree.tag_configure('file', foreground='black')
        self.local_file_tree.tag_configure('folder', foreground='orange')
        self.local_file_tree.tag_configure('file', foreground='black')

        '''Правая часть'''
        # Меню кода
        menu_code_frame = tk.Frame(right_frame, height=20)
        menu_code_frame.pack(side=tk.TOP, fill=tk.X)
        self.CURRENT_FILE_path_menubar = tk.Label(
            menu_code_frame, 
            justify="left", 
            font=("Calibri", 10), 
            cursor="arrow", 
            text=self.translate('menubar_code')
        )
        self.CURRENT_FILE_path_menubar.pack(side=tk.LEFT, fill=tk.X)

        self.compile_button = ttk.Button(
            menu_code_frame, 
            text=self.translate('compile'), 
            width=20, 
            state='disabled',
            command=self.copmile_karel
        )
        self.compile_button.pack(side=tk.RIGHT)

        self.send_button = ttk.Button(
            menu_code_frame, 
            text=self.translate('send'), 
            width=20, 
            state='disabled',
            command=self.send_file

        )
        self.send_button.pack(side=tk.RIGHT)
        # Область кода
        code_frame = tk.Frame(right_frame)
        code_frame.pack(expand=True, fill='both')
        self.scrollbarY = tk.Scrollbar(code_frame)
        self.text_area = tk.Text(
            code_frame, 
            yscrollcommand=self.scrollbarY.set,
            wrap=tk.NONE, 
            pady=2,
            font=("Consolas", 10),
            width=80, 
            height=25,
            state='disabled'
        )
        self.line_numbers = tk.Text(
            code_frame,
            width=4,
            padx=3,
            pady=2,
            takefocus=0,
            border=0,
            font=("Consolas", 10),
            background='lightgray',
            foreground='gray',
            state='disabled'
        )
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        self.scrollbarY.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_area.pack(side=tk.LEFT, expand=True, fill='both')

        self.text_area.bind("<KeyPress>", self.new_input)
        self.text_area.bind("<KeyRelease>", self.update_line_numbers)
        self.text_area.bind('<<Modified>>', self.highlight_exclamation_lines)
        self.text_area.bind("<Control-KeyPress>", self.on_ctrl_keypress)
        # Настраиваем тег для подсветки
        self.text_area.tag_config(
            "exclamation",
            foreground="black",      # цвет текста
            background="yellow",        # цвет фона
            font=("Consolas", 10, "bold")  # шрифт
        )
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)  # Обработка закрытия окна
        # Настройка прокрутки
        self.text_area.config(yscrollcommand=self.sync_scroll)
        self.line_numbers.config(yscrollcommand=self.sync_scroll)
        self.scrollbarY.config(command=self.on_scrollbar_y)
        self.update_local_files()
        self.update_server_list()
        self.create_menu()
        self._setup_context_menus()

    def highlight_exclamation_lines(self, event=None):
        # Удаляем все теги подсветки
        self.text_area.tag_remove("exclamation", "1.0", tk.END)
        # Получаем весь текст
        content = self.text_area.get("1.0", tk.END)
        lines = content.splitlines()
        for line_num, line in enumerate(lines, start=1):
            if '!' in line:
                # Координаты начала и конца строки
                start = f"{line_num}.0"
                end = f"{line_num}.{len(line)}"
                # Применяем тег к строке
                self.text_area.tag_add("exclamation", start, end)
    
    def create_menu(self):
        menubar = tk.Menu(self.root)
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
        # Язык
        lang_menu = tk.Menu(menubar, tearoff=0)
        lang_menu.add_command(label="English", command=lambda: self.set_language('en'))
        lang_menu.add_command(label="Русский", command=lambda: self.set_language('ru'))
        menubar.add_cascade(label=self.translate('lang_menu'), menu=lang_menu)
        # Робот
        robot_menu = tk.Menu(menubar, tearoff=0)
        robot_menu.add_command(label=self.translate('r_backup'), command=lambda: messagebox.showinfo('not yeat', 'Ещё не готово'))
        menubar.add_cascade(label=self.translate('robot'), menu=robot_menu)
        self.root.config(menu=menubar)
        self.file_menu = file_menu
    
    def _setup_context_menus(self):
        self._add_text_context_menu(self.text_area)
        self._add_tree_context_menu(self.file_tree)
        self._add_local_tree_context_menu(self.local_file_tree)

    def _add_text_context_menu(self, text_widget, level=1):
        """Добавляет контекстное меню для Text виджетов"""
        menu = Menu(text_widget, tearoff=0)
        menu.add_command(label=self.translate('copy'), command=lambda: text_widget.event_generate("<<Copy>>"))
        if level == 1:
            menu.add_command(label=self.translate('paste'), command=lambda: text_widget.event_generate("<<Paste>>"))
            menu.add_command(label=self.translate('cut'), command=lambda: text_widget.event_generate("<<Cut>>"))
        menu.add_separator()
        menu.add_command(label=self.translate('select_all'), 
                       command=lambda: text_widget.tag_add("sel", "1.0", "end"))

        # Привязка к правой кнопке мыши
        text_widget.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))

        # Добавляем горячие клавиши
        text_widget.bind("<Control-c>", lambda e: text_widget.event_generate("<<Copy>>"))
        text_widget.bind("<Control-x>", lambda e: text_widget.event_generate("<<Cut>>"))
        text_widget.bind("<Control-a>", lambda e: text_widget.tag_add("sel", "1.0", "end"))
    
    def _add_tree_context_menu(self, widget):
        menu = Menu(widget, tearoff=0)
        menu.add_command(label=self.translate('open'), command=self._temp_open_file)
        menu.add_command(label=self.translate('dnld'), command=self._download_and_open_file)
        menu.add_command(label=self.translate('del'), command=self._delete_selected_file)
        menu.add_separator()
        menu.add_command(label=self.translate('refresh'), command=self.refresh_file_list)
        menu.add_checkbutton(label=self.translate('filter'), command=self.refresh_file_list, variable=self.filter_server_files)
        # menu.add_command(label='Фильтр ls', command=self._filter_files_ls, state='active')
        widget.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))
    
    def _add_local_tree_context_menu(self, widget):
        menu = Menu(widget, tearoff=0)
        menu.add_command(label=self.translate('open'), command=self._on_local_file_double_click)
        menu.add_command(label=self.translate('send'), command=self._send_local_file)
        menu.add_command(label=self.translate('del'), command=self._delete_selected_local_file)
        menu.add_separator()
        menu.add_command(label=self.translate('open_folder'), command=self._open_local_folder)
        menu.add_command(label=self.translate('create_folder'), command=self._create_folder)
        menu.add_command(label=self.translate('refresh'), command=self.update_local_files)
        widget.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))
    
    def _change_def_dir(self):
        while True:
            selected_dir = filedialog.askdirectory(title="Выберите папку для проектов",
                                                   initialdir='\\'.join(self.PROJECT_DIRICTORY.split('\\')[:-1]))
            if not selected_dir:  # Пользователь отменил выбор
                return
            try:
                self.CURRENT_DIRICTORY = selected_dir.replace('/', '\\')
                self._save_settings()
            except Exception as e:
                messagebox.showerror(self.translate('err'),
                                     f"Невозможно записать в выбранную папку:\n{str(e)}\n\nВыберите другую папку.")
                
    def _create_config_file(self):
        while True:
            selected_dir = filedialog.askdirectory(title="Выберите папку для проектов",
                                                   initialdir='\\'.join(self.PROJECT_DIRICTORY.split('\\')[:-1]))
            if not selected_dir:  # Пользователь отменил выбор
                if self.CURRENT_DIRICTORY:
                    break
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
                with open(f'{self.PROJECT_DIRICTORY}\\cache.json', 'w', encoding='utf-8') as f:
                    json.dump({'path': selected_dir, 
                               'lang': CURRENT_LANGUAGE,
                               'geo': '800x500'},
                                f)
                break
            except Exception as e:
                messagebox.showerror(self.translate('err'),
                                     f"Невозможно записать в выбранную папку:\n{str(e)}\n\nВыберите другую папку.")    

    def _save_settings(self):
        with open(f'{self.PROJECT_DIRICTORY}\\cache.json', 'r+', encoding='utf-8') as f:
            temp_path = json.load(f)['path']
            f.seek(0)
            f.truncate()
            json.dump({'path': temp_path, 
                       'lang': self.language,
                       'geo': f'{self.root.geometry()}'}, 
                       f)

    def copmile_karel(self):
        self.save_file()
        try:
            os.chdir('\\'.join(self.CURRENT_FILE.split('\\')[:-1]))
            result = subprocess.run(
                [f'{self.PROJECT_DIRICTORY}\\src\\ktrans.exe', f'{self.CURRENT_FILE}', '/config' , f'{self.PROJECT_DIRICTORY}\\src\\robot.ini'],
                capture_output=True,
                text=True,
                check=True)
            messagebox.showinfo(self.translate('compile_success'),
                                result.stdout)
            self.update_local_files()
            self.compile_button.config(text=self.translate('compiled'))
            self.compile_button.config(state='disable')
            self.send_button.config(state='enable')
        except Exception as e:
            messagebox.showerror(self.translate('compilation_error'),
                                 e.stdout)
            self.send_button.config(state='disable')
        os.chdir(self.PROJECT_DIRICTORY)
    
    def send_file(self, file=''):
        if not self.target_server_name:
            messagebox.showinfo(self.translate('inf'),
                                self.translate('no_select_server'))
            return
        tmp_path = file if file else self.CURRENT_FILE
        tmp_path = tmp_path.replace('/', '\\')
        if os.path.isdir(tmp_path):
            messagebox.showerror(self.translate('warn'),
                                 self.translate('cant_send_folder'))
            return
        if not messagebox.askyesno(self.translate('send_confirm'),
                                   f'{self.translate('u_sure_to_send')}: {tmp_path}\n{self.translate('to_server')}: {self.target_server_name}?',
                                   icon='question'):
            return
        try:
            if tmp_path.split('\\')[-1].split('.')[-1].lower() == 'kl':
                tmp_path = f'{tmp_path[:-2]}pc'
            ftp = FTP(timeout=7)
            ftp.connect(self.target_server['adress'])
            log = self.target_server['login'] if self.target_server['login'] else 'admin'
            ftp.login(log, self.target_server['pass'])
            ftp.voidcmd('TYPE I')
            with open(tmp_path, 'rb') as s_file:
                ftp.storbinary(f'STOR {tmp_path.split('\\')[-1]}', s_file)
            messagebox.showinfo(self.translate('sending_file'),
                                f'{self.translate('sending_file')} {tmp_path} {self.translate('was_success')}!')
        except Exception as e:
            messagebox.showerror(self.translate('err'), f"{self.translate('couldnt_send_file')}: {e}")          
        self.send_button.config(state='disable')
        ftp.quit()

    def on_ctrl_keypress(self, event):
        """Обрабатывает сочетания клавиш с Ctrl."""
        if event.keycode == 83 or event.keycode == 1067:  # 83 - 's', 1067 - 'ы'
            self.save_file()

    def _local_nav_back(self):
        """Переходит в родительскую папку для локальных файлов"""
        parent = os.path.dirname(self.CURRENT_DIRICTORY.rstrip('/\\'))
        if os.path.exists(parent):
            self.CURRENT_DIRICTORY = parent
            self.update_local_files()
            self.local_path_label.config(text=self.CURRENT_DIRICTORY)
            self.CURRENT_DIRICTORY = parent
        
    def _create_robot_ini(self, main_dir):
        with open(f'{main_dir}\\src\\robot.ini', 'w', encoding='utf-8') as f:
            print('Creating robot.ini...')
            f.write('[WinOLPC_Util]\n')
            f.write(f'Robot={main_dir}\\resources\\Robot_1\n')
            f.write('Version=V9.10-1\n')
            f.write(f'Path={main_dir}\\resources\\V910-1\\bin\n')
            f.write(f'Support={main_dir}\\resources\\Robot_1\\support\n')
            f.write(f'Output={main_dir}\\resources\\Robot_1\\output\n')
    
    def _open_local_folder(self):
        open_folder = filedialog.askdirectory(title=self.translate('choice_folder'),
                                              initialdir=self.CURRENT_DIRICTORY)
        if not open_folder:
            return
        self.CURRENT_DIRICTORY = open_folder
        self.update_local_files()
    
    def _create_folder(self):
        while True:
            folder_name = simpledialog.askstring(
                f'{self.translate('folder_name')}:',
                f'{self.translate('enter_folder_name')}: ',
                initialvalue='folder1'
            )
            if folder_name is None:
                return
            if not folder_name.strip():
                messagebox.showwarning(
                    self.translate('empty_name'),
                    self.translate('name_empty')
                )
                continue
            try:
                os.makedirs(f'{self.CURRENT_DIRICTORY}\\{folder_name}')
            except Exception as e:
                messagebox.showerror(
                    'Ошибка создания',
                    f'Не удалось создать папку: {e}'
                )
            self.update_local_files()
            break

    def _delete_selected_local_file(self):
        try:
            item = self.local_file_tree.selection()[0]
        except Exception as e:
            messagebox.showwarning(
                'Ошибка удаления',
                'Не выбран файл'
            )
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
        if messagebox.askyesno(
            "Подтверждение", 
            f"Вы точно хотите удалить файл {filename}\nС сервера: {self.target_server_name}?",
            icon='warning'
        ):
            try:
                ftp = FTP(timeout=5)
                ftp.connect(self.target_server['adress'])
                ftp.login('admin', '')
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
                ftp = FTP(timeout=5)
                ftp.connect(self.target_server['adress'])
                login = self.target_server['login'] if self.target_server['login'] else 'admin'
                ftp.login(login, self.target_server['pass'])
                files = ftp.nlst()
                if self.filter_server_files.get():
                    extensions = ['.kl', '.ls']  # Нужные расширения
                    files = [f for f in files if any(f.lower().endswith(ext) for ext in extensions)]
            except Exception as e:
                messagebox.showerror(self.translate('err'), f"{self.translate('connection_error')}: {e}")
                return
            for item in self.file_tree.get_children():
                self.file_tree.delete(item)
            for name in files:
                self.file_tree.insert('', 'end', text=name)
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
                messagebox.showerror(self.translate('err'), f"Не удалось загрузить список: {e}")
                return None 
            self.server_combobox['values'] = list(self.all_servers.keys())
    
    def update_local_files(self, path=None):
        """Обновляет список локальных файлов и папок"""
        if path is None:
            path = self.CURRENT_DIRICTORY

        for item in self.local_file_tree.get_children():
            self.local_file_tree.delete(item)
        self.local_file_tree.insert('', 'end', text='...', tags=('folder',))
        try:
            items = os.listdir(path)
            # Сначала добавляем папки, потом файлы
            for name in sorted(items, key=lambda x: not os.path.isdir(os.path.join(path, x))):
                full_path = os.path.join(path, name)
                if os.path.isdir(full_path):
                    self.local_file_tree.insert('', 'end', text=name, values=[full_path], tags=('folder',))
                else:
                    self.local_file_tree.insert('', 'end', text=name, values=[full_path], tags=('file',))
        except Exception as e:
            messagebox.showerror(self.translate('wee'), f"Не удалось прочитать папку: {str(e)}")
    
    def _on_local_file_double_click(self, event=None):
        """Обрабатывает двойной клик по локальным файлам/папкам"""
        selected = self.local_file_tree.selection()
        if not selected:
            return

        item = selected[0]
        name = self.local_file_tree.item(item, 'text')
        if name == '...':
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
            self.open_file(full_path)
            self.is_temp = False
            self.send_button.config(state='enable')
        
    def _temp_open_file(self, event=None):
        item = self.file_tree.selection()[0]
        if item:
            ftp = FTP(timeout=5)
            ftp.connect(self.target_server['adress'])
            login = self.target_server['login'] if self.target_server['login'] else 'admin'
            ftp.login(login, self.target_server['pass'])
            filename = self.file_tree.item(item, 'text')
            t_filename = f'TEMP_FILE-{filename}'
            with open(t_filename, 'wb+') as f:
                ftp.retrbinary(f"RETR {filename}", f.write)
            self.open_file(t_filename)
            self.update_file_path(custom=f'{self.target_server_name} - {t_filename}')
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
                ans = messagebox.askyesno('Отмена загрузки',
                                          'Вы хотите отменить загрузку?',
                                          icon='question')
                if ans:
                    return
            elif file_path:
                break
        try:
            ftp = FTP(timeout=5)
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
        self.compile_button.config(text=self.translate('compile'))
        self.send_button.config(text=self.translate('send'))
        if not self.CURRENT_FILE:
            self.CURRENT_FILE_path_menubar.config(text=self.translate('menubar_code'))
        self._setup_context_menus()

    def translate(self, key):
        """Получение перевода по ключу"""
        return LANGUAGES[self.language].get(key, key)

    def update_file_path(self, custom=''):
        """Обновляет заголовок окна."""
        if custom:
            self.CURRENT_FILE_path_menubar.config(text=custom)
        elif self.CURRENT_FILE and not custom:
            self.CURRENT_FILE_path_menubar.config(text=self.CURRENT_FILE)

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
                                                 filetypes=[("Karel listing", "*.kl"), ("TP program", "*.ls"), (self.translate('all_files'), "*.*")])
        if file_path:
            self.CURRENT_FILE = file_path
            self._save_to_file(file_path)
            self.update_file_path()  # Обновляем заголовок окна
            self.file_menu.entryconfig(self.translate('save'), state=tk.NORMAL)  # Активируем "Сохранить"
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
            )
        self.text_area.config(state='normal')
        if file_path:
            self.send_button.config(state='disable')
            self.compile_button.config(state='disable')
            self.buffer_asser = ''
            self.buffer_header = ''
            if file_path[-1:-3:-1].lower() == 'sl':
                content = ""
                one_line = ""
                header = ""
                asser = ""
                header_getted = False
                text_getted = False
                try:
                    with open(file_path, "r", encoding="utf-8") as file:
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
                            self.send_button.config(state='disable')
                            return
                        header += one_line                        
                        while True:
                            one_line = file.readline()
                            if "/MN" in one_line:
                                header_getted = True
                                header += one_line
                            elif "/POS" in one_line:
                                text_getted = True
                                asser += one_line
                            elif "/END" in one_line:
                                asser += one_line
                                break
                            else:
                                if not header_getted:
                                    header += one_line
                                elif header_getted and text_getted:
                                    asser += one_line
                                elif header_getted and not text_getted:
                                    content += one_line[5:]
                                    continue
                    content = content[:-1]
                    content = content.replace(";", "")
                    self.buffer_header = header
                    self.buffer_asser = asser
                    index = self.buffer_header.find("READ;")
                    if index!= -1:
                        self.buffer_header = self.buffer_header[:index] + 'READ_WRITE' + self.buffer_header[index+4:]
                    self.text_area.delete("1.0", tk.END) 
                    self.text_area.insert(tk.END, content)
                    self.CURRENT_FILE = file_path  
                    self.update_file_path() 
                    self.file_menu.entryconfig(self.translate('save'), state=tk.NORMAL)
                    self.is_modified = False
                    self.update_line_numbers()
                    self.is_karel = False
                except Exception as e:
                    messagebox.showerror(self.translate('err'), f'{self.translate('couldnt_open_file')}: {e}')
            elif file_path[-1:-3:-1].lower() == 'lk':
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    self.text_area.delete("1.0", tk.END) 
                    self.text_area.insert(tk.END, content)
                    self.CURRENT_FILE = file_path 
                    self.update_file_path() 
                    self.file_menu.entryconfig(self.translate('save'), state=tk.NORMAL)
                    self.is_modified = False
                    self.update_line_numbers()
                    self.compile_button.config(text=self.translate('compile'))
                    self.compile_button.config(state='enable')
                    self.is_karel = True

    def save_file(self, event=None):
        """Сохраняет файл, если он уже существует, иначе вызывает 'Сохранить как'."""
        if self.CURRENT_FILE and not self.is_temp:
            self._save_to_file(self.CURRENT_FILE)
        else:
            self.save_file_as()
            self.is_temp = False

    def save_file_as(self):
        """Открывает диалог сохранения файла и сохраняет текст."""
        if self.CURRENT_FILE[-1:-3:-1] == 'sl':
            file_path = filedialog.asksaveasfilename(
                defaultextension="ls kl",
                initialfile=self.CURRENT_FILE.split('\\')[-1],
                filetypes=[("TP", "*.ls"), (self.translate('all_files'), "*.*")]
            )
        elif self.CURRENT_FILE[-1:-3:-1] == 'lk':
            file_path = filedialog.asksaveasfilename(
                defaultextension="kl",
                initialfile=self.CURRENT_FILE.split('\\')[-1],
                filetypes=[("Karel", "*.kl"), (self.translate('all_files'), "*.*")]
            )
        if file_path:
            self.CURRENT_FILE = file_path
            self._save_to_file(file_path)
            self.update_file_path() 
            self.file_menu.entryconfig(self.translate('save'), state=tk.NORMAL)
            self.is_modified = False 

    def _save_to_file(self, file_path):
        """Сохраняет текст в указанный файл."""
        if self.buffer_header and self.buffer_asser:
            text_to_save = self.buffer_header
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
            self.send_button.config(state='enable')
        else:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(self.text_area.get("1.0", tk.END))
        self.is_modified = False 
        self.update_file_path() 

    def new_input(self, event):
        """Обработка нового ввода."""
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
        else:
            self.is_modified = True
        if not self.CURRENT_FILE:
            return
        self.update_line_numbers()
        self.update_file_path(self.CURRENT_FILE + '*')
        if self.is_karel and not self.is_temp:
            self.compile_button.config(text=self.translate('compile'))
            self.compile_button.config(state='enable')
        elif not self.is_temp and not self.is_karel:
            self.send_button.config(state='enable')

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
        self.highlight_exclamation_lines()

    def show_ftp_settings(self):
        """Открывает окно настроек FTP"""
        if hasattr(self, 'ftp_window') and self.ftp_window.winfo_exists():
            self.ftp_window.lift()
            return

        self.ftp_window = FTPSettingsWindow(
            parent=self.root,         # Передаем иконку
            lang=self.language,
            callback=self._ftp_settings_close
        )
    
    def _ftp_settings_close(self):
        self.update_server_list()
    
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

if __name__ == "__main__":
    root = tk.Tk()
    ide = FANUCE_IDE(root)
    root.mainloop()