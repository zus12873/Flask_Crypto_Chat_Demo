import unittest
from app import app, socketio
from flask_socketio import SocketIOTestClient
import time

class TestApp(unittest.TestCase):

    def setUp(self):
        """在每个测试前启动 Flask 测试客户端"""
        self.client = app.test_client()
        
        # 使用 Flask 的测试服务器并传递给 SocketIOTestClient
        self.socket_client = socketio.test_client(app)

    def tearDown(self):
        """测试后关闭客户端"""
        self.socket_client.disconnect()

    def test_user_registration(self):
        """测试用户注册功能"""
        # 模拟客户端1注册
        self.socket_client.emit('register', {'username': 'a', 'public_key': 'public_key_1'})
        
        # 监听并验证是否接收到了在线用户列表
        received = self.socket_client.get_received()
        user_list = received[0]['args'][0]
        self.assertIn('a', [user['username'] for user in user_list])

    def test_key_exchange(self):
        """测试密钥交换功能"""
        # 模拟客户端1和客户端2注册
        self.socket_client.emit('register', {'username': 'a', 'public_key': 'public_key_a'})
        self.socket_client.emit('register', {'username': 'b', 'public_key': 'public_key_b'})
        
        # 模拟客户端1请求密钥交换
        self.socket_client.emit('key_exchange', {'sender': 'a', 'recipient': 'b', 'ecdh_public': 'ecdh_public_1'})

        # 监听客户端2的密钥交换事件
        received = self.socket_client.get_received()
        key_exchange_event = next((event for event in received if event['name'] == 'key_exchange'), None)
        
        # 确保接收到了正确的事件
        self.assertIsNotNone(key_exchange_event)
        self.assertEqual(key_exchange_event['args'][0]['sender'], 'a')

    def test_send_message(self):
        """测试消息发送功能"""
        # 模拟客户端1和客户端2注册
        self.socket_client.emit('register', {'username': 'a', 'public_key': 'public_key_1'})
        self.socket_client.emit('register', {'username': 'b', 'public_key': 'public_key_2'})

        # 模拟客户端1发送加密消息
        self.socket_client.emit('send_message', {
            'sender': 'a',
            'recipient': 'b',
            'ciphertext': 'encrypted_message',
            'signature': 'signature',
            'message_id': 'msg_123'
        })

        # 监听客户端2接收到的消息
        received = self.socket_client.get_received()
        receive_message_event = next((event for event in received if event['name'] == 'receive_message'), None)
        
        # 确保接收到了正确的事件
        self.assertIsNotNone(receive_message_event)
        self.assertEqual(receive_message_event['args'][0]['ciphertext'], 'encrypted_message')

    def test_recall_message(self):
        """测试消息撤回功能"""
        # 模拟客户端1和客户端2注册
        self.socket_client.emit('register', {'username': 'a', 'public_key': 'public_key_1'})
        self.socket_client.emit('register', {'username': 'b', 'public_key': 'public_key_2'})

        # 模拟客户端1发送消息
        self.socket_client.emit('send_message', {
            'sender': 'a',
            'recipient': 'b',
            'ciphertext': 'encrypted_message',
            'signature': 'signature',
            'message_id': 'msg_123'
        })

        # 模拟客户端1撤回消息
        self.socket_client.emit('recall_message', {'sender': 'a', 'message_id': 'msg_123'})

        # 监听客户端2收到的撤回消息通知
        received = self.socket_client.get_received()
        message_recalled_event = next((event for event in received if event['name'] == 'message_recalled'), None)

        # 确保接收到了正确的事件
        self.assertIsNotNone(message_recalled_event)
        self.assertEqual(message_recalled_event['args'][0]['message_id'], 'msg_123')

if __name__ == '__main__':
    unittest.main()
