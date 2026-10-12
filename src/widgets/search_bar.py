import tkinter as tk
from tkinter.ttk import Button, Entry
from ..service import Service

class SearchBar:
    def __init__(
            self,
            text_widget: tk.Text,
            ide,
            service: Service
        ) -> None:
        self.ide = ide
        self.view = False
        self.SERVICE = Service('en')
        self.text = text_widget
        self.frame = tk.Frame(self.text, bg="#9E9E9E", bd=1, relief='solid')        
        # Поле ввода
        self.entry = Entry(self.frame, width=30)
        self.entry.pack(side='left', padx=5, pady=5)        
        # Кнопки
        self.btn_next = Button(self.frame, text=self.SERVICE.translate('find'), command=self.find_next, cursor='arrow')
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
        self.btn_next.config(text=self.SERVICE.translate('find'))
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
        self.text.tag_remove('sel', "1.0", tk.END)
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