"""Codifica la contraseña para una URI sin mostrar la entrada al teclear."""
import getpass
from urllib.parse import quote
print(quote(getpass.getpass('Password DB: '), safe=''))
