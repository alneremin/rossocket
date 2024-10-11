
import sys
import socket
import json
import time

class SocketClient:

    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect()


    def connect(self):
        try:
            self.socket.connect((self.host, self.port))
        except Exception as e:
            print(f'Connection error: {e}')

    def send(self, data):
        try:
            self.socket.sendall(data)
            response = self.socket.recv(1024)
            return response
        except Exception as e:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connect()
            print(f'Send message error: {e}')

        return None


def main(argv):
    s = SocketClient(str(argv[1]), int(argv[2]))
    
    while True:
        resp = s.send("0;/mobile_base_controller/cmd_vel;geometry_msgs/Twist".encode(encoding='utf-8'))
        print(resp)

        command = { "linear_x": 1.0 }
        resp = s.send(f"1;/mobile_base_controller/cmd_vel;geometry_msgs/Twist;{json.dumps(command)}".encode('utf-8'))
        print(resp)
        
        time.sleep(0.5)

if __name__ == '__main__':
    main(sys.argv)