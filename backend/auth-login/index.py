import json
import os
import hashlib
import secrets
import psycopg2

def handler(event: dict, context) -> dict:
    """Авторизация пользователя по email и паролю."""
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': {'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type', 'Access-Control-Max-Age': '86400'}, 'body': ''}

    body = json.loads(event.get('body') or '{}')
    email = body.get('email', '').strip().lower()
    password = body.get('password', '')

    if not email or not password:
        return {'statusCode': 400, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps({'error': 'Email и пароль обязательны'})}

    password_hash = hashlib.sha256(password.encode()).hexdigest()

    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()

    cur.execute('SELECT id, email FROM users WHERE email = %s AND password_hash = %s', (email, password_hash))
    user = cur.fetchone()

    if not user:
        cur.close()
        conn.close()
        return {'statusCode': 401, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps({'error': 'Неверный email или пароль'})}

    user_id, user_email = user

    session_id = secrets.token_hex(32)
    cur.execute('INSERT INTO sessions (id, user_id) VALUES (%s, %s)', (session_id, user_id))

    conn.commit()
    cur.close()
    conn.close()

    return {
        'statusCode': 200,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'session_id': session_id, 'user_id': user_id, 'email': user_email})
    }
