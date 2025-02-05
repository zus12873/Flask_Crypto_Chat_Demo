from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# 用于存储消息的列表
messages = []

@app.route('/')
def index():
    return render_template('index.html', messages=messages)

@socketio.on('send_message')
def handle_message(data):
    message = data.get('message')
    if message:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_message = {
            'text': message,
            'timestamp': timestamp
        }
        messages.append(new_message)
        emit('new_message', new_message, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
