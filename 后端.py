#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
枫叶服务器平台后端
功能：用户认证、邮件发送、短信验证、订单处理
"""

from flask import Flask, request, jsonify, session
from flask_cors import CORS
import sqlite3
import hashlib
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
import json
import threading
import time
import random
from functools import wraps
import re

app = Flask(__name__)
app.secret_key = 'mapleserver_secret_key_2025'
app.config['SESSION_TYPE'] = 'filesystem'
CORS(app, supports_credentials=True)

# 数据库初始化
def init_db():
    conn = sqlite3.connect('mapleserver.db')
    cursor = conn.cursor()
    
    # 用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            balance REAL DEFAULT 0,
            total_spent REAL DEFAULT 0,
            server_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # 订单表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            plan_id INTEGER NOT NULL,
            plan_name TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            payment_method TEXT,
            transaction_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # 服务器表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS servers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            order_id INTEGER NOT NULL,
            plan_name TEXT NOT NULL,
            ip_address TEXT NOT NULL,
            ssh_port INTEGER DEFAULT 22,
            ssh_username TEXT DEFAULT 'root',
            ssh_password TEXT NOT NULL,
            panel_url TEXT,
            panel_username TEXT,
            panel_password TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (order_id) REFERENCES orders (id)
        )
    ''')
    
    # 验证码表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS verification_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT NOT NULL,
            code TEXT NOT NULL,
            type TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            is_used BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 邮件队列表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient TEXT NOT NULL,
            subject TEXT NOT NULL,
            content TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            retry_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sent_at TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# 初始化数据库
init_db()

# 邮件配置
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': 'your-email@gmail.com',
    'sender_password': 'your-app-password',
    'use_tls': True
}

# 短信配置（模拟）
SMS_CONFIG = {
    'api_key': 'your_sms_api_key',
    'api_secret': 'your_sms_api_secret',
    'sender': 'MapleServer'
}

# 装饰器：需要登录
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': '请先登录'}), 401
        return f(*args, **kwargs)
    return decorated_function

# 密码哈希
def hash_password(password):
    salt = secrets.token_hex(16)
    return salt + ':' + hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()

def verify_password(stored_password, provided_password):
    salt, hash_value = stored_password.split(':')
    computed_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode(), salt.encode(), 100000).hex()
    return hash_value == computed_hash

# 发送邮件函数
def send_email(to_email, subject, content):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # HTML内容
        html_content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(45deg, #3498db, #2ecc71); color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; background: #f9f9f9; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                .server-info {{ background: white; padding: 20px; border-radius: 5px; border-left: 4px solid #3498db; }}
                .important {{ color: #e74c3c; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>枫叶高防服务器</h1>
                    <p>专业级DDoS/CC攻击防御解决方案</p>
                </div>
                <div class="content">
                    {content}
                </div>
                <div class="footer">
                    <p>© 2025 枫叶网络科技有限公司 | QQ群: 1078205267</p>
                    <p>此邮件为系统自动发送，请勿回复</p>
                </div>
            </div>
        </body>
        </html>
        '''
        
        msg.attach(MIMEText(html_content, 'html'))
        
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            if EMAIL_CONFIG['use_tls']:
                server.starttls()
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"发送邮件失败: {e}")
        return False

# 邮件队列处理线程
def email_worker():
    while True:
        try:
            conn = sqlite3.connect('mapleserver.db')
            cursor = conn.cursor()
            
            # 获取待发送邮件
            cursor.execute('SELECT * FROM email_queue WHERE status = "pending" AND retry_count < 3 LIMIT 10')
            emails = cursor.fetchall()
            
            for email in emails:
                email_id, recipient, subject, content, status, retry_count, created_at, sent_at = email
                
                if send_email(recipient, subject, content):
                    # 发送成功
                    cursor.execute('''
                        UPDATE email_queue 
                        SET status = "sent", sent_at = CURRENT_TIMESTAMP 
                        WHERE id = ?
                    ''', (email_id,))
                else:
                    # 发送失败，增加重试计数
                    cursor.execute('''
                        UPDATE email_queue 
                        SET retry_count = retry_count + 1 
                        WHERE id = ?
                    ''', (email_id,))
                
                conn.commit()
            
            conn.close()
        except Exception as e:
            print(f"邮件队列处理错误: {e}")
        
        time.sleep(10)  # 每10秒检查一次

# 启动邮件工作线程
email_thread = threading.Thread(target=email_worker, daemon=True)
email_thread.start()

# 生成随机IP地址
def generate_ip():
    return f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"

# 生成随机密码
def generate_random_password(length=12):
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    return ''.join(random.choice(chars) for _ in range(length))

# API路由
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        phone = data.get('phone')
        password = data.get('password')
        sms_code = data.get('smsCode')
        
        # 验证数据
        if not all([username, email, phone, password, sms_code]):
            return jsonify({'success': False, 'message': '请填写所有必填字段'})
        
        if not re.match(r'^1[3-9]\d{9}$', phone):
            return jsonify({'success': False, 'message': '手机号码格式不正确'})
        
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            return jsonify({'success': False, 'message': '邮箱格式不正确'})
        
        if len(password) < 8:
            return jsonify({'success': False, 'message': '密码长度至少8位'})
        
        # 验证短信验证码
        conn = sqlite3.connect('mapleserver.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT code FROM verification_codes 
            WHERE phone = ? AND type = 'register' AND is_used = 0 AND expires_at > CURRENT_TIMESTAMP
            ORDER BY created_at DESC LIMIT 1
        ''', (phone,))
        
        result = cursor.fetchone()
        if not result or result[0] != sms_code:
            conn.close()
            return jsonify({'success': False, 'message': '验证码错误或已过期'})
        
        # 检查用户是否存在
        cursor.execute('SELECT id FROM users WHERE username = ? OR email = ? OR phone = ?', 
                      (username, email, phone))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': '用户名、邮箱或手机号已存在'})
        
        # 创建用户
        password_hash = hash_password(password)
        cursor.execute('''
            INSERT INTO users (username, email, phone, password_hash, balance) 
            VALUES (?, ?, ?, ?, ?)
        ''', (username, email, phone, password_hash, 0))
        
        user_id = cursor.lastrowid
        
        # 标记验证码为已使用
        cursor.execute('UPDATE verification_codes SET is_used = 1 WHERE phone = ? AND code = ?', 
                      (phone, sms_code))
        
        # 创建欢迎邮件
        welcome_content = f'''
            <h2>欢迎注册枫叶服务器平台！</h2>
            <p>尊敬的 {username}，</p>
            <p>感谢您注册枫叶高防服务器平台，您的账户已成功创建。</p>
            <div class="server-info">
                <p><strong>账户信息：</strong></p>
                <p>用户名：{username}</p>
                <p>邮箱：{email}</p>
                <p>注册时间：{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            </div>
            <p class="important">请妥善保管您的账户信息，不要泄露给他人。</p>
            <p>如果您有任何问题，请随时联系我们的客服QQ群：1078205267</p>
        '''
        
        cursor.execute('''
            INSERT INTO email_queue (recipient, subject, content) 
            VALUES (?, ?, ?)
        ''', (email, '欢迎注册枫叶服务器平台', welcome_content))
        
        conn.commit()
        
        # 创建用户会话
        session['user_id'] = user_id
        session['username'] = username
        
        user_data = {
            'id': user_id,
            'username': username,
            'email': email,
            'phone': phone,
            'balance': 0,
            'servers': 0,
            'totalSpent': 0
        }
        
        conn.close()
        return jsonify({'success': True, 'user': user_data})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        account = data.get('account')
        password = data.get('password')
        
        if not account or not password:
            return jsonify({'success': False, 'message': '请输入账号和密码'})
        
        conn = sqlite3.connect('mapleserver.db')
        cursor = conn.cursor()
        
        # 查找用户（支持用户名、邮箱、手机号登录）
        cursor.execute('''
            SELECT id, username, email, phone, password_hash, balance, 
                   (SELECT COUNT(*) FROM servers WHERE user_id = users.id AND status = 'active') as server_count,
                   (SELECT COALESCE(SUM(amount), 0) FROM orders WHERE user_id = users.id AND status = 'completed') as total_spent
            FROM users 
            WHERE (username = ? OR email = ? OR phone = ?) AND is_active = 1
        ''', (account, account, account))
        
        user = cursor.fetchone()
        
        if not user or not verify_password(user[4], password):
            conn.close()
            return jsonify({'success': False, 'message': '账号或密码错误'})
        
        # 更新最后登录时间
        cursor.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user[0],))
        
        # 创建会话
        session['user_id'] = user[0]
        session['username'] = user[1]
        
        user_data = {
            'id': user[0],
            'username': user[1],
            'email': user[2],
            'phone': user[3],
            'balance': user[5],
            'servers': user[6],
            'totalSpent': user[7]
        }
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'user': user_data})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/send-sms', methods=['POST'])
def send_sms():
    try:
        data = request.json
        phone = data.get('phone')
        
        if not phone or not re.match(r'^1[3-9]\d{9}$', phone):
            return jsonify({'success': False, 'message': '手机号码格式不正确'})
        
        # 生成6位验证码
        code = ''.join(random.choices('0123456789', k=6))
        
        # 保存验证码到数据库（有效期10分钟）
        expires_at = datetime.datetime.now() + datetime.timedelta(minutes=10)
        
        conn = sqlite3.connect('mapleserver.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO verification_codes (phone, code, type, expires_at) 
            VALUES (?, ?, 'register', ?)
        ''', (phone, code, expires_at))
        
        conn.commit()
        conn.close()
        
        # 这里应该调用真实的短信API
        # 模拟发送
        print(f"发送短信验证码到 {phone}: {code}")
        
        return jsonify({'success': True, 'message': '验证码已发送'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/pay', methods=['POST'])
@login_required
def pay():
    try:
        data = request.json
        user_id = session.get('user_id')
        plan_id = data.get('planId')
        amount = data.get('amount')
        
        # 获取套餐信息
        plans = {
            '1': {'name': '体验版', 'duration': 7, 'defense': '10G'},
            '2': {'name': '标准版', 'duration': 30, 'defense': '20G'},
            '3': {'name': '专业版', 'duration': 90, 'defense': '50G'},
            '4': {'name': '企业版', 'duration': 180, 'defense': '100G'},
            '5': {'name': '永久版', 'duration': 365*10, 'defense': '50G'}
        }
        
        plan_info = plans.get(str(plan_id))
        if not plan_info:
            return jsonify({'success': False, 'message': '套餐不存在'})
        
        conn = sqlite3.connect('mapleserver.db')
        cursor = conn.cursor()
        
        # 创建订单
        cursor.execute('''
            INSERT INTO orders (user_id, plan_id, plan_name, amount, status) 
            VALUES (?, ?, ?, ?, 'pending')
        ''', (user_id, plan_id, plan_info['name'], amount))
        
        order_id = cursor.lastrowid
        
        # 模拟支付成功
        transaction_id = f"TXN{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"
        
        # 更新订单状态
        cursor.execute('''
            UPDATE orders 
            SET status = 'completed', payment_method = 'alipay', 
                transaction_id = ?, completed_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (transaction_id, order_id))
        
        # 更新用户信息
        cursor.execute('''
            UPDATE users 
            SET total_spent = total_spent + ?, 
                server_count = server_count + 1 
            WHERE id = ?
        ''', (amount, user_id))
        
        # 创建服务器
        ip_address = generate_ip()
        ssh_password = generate_random_password()
        panel_password = generate_random_password()
        
        expires_at = datetime.datetime.now() + datetime.timedelta(days=plan_info['duration'])
        
        cursor.execute('''
            INSERT INTO servers (user_id, order_id, plan_name, ip_address, ssh_password, panel_url, panel_username, panel_password, expires_at) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, order_id, plan_info['name'], ip_address, ssh_password, 
              f"http://panel.{random.randint(1000, 9999)}.mapleserver.com:8888", 
              "admin", panel_password, expires_at))
        
        # 获取用户更新后的信息
        cursor.execute('SELECT balance, server_count, total_spent FROM users WHERE id = ?', (user_id,))
        user_info = cursor.fetchone()
        
        # 准备服务器开通邮件
        server_content = f'''
            <h2>服务器开通成功！</h2>
            <p>尊敬的 {session.get('username')}，</p>
            <p>您的服务器已成功开通，以下是服务器配置信息：</p>
            <div class="server-info">
                <p><strong>套餐信息：</strong></p>
                <p>套餐名称：{plan_info['name']}</p>
                <p>防御等级：{plan_info['defense']} DDoS防护</p>
                <p>开通时间：{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                <p>到期时间：{expires_at.strftime("%Y-%m-%d %H:%M:%S")}</p>
                
                <p><strong>服务器配置：</strong></p>
                <p>IP地址：{ip_address}</p>
                <p>SSH端口：22</p>
                <p>SSH用户名：root</p>
                <p>SSH密码：{ssh_password}</p>
                <p>控制面板：<a href="http://panel.{random.randint(1000, 9999)}.mapleserver.com:8888">点击访问</a></p>
                <p>面板用户名：admin</p>
                <p>面板密码：{panel_password}</p>
            </div>
            <p class="important">请立即修改默认密码！</p>
            <p>如果遇到任何问题，请联系客服QQ群：1078205267</p>
        '''
        
        # 获取用户邮箱
        cursor.execute('SELECT email FROM users WHERE id = ?', (user_id,))
        user_email = cursor.fetchone()[0]
        
        # 加入邮件队列
        cursor.execute('''
            INSERT INTO email_queue (recipient, subject, content) 
            VALUES (?, ?, ?)
        ''', (user_email, '服务器开通通知 - 枫叶高防服务器', server_content))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '支付成功',
            'orderId': order_id,
            'transactionId': transaction_id,
            'newBalance': user_info[0],
            'serverInfo': {
                'ip': ip_address,
                'sshPassword': ssh_password
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/user-info', methods=['GET'])
@login_required
def get_user_info():
    try:
        user_id = session.get('user_id')
        
        conn = sqlite3.connect('mapleserver.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, phone, balance,
                   (SELECT COUNT(*) FROM servers WHERE user_id = ? AND status = 'active') as server_count,
                   (SELECT COALESCE(SUM(amount), 0) FROM orders WHERE user_id = ? AND status = 'completed') as total_spent
            FROM users WHERE id = ?
        ''', (user_id, user_id, user_id))
        
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'})
        
        user_data = {
            'id': user[0],
            'username': user[1],
            'email': user[2],
            'phone': user[3],
            'balance': user[4],
            'servers': user[5],
            'totalSpent': user[6]
        }
        
        return jsonify({'success': True, 'user': user_data})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/orders', methods=['GET'])
@login_required
def get_orders():
    try:
        user_id = session.get('user_id')
        
        conn = sqlite3.connect('mapleserver.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, plan_name, amount, status, created_at 
            FROM orders 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        ''', (user_id,))
        
        orders = cursor.fetchall()
        conn.close()
        
        orders_list = []
        for order in orders:
            orders_list.append({
                'id': order[0],
                'plan': order[1],
                'amount': order[2],
                'status': order[3],
                'time': order[4]
            })
        
        return jsonify({'success': True, 'orders': orders_list})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/servers', methods=['GET'])
@login_required
def get_servers():
    try:
        user_id = session.get('user_id')
        
        conn = sqlite3.connect('mapleserver.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, plan_name, ip_address, ssh_port, status, created_at, expires_at 
            FROM servers 
            WHERE user_id = ? AND status = 'active'
            ORDER BY created_at DESC
        ''', (user_id,))
        
        servers = cursor.fetchall()
        conn.close()
        
        servers_list = []
        for server in servers:
            servers_list.append({
                'id': server[0],
                'plan': server[1],
                'ip': server[2],
                'port': server[3],
                'status': server[4],
                'created': server[5],
                'expires': server[6]
            })
        
        return jsonify({'success': True, 'servers': servers_list})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# 测试路由
@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({'success': True, 'message': '服务器正常运行'})

# 健康检查
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.datetime.now().isoformat()})

if __name__ == '__main__':
    print("启动枫叶服务器平台后端...")
    print(f"管理员邮箱: {EMAIL_CONFIG['sender_email']}")
    print("请确保已配置正确的邮箱和短信API密钥")
    print("服务启动在 http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)