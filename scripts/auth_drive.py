"""
auth_drive.py — Flujo OAuth interactivo en terminal para servidores remotos.
"""
import os
from pathlib import Path
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/drive']
DIR_ROOT = Path(__file__).resolve().parent.parent
CLIENT_SECRET = os.getenv('DRIVE_CLIENT_SECRET', str(DIR_ROOT / 'client_secret.json'))
TOKEN_FILE    = os.getenv('DRIVE_TOKEN_FILE', str(DIR_ROOT / 'token_drive.json'))

if __name__ == '__main__':
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRET,
        SCOPES,
        redirect_uri='http://localhost:8085/'
    )
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
    
    print('========================================================================')
    print('AUTORIZACIÓN DE GOOGLE DRIVE EN SERVIDOR REMOTO')
    print('========================================================================')
    print('\n1. Abre este enlace en el navegador de tu computador:')
    print(auth_url)
    print('\n2. Inicia sesión con la cuenta dueña de la carpeta de Drive y dale "Permitir".')
    print('3. Copia la URL completa donde falle la redirección (http://localhost:8085/?...)')
    print('   y pégala aquí abajo en la misma terminal donde corre este script:\n')
    
    url_respuesta = input('Pega la URL de redirección completa: ').strip()
    
    flow.fetch_token(authorization_response=url_respuesta)
    creds = flow.credentials
    with open(TOKEN_FILE, 'w') as token:
        token.write(creds.to_json())
    print(f'\n✓ ¡Autorización exitosa! Token guardado en: {TOKEN_FILE}')
