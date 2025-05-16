import re

def is_valid_url(url: str) -> bool:
    regex = re.compile(
            r'^(?:http|ftp)s?://' # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
            r'localhost|' #localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
            r'(?::\d+)?' # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return re.match(regex, url) is not None

def load_text_from_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Файл {filename} не найден")
        return None
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
        return None
    
def escape_markdown(text: str) -> str:
    """
    Экранирует: _ * [ ] ( ) ~ ` > # + - = | { } . ! 
    Учитывает уже экранированные символы (не добавляет лишние \).
    """
    # Символы, которые нужно экранировать (согласно документации Telegram)
    chars_to_escape = r'_[]()~>#+-=|{}.!'
    
    # Регулярное выражение для поиска символов, которые НЕ экранированы
    pattern = re.compile(rf'(?<!\\)([{re.escape(chars_to_escape)}])')
    
    # Заменяем все неэкранированные символы на экранированные
    escaped_text = pattern.sub(r'\\\1', text)
    
    return escaped_text
