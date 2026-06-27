import json
import os
import secrets
import psycopg2
import urllib.request
import urllib.parse
import hashlib

BASE_URL = "https://neptune-research-exploration.poehali.dev"
VK_REDIRECT_URI = f"{BASE_URL}/auth/vk/callback"
GOOGLE_REDIRECT_URI = f"{BASE_URL}/auth/google/callback"


def get_or_create_user(cur, email, name, vk_id=None, google_id=None):
    if vk_id:
        cur.execute("SELECT id, email FROM users WHERE vk_id = %s", (vk_id,))
        user = cur.fetchone()
        if not user and email and not email.endswith('@vk.local'):
            cur.execute("SELECT id, email FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
            if user:
                cur.execute("UPDATE users SET vk_id = %s WHERE id = %s", (vk_id, user[0]))
        if not user:
            dummy = hashlib.sha256(secrets.token_hex(32).encode()).hexdigest()
            cur.execute(
                "INSERT INTO users (email, password_hash, name, vk_id) VALUES (%s, %s, %s, %s) RETURNING id, email",
                (email, dummy, name, vk_id)
            )
            user = cur.fetchone()
    else:
        cur.execute("SELECT id, email FROM users WHERE google_id = %s", (google_id,))
        user = cur.fetchone()
        if not user:
            cur.execute("SELECT id, email FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
            if user:
                cur.execute("UPDATE users SET google_id = %s WHERE id = %s", (google_id, user[0]))
        if not user:
            dummy = hashlib.sha256(secrets.token_hex(32).encode()).hexdigest()
            cur.execute(
                "INSERT INTO users (email, password_hash, name, google_id) VALUES (%s, %s, %s, %s) RETURNING id, email",
                (email, dummy, name, google_id)
            )
            user = cur.fetchone()
    return user


def handler(event: dict, context) -> dict:
    """OAuth авторизация через ВКонтакте и Google. provider=vk|google, code=... в query параметрах."""
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': {'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET, POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type', 'Access-Control-Max-Age': '86400'}, 'body': ''}

    params = event.get('queryStringParameters') or {}
    provider = params.get('provider', 'vk')
    code = params.get('code')

    if provider == 'vk':
        if not code:
            vk_params = urllib.parse.urlencode({
                'client_id': os.environ['VK_CLIENT_ID'],
                'redirect_uri': VK_REDIRECT_URI,
                'scope': 'email',
                'response_type': 'code',
                'state': secrets.token_hex(16),
                'v': '5.131',
            })
            return {
                'statusCode': 200,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'auth_url': f"https://oauth.vk.com/authorize?{vk_params}"})
            }

        token_params = urllib.parse.urlencode({
            'client_id': os.environ['VK_CLIENT_ID'],
            'client_secret': os.environ['VK_CLIENT_SECRET'],
            'redirect_uri': VK_REDIRECT_URI,
            'code': code,
        })
        with urllib.request.urlopen(f"https://oauth.vk.com/access_token?{token_params}") as resp:
            token_data = json.loads(resp.read())

        if 'error' in token_data:
            return {'statusCode': 400, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps({'error': token_data.get('error_description', 'VK auth error')})}

        access_token = token_data['access_token']
        vk_user_id = str(token_data['user_id'])
        email = token_data.get('email') or f"vk_{vk_user_id}@vk.local"

        api_params = urllib.parse.urlencode({'user_ids': vk_user_id, 'fields': 'first_name,last_name', 'access_token': access_token, 'v': '5.131'})
        with urllib.request.urlopen(f"https://api.vk.com/method/users.get?{api_params}") as resp:
            vk_user = json.loads(resp.read()).get('response', [{}])[0]
        name = f"{vk_user.get('first_name', '')} {vk_user.get('last_name', '')}".strip()

        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        user = get_or_create_user(cur, email, name, vk_id=vk_user_id)

    else:  # google
        if not code:
            google_params = urllib.parse.urlencode({
                'client_id': os.environ['GOOGLE_CLIENT_ID'],
                'redirect_uri': GOOGLE_REDIRECT_URI,
                'scope': 'openid email profile',
                'response_type': 'code',
                'state': secrets.token_hex(16),
                'access_type': 'online',
            })
            return {
                'statusCode': 200,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'auth_url': f"https://accounts.google.com/o/oauth2/v2/auth?{google_params}"})
            }

        token_payload = urllib.parse.urlencode({
            'code': code,
            'client_id': os.environ['GOOGLE_CLIENT_ID'],
            'client_secret': os.environ['GOOGLE_CLIENT_SECRET'],
            'redirect_uri': GOOGLE_REDIRECT_URI,
            'grant_type': 'authorization_code',
        }).encode()
        req = urllib.request.Request('https://oauth2.googleapis.com/token', data=token_payload, method='POST')
        with urllib.request.urlopen(req) as resp:
            token_data = json.loads(resp.read())

        if 'error' in token_data:
            return {'statusCode': 400, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps({'error': token_data.get('error_description', 'Google auth error')})}

        access_token = token_data['access_token']
        req2 = urllib.request.Request('https://www.googleapis.com/oauth2/v2/userinfo', headers={'Authorization': f'Bearer {access_token}'})
        with urllib.request.urlopen(req2) as resp:
            userinfo = json.loads(resp.read())

        google_id = userinfo['id']
        email = userinfo.get('email') or f"google_{google_id}@google.local"
        name = userinfo.get('name', '')

        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        user = get_or_create_user(cur, email, name, google_id=google_id)

    user_id, user_email = user
    session_id = secrets.token_hex(32)
    cur.execute('INSERT INTO sessions (id, user_id) VALUES (%s, %s)', (session_id, user_id))
    conn.commit()
    cur.close()
    conn.close()

    return {
        'statusCode': 200,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'session_id': session_id, 'user_id': user_id, 'email': user_email, 'name': name})
    }
