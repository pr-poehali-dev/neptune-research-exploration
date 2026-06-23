import json
import os
import urllib.request
import psycopg2

def handler(event: dict, context) -> dict:
    """Генерация изображения через gpt-image-1 (Promptra API) с сохранением в историю."""
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': {'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type, X-Session-Id', 'Access-Control-Max-Age': '86400'}, 'body': ''}

    body = json.loads(event.get('body') or '{}')
    prompt = body.get('prompt', '').strip()
    session_id = event.get('headers', {}).get('x-session-id') or body.get('session_id', '')

    if not prompt:
        return {'statusCode': 400, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps({'error': 'Prompt обязателен'})}

    api_key = os.environ['PROMPTRA_API_KEY']

    payload = json.dumps({
        'model': 'gpt-image-1',
        'prompt': prompt,
        'n': 1,
        'size': '1024x1024',
        'response_format': 'url'
    }).encode('utf-8')

    req = urllib.request.Request(
        'https://api.promptra.ru/v1/images/generations',
        data=payload,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        },
        method='POST'
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode('utf-8'))

    image_url = result['data'][0]['url']

    if session_id:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        cur.execute('SELECT user_id FROM sessions WHERE id = %s AND expires_at > NOW()', (session_id,))
        row = cur.fetchone()
        if row:
            user_id = row[0]
            cur.execute('INSERT INTO generations (user_id, prompt, image_url) VALUES (%s, %s, %s)', (user_id, prompt, image_url))
            conn.commit()
        cur.close()
        conn.close()

    return {
        'statusCode': 200,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'url': image_url})
    }
