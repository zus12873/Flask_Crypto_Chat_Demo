from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit
import uuid
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# 内存存储在线用户（格式：username -> {'sid': socket_id, 'public_key': 签名公钥（字符串）}）
online_users = {}
# 存储消息，每条消息是字典，包含：id, sender, recipient, ciphertext, signature, timestamp, recalled
messages = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat')
def chat():
    username = request.args.get('username')
    if not username:
        return redirect(url_for('index'))
    return render_template('chat.html', username=username)

# 注册事件：客户端发送用户名和签名公钥（用于数字认证）
@socketio.on('register')
def handle_register(data):
    username = data.get('username')
    public_key = data.get('public_key')
    if username:
        online_users[username] = {'sid': request.sid, 'public_key': public_key}
        # 向所有客户端广播最新在线用户列表（包含用户名和签名公钥）
        user_list = [{'username': k, 'public_key': v['public_key']} for k, v in online_users.items()]
        emit('user_list', user_list, broadcast=True)
        print(f"User registered: {username}")

@socketio.on('disconnect')
def handle_disconnect():
    for username, info in list(online_users.items()):
        if info['sid'] == request.sid:
            del online_users[username]
            user_list = [{'username': k, 'public_key': v['public_key']} for k, v in online_users.items()]
            emit('user_list', user_list, broadcast=True)
            print(f"User disconnected: {username}")

# 密钥交换请求：将发起方的 ECDH 公钥转发给目标用户
@socketio.on('key_exchange')
def handle_key_exchange(data):
    # data 包含：sender, recipient, ecdh_public（已转换为 base64 字符串）
    sender = data.get('sender')
    recipient = data.get('recipient')
    ecdh_public = data.get('ecdh_public')
    if recipient in online_users:
        recipient_sid = online_users[recipient]['sid']
        emit('key_exchange', {'sender': sender, 'ecdh_public': ecdh_public}, room=recipient_sid)

# 密钥交换响应：收到后转发给发起方
@socketio.on('key_exchange_response')
def handle_key_exchange_response(data):
    # data 包含：sender, recipient, ecdh_public
    sender = data.get('sender')
    recipient = data.get('recipient')
    ecdh_public = data.get('ecdh_public')
    if recipient in online_users:
        recipient_sid = online_users[recipient]['sid']
        emit('key_exchange_response', {'sender': sender, 'ecdh_public': ecdh_public}, room=recipient_sid)

# 接收消息事件（消息内容已经由客户端用共享密钥加密，并附带数字签名）
@socketio.on('send_message')
def handle_send_message(data):
    sender = data.get('sender')
    recipient = data.get('recipient')
    ciphertext = data.get('ciphertext')
    signature = data.get('signature')
    message_id = data.get('message_id', str(uuid.uuid4()))
    timestamp = int(time.time())
    msg = {
        'id': message_id,
        'sender': sender,
        'recipient': recipient,
        'ciphertext': ciphertext,
        'signature': signature,
        'timestamp': timestamp,
        'recalled': False
    }
    messages.append(msg)
    # 转发给目标用户（如果在线）以及发信人自己（便于本地显示）
    if recipient in online_users:
        recipient_sid = online_users[recipient]['sid']
        emit('receive_message', msg, room=recipient_sid)
    emit('receive_message', msg, room=request.sid)
    print(f"Message from {sender} to {recipient}: {ciphertext}")

# 消息撤回：发送撤回请求后，服务器将该消息标记为撤回，并通知双方更新显示
@socketio.on('recall_message')
def handle_recall_message(data):
    sender = data.get('sender')
    message_id = data.get('message_id')
    for msg in messages:
        if msg['id'] == message_id and msg['sender'] == sender:
            msg['recalled'] = True
            recipient = msg['recipient']
            if recipient in online_users:
                recipient_sid = online_users[recipient]['sid']
                emit('message_recalled', {'message_id': message_id}, room=recipient_sid)
            emit('message_recalled', {'message_id': message_id}, room=request.sid)
            print(f"Message {message_id} recalled by {sender}")
            break

if __name__ == '__main__':
    socketio.run(app, debug=True)
