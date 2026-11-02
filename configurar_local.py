"""Completa las credenciales locales sin mostrarlas ni enviarlas al chat."""

from getpass import getpass
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit

from dotenv import dotenv_values, set_key


def main():
    env = Path(__file__).resolve().with_name('.env')
    if not env.exists():
        print('Primero copia .env.example como .env.')
        return
    values = dotenv_values(env)
    url = urlsplit(values.get('DATABASE_URL') or '')
    if not url.hostname or not url.username:
        print('Completa primero el host y usuario de DATABASE_URL en .env.')
        return
    print('Las entradas son privadas: no aparecen mientras escribes o pegas.')
    password = getpass('Contrasena de la base de datos Supabase (Enter conserva la actual): ')
    api_key = getpass('Clave API de Groq (Enter conserva la actual): ').strip()
    if password:
        host = f'[{url.hostname}]' if ':' in url.hostname else url.hostname
        port = f':{url.port}' if url.port else ''
        netloc = f'{url.username}:{quote(password, safe="")}@{host}{port}'
        set_key(str(env), 'DATABASE_URL', urlunsplit(url._replace(netloc=netloc)))
    if api_key:
        set_key(str(env), 'LLM_API_KEY', api_key)
    print('Configuracion guardada solo en .env. No compartas ese archivo.')


if __name__ == '__main__':
    main()
