import sqlite3

conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()

def init_db():
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        telegram_id INTEGER PRIMARY KEY,
        username TEXT,
        created_date TEXT,
        captcha_service TEXT,
        captcha_api_key TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        email TEXT,
        password TEXT,
        imap_pass TEXT,
        client_id TEXT,
        node_password TEXT,  
        points INTEGER DEFAULT 0,     
        FOREIGN KEY(user_id) REFERENCES users(telegram_id)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS proxies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        proxy TEXT,
        FOREIGN KEY(user_id) REFERENCES users(telegram_id)
    )''')

    conn.commit()

def add_user(telegram_id, username, created_date):
    cursor.execute('INSERT OR IGNORE INTO users (telegram_id, username, created_date) VALUES (?, ?, ?)', (telegram_id, username, created_date))
    conn.commit()

def get_user(telegram_id):
    cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
    return cursor.fetchone()

def update_user_captcha_service(telegram_id, captcha_service):
    cursor.execute('UPDATE users SET captcha_service = ? WHERE telegram_id = ?', (captcha_service, telegram_id))
    conn.commit()

def update_user_captcha_api_key(telegram_id, api_key):
    cursor.execute('UPDATE users SET captcha_api_key = ? WHERE telegram_id = ?', (api_key, telegram_id))
    conn.commit()

def add_accounts_to_user(user_id, accounts):
    for email, password, imap_pass in accounts:
        cursor.execute('INSERT INTO accounts (user_id, email, password, imap_pass) VALUES (?, ?, ?, ?)', (user_id, email, password, imap_pass))
    conn.commit()

def add_proxies_to_user(user_id, proxies):
    for proxy in proxies:
        cursor.execute('INSERT INTO proxies (user_id, proxy) VALUES (?, ?)', (user_id, proxy))
    conn.commit()

def get_user_accounts(user_id):
    cursor.execute('SELECT email, password, imap_pass FROM accounts WHERE user_id = ?', (user_id,))
    return cursor.fetchall()

def get_account_node(user_id, email):
    cursor.execute('SELECT client_id, node_password FROM accounts WHERE user_id = ? AND email = ?', (user_id, email))
    result = cursor.fetchone()
    if result and all(result):
        return result
    else:
        return (None, None)

def get_user_accounts_stats(user_id):
    cursor.execute('SELECT email, password, points FROM accounts WHERE user_id = ?', (user_id,))
    return cursor.fetchall()

def get_user_proxies(user_id):
    cursor.execute('SELECT proxy FROM proxies WHERE user_id = ?', (user_id,))
    return [row[0] for row in cursor.fetchall()]

def get_user_captcha_service_and_key(user_id):
    cursor.execute('SELECT captcha_service, captcha_api_key FROM users WHERE telegram_id = ?', (user_id,))
    result = cursor.fetchone()
    if result:
        return result
    else:
        return (None, None)

def update_account_points(user_id, email, points):
    cursor.execute('UPDATE accounts SET points = ? WHERE user_id = ? AND email = ?', (points, user_id, email))
    conn.commit()

def update_account_client_id(user_id, email, client_id):
    cursor.execute('UPDATE accounts SET client_id = ? WHERE user_id = ? AND email = ?', (client_id, user_id, email))
    conn.commit()

def update_account_node_password(user_id, email, node_password):
    cursor.execute('UPDATE accounts SET node_password = ? WHERE user_id = ? AND email = ?', (node_password, user_id, email))
    conn.commit()

def get_user_accounts_count(user_id):
    cursor.execute('SELECT COUNT(*) FROM accounts WHERE user_id = ?', (user_id,))
    return cursor.fetchone()[0]

def get_user_proxies_count(user_id):
    cursor.execute('SELECT COUNT(*) FROM proxies WHERE user_id = ?', (user_id,))
    return cursor.fetchone()[0]

def get_total_points(user_id):
    cursor.execute('SELECT SUM(points) FROM accounts WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()[0]
    if result is None:
        return 0
    return result

def delete_user_accounts(user_id):
    cursor.execute('DELETE FROM accounts WHERE user_id = ?', (user_id,))
    conn.commit()

def delete_user_proxies(user_id):
    cursor.execute('DELETE FROM proxies WHERE user_id = ?', (user_id,))
    conn.commit()