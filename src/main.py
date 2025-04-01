import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import sys
import re
from conf import LANGUAGES, CURRENT_LANGUAGE, THEME, SINTAX_WORDS

class FANUCIDE:
    def __init__(self, root):
        self.root = root
        self.root.title("FANUC IDE")
        self.root.iconbitmap("./resources/icon.ico")     
        self.theme = ""
        self.language = CURRENT_LANGUAGE
        self.current_file = None # Переменная для хранения пути к текущему файлу
        self.SysKeys = ["Control_R", "Control_L", "Alt_L", "Alt_R", "Escape", "Shift_L", "Shift_R"]
        self.del_stoppers = [" ", ",", ".", "!", "?", ";", ":", "-", "(", ")", "\\", "/", "="]
        self.buffer_header = ""
        self.buffer_asser = ""
        self.colors = THEME['light']
        # Переменная для отслеживания изменений
        self.is_modified = False
        self.view = False
        # Создаем фрейм для группировки текстового поля и скроллбара
        right_frame = tk.Frame(self.root)
        right_frame.pack(side=tk.RIGHT, expand=True, fill='both')
        self.scrollbarY = tk.Scrollbar(right_frame)
        # Создаем текстовое поле с прокруткой и номерами строк
        self.text_area = tk.Text(right_frame, 
                           yscrollcommand=self.scrollbarY.set,
                           wrap=tk.NONE, 
                           pady=2,
                           font=("Consolas", 10),
                           width=80, 
                           height=25)
        self.scrollbarY.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_area.pack(side=tk.LEFT, expand=True, fill='both')
        # Поле для номеров строк
        self.line_numbers = tk.Text(self.root,
                                  width=4,
                                  padx=3,
                                  pady=2,
                                  takefocus=0,
                                  border=0,
                                  font=("Consolas", 10),
                                  background='lightgray',
                                  foreground='gray',
                                  state='disabled')
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        for tag, color in self.colors.items():
            self.text_area.tag_config(tag, foreground=color)

        self.text_area.bind("<KeyPress>", self.new_input)
        self.text_area.bind("<KeyRelease>", self.update_line_numbers)
        self.root.bind("<Control-KeyPress>", self.on_ctrl_keypress)  # Обработка Ctrl + клавиша
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)  # Обработка закрытия окна
        # Настройка прокрутки
        self.text_area.config(yscrollcommand=self.sync_scroll)
        self.line_numbers.config(yscrollcommand=self.sync_scroll)
        self.scrollbarY.config(command=self.on_scrollbar_y)
        # Создаем меню
        self.create_menu()
        try:
            settings = self.load_settings()
            self.theme = settings["theme"]
            self.root.geometry(settings["window_size"])
        except Exception as e:
            print(e)
            self.save_settings()
        if self.theme == "light":
            self.set_light_theme()
        else:
            self.set_dark_theme()
        if len(sys.argv) >= 2:
            self.current_file = sys.argv[1]
            self.open_file(self.current_file)
        self.update_line_numbers()

    def highlight_syntax(self, event=None):
        for tag in self.colors.keys():
            self.text_area.tag_remove(tag, '1.0', 'end')
        keywords = SINTAX_WORDS['keywords']
        # Подсветка ключевых слов
        for word in keywords:
            start = '1.0'
            while True:
                # Используем регулярное выражение для точного совпадения слов
                start = self.text_area.search(r'\y{}\y'.format(word), start, stopindex='end', regexp=True)
                if not start:
                    break
                end = f"{start}+{len(word)}c"
                self.text_area.tag_add('keywords', start, end)
                start = end
        datas = SINTAX_WORDS['datas']
        for word in datas:
            start = '1.0'
            while True:
                # Используем регулярное выражение для точного совпадения слов
                start = self.text_area.search(r'\y{}\y'.format(word), start, stopindex='end', regexp=True)
                if not start:
                    break
                end = f"{start}+{len(word)}c"
                self.text_area.tag_add('datas', start, end)
                start = end
        logic = SINTAX_WORDS['logic']
        for word in logic:
            start = '1.0'
            while True:
                # Используем регулярное выражение для точного совпадения слов
                start = self.text_area.search(r'\y{}\y'.format(word), start, stopindex='end', regexp=True)
                if not start:
                    break
                end = f"{start}+{len(word)}c"
                self.text_area.tag_add('logic', start, end)
                start = end
        self.highlight_pattern(r'(?<!\w)\d+(?!\w)', 'nums')
        self.highlight_pattern(r'LBL', 'LBL')
        self.highlight_pattern(r'!.*$|//.*$', 'comment')
        
    def highlight_pattern(self, pattern, tags, start='1.0', end='end'):
        """Подсвечивает текст по регулярному выражению"""
        text = self.text_area.get(start, end)
        
        for match in re.finditer(pattern, text, re.MULTILINE):
            group = 0 if isinstance(tags, str) else next((i for i, g in enumerate(match.groups()) if g), 0)
            tag = tags if isinstance(tags, str) else tags[group]
            
            start_idx = f"{start}+{match.start(group)}c"
            end_idx = f"{start}+{match.end(group)}c"
            
            self.text_area.tag_add(tag, start_idx, end_idx)
    def translate(self, key):
        """Получение перевода по ключу"""
        return LANGUAGES[self.language].get(key, key)

    def create_menu(self):
        menubar = tk.Menu(self.root)
        # Меню "Файл"
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label=self.translate('new'), command=self.new_file)
        file_menu.add_command(label=self.translate('open'), command=self.open_file)
        file_menu.add_separator()
        file_menu.add_command(label=self.translate('save'), command=self.save_file, state=tk.DISABLED)  # Изначально деактивировано
        file_menu.add_command(label=self.translate('save_as'), command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label=self.translate('exit'), command=self.on_close)
        menubar.add_cascade(label=self.translate('file'), menu=file_menu)
        # Меню "Вид"
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label=self.translate('dark_theme'), command=self.set_dark_theme)
        view_menu.add_command(label=self.translate('light_theme'), command=self.set_light_theme)
        view_menu.add_separator()
        view_menu.add_command(label=self.translate('full_v'), command=self.set_view)
        menubar.add_cascade(label=self.translate('view'), menu=view_menu)
        lang_menu = tk.Menu(menubar, tearoff=0)
        lang_menu.add_command(label="English", command=lambda: self.set_language('en'))
        lang_menu.add_command(label="Русский", command=lambda: self.set_language('ru'))
        menubar.add_cascade(label=self.translate('lang_menu'), menu=lang_menu)
        self.root.config(menu=menubar)
        self.file_menu = file_menu
        self.view_menu = view_menu
    
    def set_language(self, lang_code):
        """Смена языка интерфейса"""
        self.language = lang_code
        # Пересоздаем меню
        self.create_menu()
    
    def save_settings(self):
        """Сохраняет настройки в файл."""
        settings = {
            "theme": self.theme,
            "window_size": self.root.geometry(),
        }
        # Сохраняем настройки в файл
        with open("settings.json", "w", encoding="utf-8") as file:
            json.dump(settings, file, indent=4)

    def load_settings(self):
        """Загружает настройки из файла."""
        if not os.path.exists("settings.json"):
            return None 

        try:
            with open("settings.json", "r", encoding="utf-8") as file:
                settings = json.load(file)
                return settings
        except Exception as e:
            print(f"Error with settings load: {e}")
            return None
    
    def set_light_theme(self):
        """Настройка светлой темы для всех виджетов."""
        self.theme = "light"
        self.colors = THEME['light']
        # Настройка главного окна
        self.root.configure(bg=self.colors['bg_color'])
        # Настройка текстового поля
        self.text_area.configure(
            bg=self.colors['bg_color'],  # Фон текстового поля
            fg=self.colors['fg_color'],  # Цвет текста
            insertbackground=self.colors['insert_bg'],  # Цвет курсора
        )
        # Настройка поля для номеров строк
        self.line_numbers.configure(
            bg=self.colors['line_numbers_bg'],  # Фон
            fg=self.colors['line_numbers_fg'],  # Цвет текста
        )
        for tag, color in self.colors.items():
            self.text_area.tag_config(tag, foreground=color)
    
    def set_dark_theme(self):
        """Настройка тёмной темы для всех виджетов."""
        self.theme = "dark"
        self.colors = THEME['dark']
        # Настройка главного окна
        self.root.configure(bg=self.colors['bg_color'])
        # Настройка текстового поля
        self.text_area.configure(
            bg=self.colors['bg_color'],  # Фон текстового поля
            fg=self.colors['fg_color'],  # Цвет текста
            insertbackground=self.colors['insert_bg'],  # Цвет курсора
        )
        # Настройка поля для номеров строк
        self.line_numbers.configure(
            bg=self.colors['line_numbers_bg'],  # Фон
            fg=self.colors['line_numbers_fg'],  # Цвет текста
        )
        for tag, color in self.colors.items():
            self.text_area.tag_config(tag, foreground=color)
    
    def new_file(self):
        """Создание нового файла."""
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
            else:
                return
        file_path = filedialog.asksaveasfilename(
            defaultextension="new_file.LS",
            filetypes=[("FANUC Programs", "*.LS"), (self.translate('all_files'), "*.*")]
        )
        if file_path:
            self.current_file = file_path
            self._save_to_file(file_path)
            self.update_title()  # Обновляем заголовок окна
            self.file_menu.entryconfig(self.translate('save'), state=tk.NORMAL)  # Активируем "Сохранить"
            self.is_modified = False  # Сбрасываем флаг изменений
            self.text_area.delete("1.0", tk.END)
        else:
            self.update_title()
    
    def set_view(self):
        if self.view:
            self.view_menu.entryconfig(self.translate('light_v'), label=self.translate('full_v'))
        else:
            self.view_menu.entryconfig(self.translate('full_v'), label=self.translate('light_v'))
        self.view = not self.view
        self.open_file(self.current_file)

    def open_file(self, file_path=None):
        """Открывает файл и загружает его содержимое в текстовое поле."""
        if not file_path:
            file_path = filedialog.askopenfilename(
                filetypes=[("FANUC Programs", "*.LS"), (self.translate('all_files'), "*.*")]
            )
        if file_path:
            content = ""
            one_line = ""
            header = ""
            asser = ""
            header_getted = False
            text_getted = False
            try:
                if not self.view:
                    with open(file_path, "r", encoding="utf-8") as file:
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
                                elif header_getted and not text_getted:
                                    content += one_line[5:]
                                else:
                                    asser += one_line
                    content = content[:-1]
                    self.buffer_header = header
                    self.buffer_asser = asser
                    content = content.replace(";", "")
                    self.text_area.delete("1.0", tk.END) 
                    self.text_area.insert(tk.END, content) 
                else:
                    with open(file_path, "r", encoding="utf-8") as file:
                        content = file.read()
                    self.text_area.delete("1.0", tk.END)
                    self.text_area.insert(tk.END, content)
                self.current_file = file_path  
                self.update_title() 
                self.file_menu.entryconfig(self.translate('save'), state=tk.NORMAL)
                self.is_modified = False
                self.update_line_numbers()
                self.highlight_syntax()
            except Exception as e:
                messagebox.showerror("Error", f"Can't open file: {e}")

    def save_file(self, event=None):
        """Сохраняет файл, если он уже существует, иначе вызывает 'Сохранить как'."""
        if self.current_file:
            self._save_to_file(self.current_file)
        else:
            self.save_file_as()

    def save_file_as(self):
        """Открывает диалог сохранения файла и сохраняет текст."""
        file_path = filedialog.asksaveasfilename(
            defaultextension="new_file.LS",
            filetypes=[("FANUC Programs", "*.LS"), (self.translate('all_files'), "*.*")]
        )
        if file_path:
            self.current_file = file_path
            self._save_to_file(file_path)
            self.update_title() 
            self.file_menu.entryconfig(self.translate('save'), state=tk.NORMAL)
            self.is_modified = False 

    def _save_to_file(self, file_path):
        """Сохраняет текст в указанный файл."""
        try:
            if not self.view:
                text_to_save = self.buffer_header
                temp = self.text_area.get("1.0", tk.END)
                text = self.text_area.get("1.0", tk.END).split("\n")[:-1]
                temp = ""
                for i, line in enumerate(text):
                    t = "    " + str(i+1)
                    temp += t[abs(4-len(t)):] + ":" + line + "\n"
                text_to_save += temp.replace("\n", ";\n")
                text_to_save += self.buffer_asser
            else:
                text_to_save = self.text_area.get("1.0", tk.END)
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(text_to_save)
            self.is_modified = False 
            self.update_title() 
        except Exception as e:
            messagebox.showerror("Error", f"Can't save file: {e}")
    
    def update_title(self):
        """Обновляет заголовок окна."""
        title = "FANUC IDE"
        if self.current_file:
            title += f" - {self.current_file}"
            if self.is_modified:
                title += "*(Not saved)"
        self.root.title(title)

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
        self.update_title()
        self.update_line_numbers()
        self.highlight_syntax()

    def on_ctrl_keypress(self, event):
        """Обрабатывает сочетания клавиш с Ctrl."""
        if event.keycode == 83 or event.keycode == 1067:  # 83 - 's', 1067 - 'ы'
            self.save_file()
    
    def update_line_numbers(self, event=None):
        """Обновляет номера строк с выравниванием по правому краю"""
        self.line_numbers.config(state=tk.NORMAL)
        self.line_numbers.delete(1.0, tk.END)
        # Получаем количество строк
        lines = self.text_area.get(1.0, tk.END).count('\n')
        if lines == 0:
            lines = 1
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

    def on_close(self):
        self.save_settings()
        """Обрабатывает закрытие окна."""
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

    def sync_scroll(self, *args):
        """Синхронизирует прокрутку текста и номеров строк"""
        self.scrollbarY.set(*args)
        self.line_numbers.yview_moveto(args[0])

    def on_scrollbar_y(self, *args):
        """Обработчик движения скроллбара"""
        self.text_area.yview(*args)
        self.line_numbers.yview(*args)

if __name__ == "__main__":
    root = tk.Tk()
    ide = FANUCIDE(root)
    root.mainloop()