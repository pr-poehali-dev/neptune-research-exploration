import json
import os
import psycopg2

def handler(event: dict, context) -> dict:
    """Получение истории генераций пользователя по session_id."""
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': {'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type, X-Session-Id', 'Access-Control-Max-Age': '86400'}, 'body': ''}

    session_id = event.get('headers', {}).get('x-session-id', '')

    if not session_id:
        return {'statusCode': 401, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps({'error': 'Не авторизован'})}

    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()

    cur.execute('SELECT user_id FROM sessions WHERE id = %s AND expires_at > NOW()', (session_id,))
    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
        return {'statusCode': 401, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps({'error': 'Сессия истекла'})}

    user_id = row[0]
    cur.execute('SELECT id, prompt, image_url, created_at FROM generations WHERE user_id = %s ORDER BY created_at DESC LIMIT 50', (user_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    items = [{'id': r[0], 'prompt': r[1], 'image_url': r[2], 'created_at': r[3].isoformat()} for r in rows]

    return {
        'statusCode': 200,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'items': items})
    }
