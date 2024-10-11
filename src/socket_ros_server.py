# pylint: disable=pointless-string-statement
import asyncio, signal

import sys

if sys.version_info[:2] >= (3, 7):
    from asyncio import get_running_loop
else:
    from asyncio import _get_running_loop as get_running_loop

import rospy
from typing import Tuple
from enum import Enum

from utils import get_data_class, process_class_data

class ErrorCode(Enum):
    OK = 0
    PUBLISHER_ALREADY_EXISTS = 1
    BAD_DATA = 2
    PUBLISHER_IS_NOT_EXISTS = 3
    EXCEPTION = 4


class SocketRosServer:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.publishers = {}


    def run(self):
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.start_server())
            # asyncio.run(self.start_server())
        except KeyboardInterrupt:
            print("Server stopped manually.")


    async def start_server(self):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)

        addr = server.sockets[0].getsockname()
        print(f"Serving on {addr}")

        # Handle shutdown signals
        loop = get_running_loop()
        stop_event = asyncio.Event()

        def handle_shutdown(*args):
            stop_event.set()

        loop.add_signal_handler(signal.SIGINT, handle_shutdown)
        loop.add_signal_handler(signal.SIGTERM, handle_shutdown)

        await stop_event.wait()
        rospy.loginfo("Shutting down server...")


    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        print(f"Connected to {addr}")

        try:
            while True:
                data = await reader.read(1024)

                if not data:
                    break

                message = data.decode(encoding='utf-8')

                print(f"Received {message} from {addr}")

                # Process the message and prepare a response
                code, desc = self.process_data(message)
                response = ";".join([str(code.value), desc])

                writer.write(response.encode(encoding='utf-8'))
                await writer.drain()  # Make sure data is sent

        except asyncio.CancelledError:
            print(f"Connection with {addr} was cancelled")
        finally:
            writer.close()
            await writer.wait_closed()
        print(f"Connection with {addr} closed")


    def process_data(self, data) -> Tuple[ErrorCode, str]:
        try:
            """
            data example:
                '0;/cmd_vel;geometry_msgs/Twist'
                '1;/cmd_vel;geometry_msgs/Twist;{ "linear_x": 3.0 }'
            """
            separated_data = data.split(';')

            if len(separated_data) < 3:
                return ErrorCode.BAD_DATA, 'Separated data len less than 3'

            if separated_data[0] == '0':
                publishers = self.publishers.keys()
                if separated_data[1] not in publishers:
                    cls = get_data_class(separated_data[2])
                    if cls is not None:
                        self.publishers[separated_data[1]] = rospy.Publisher(separated_data[1], cls, queue_size=10)
                    else:
                        return ErrorCode.BAD_DATA, f'Unknown class name: {separated_data[2]}'
                else:
                    return ErrorCode.PUBLISHER_ALREADY_EXISTS, f'Publisher {separated_data[1]} already exists'
            elif separated_data[0] == '1':

                if len(separated_data) < 4:
                    return ErrorCode.BAD_DATA, 'Separated data len less than 3'

                publishers = self.publishers.keys()
                if separated_data[1] in publishers:
                    cls = get_data_class(separated_data[2])
                    if cls is not None:
                        data = process_class_data(separated_data[2], separated_data[3])
                        if data is not None:
                            print('Publish: ', separated_data[1], data)
                            self.publishers[separated_data[1]].publish(data)
                        else:
                            return ErrorCode.BAD_DATA, f'Cannot parse data: {separated_data[3]} for type "{separated_data[2]}"'
                    else:
                        return ErrorCode.BAD_DATA, f'Unknown class name: {separated_data[2]}'
                else:
                    return ErrorCode.PUBLISHER_IS_NOT_EXISTS, f"Publisher {separated_data[1]} does not exist"
            else:
                return ErrorCode.BAD_DATA, f'Unknown key: {separated_data[0]}'
        except Exception as e:
            return ErrorCode.EXCEPTION, f'Process data error: {e}'

        return ErrorCode.OK, 'ok'

def main(argv):
    rospy.init_node('socket_ros_server', anonymous=True)
    sub = SocketRosServer(str(argv[1]), int(argv[2]))
    sub.run()

if __name__ == '__main__':
    main(sys.argv)