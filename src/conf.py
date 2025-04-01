LANGUAGES = {
    'en': {
        'file': 'File',
        'new': 'New',
        'open': 'Open',
        'save': 'Save',
        'save_as': 'Save as...',
        'exit': 'Exit',
        'view': 'View',
        'dark_theme': 'Dark Theme',
        'light_theme': 'Light Theme',
        'full_v': 'Full Version',
        'light_v': 'Light Version',
        'save_file': 'Save File',        
        'quest_bef_cls': 'Do you want to save this file?',
        'all_files': 'All files',
        'lang': 'English',
        'lang_menu': 'Language',
    },
    'ru': {
        'file': 'Файл',
        'new': 'Новый',
        'open': 'Открыть',
        'save': 'Сохранить',
        'save_as': 'Сохранить как...',
        'exit': 'Выход',
        'view': 'Вид',
        'dark_theme': 'Тёмная тема',
        'light_theme': 'Светлая тема',
        'full_v': 'Полный вид',
        'light_v': 'Упрощённый вид',
        'save_file': 'Сохранить файл',        
        'quest_bef_cls': 'Вы хотите сохранить изменения перед созданием нового?',
        'all_files': 'Все файлы',
        'lang': 'Русский',
        'lang_menu': 'Язык',
    }
}

THEME = {
    'light': {
        'keywords': '#c75ff7',
        'datas': '#50c9cf',
        'comment': '#2fcf00',
        'logic': '#4590b7',
        'nums': '#95bf81',
        'LBL': '#d1a855',
        'bg_color': '#ffffff',
        'fg_color': '#000000',
        'insert_bg': '#000000',
        'line_numbers_bg': '#f0f0f0',
        'line_numbers_fg': '#606060',
    },
    'dark': {
        'keywords': '#d67eff',
        'datas': '#50c9cf',
        'comment': '#a0f164',
        'logic': '#50a3cf',
        'nums': '#d9ffc7',
        'LBL': '#fdce71',
        'bg_color': '#1e1e1e',
        'fg_color': '#ffffff',
        'insert_bg': '#ffffff',
        'line_numbers_bg': '#252526',
        'line_numbers_fg': '#cccccc',
    }
}
SINTAX_WORDS = {
'keywords': [
            'IF', 'WAIT', 'CALL', 'PAUSE', 'ENDIF', 'ELSE',
            'THEN', 'SKIP', 'JMP',
            'RUN', 'L', 'J',
            ],
'logic': [
         'AND', 'OR', 'ON', 'OFF',
         ],
'datas': [
         'DO', 'DI', 'F', 'R', 'P', 'PR',
         ],
}

CURRENT_LANGUAGE = 'en'  # by default