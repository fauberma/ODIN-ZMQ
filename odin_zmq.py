import zmq
import json
import struct


class OdinZMQ:
    def __init__(self, IP, port=9000):
        self.IP = IP
        self.port = port
        self.context = zmq.Context()

        print("Connecting to ODIN server")

        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(f"tcp://{self.IP}:{self.port}")

    #@classmethod
    # def send_request(cls, request):
    #     def wrap_REQ_REP(instance, *args):
    #         REQ = request(instance, *args)
    #         instance.socket.send_json(REQ)
    #         REP= instance.socket.recv()
    #         return json.loads(REP.decode('utf-8'))
    #     return wrap_REQ_REP
    #
    # def get_frame(self, xbegin=0, xend=1280, ybegin=0, yend=1024, quality=90, bitmap=False):
    #     request = {
    #         "cmd": "get_frame",
    #         "data": {
    #             "xbegin": xbegin,
    #             "xend": xend,
    #             "ybegin": ybegin,
    #             "yend": yend,
    #             "quality": quality,
    #             "bitmap": bitmap,
    #         }
    #     }
    #     self.socket.send_json(request)
    #     reply = self.socket.recv()
    #     width = struct.unpack('I', reply[0:4])
    #     height = struct.unpack('I', reply[4:8])
    #     return width, height, reply[8:]
    #
    # @send_request
    # def recording_start(self, num_frames=100, filtered=True):
    #     request = {
    #         "cmd": "recording_start",
    #         "data": {
    #             "num_frames": num_frames,
    #             "filtered": filtered,
    #         }
    #     }
    #     return request
    #
    # @send_request
    # def recording_stop(self):
    #     request = {
    #         "cmd": "recording_stop",
    #     }
    #     return request
    #
    # @send_request
    # def recording_status(self):
    #     request = {
    #         "cmd": "recording_status",
    #     }
    #     return request
    #
    # def recording_get_frame(self, frame, roi=0, background=False, bitmap=True, quality=90):
    #     request = {
    #         "cmd": "recording_get_frame",
    #         "data": {
    #             "frame": frame,
    #             "roi": roi,
    #             "background": background,
    #             "bitmap": bitmap,
    #             "quality": quality,
    #         }
    #     }
    #     self.socket.send_json(request)
    #     reply = self.socket.recv()
    #     return reply
    #
    # @send_request
    # def recording_values(self, frames, roi=0):
    #     request = {
    #         "cmd": "recording_values",
    #         "data": {
    #             "frames": frames,
    #             "roi": roi,
    #         }
    #     }
    #     return request
    #
    # @send_request
    # def get_all(self, ):
    #     request = {
    #         "cmd": "get_all",
    #     }
    #     return request
    #
    # @send_request
    # def set(self, name, value):
    #     request = {
    #         "cmd": "set",
    #         "data": {
    #             "name": name,
    #             "value": value,
    #         }
    #     }
    #     return request
    #
    # @send_request
    # def sorting_start(self, reset=False):
    #     request = {
    #         "cmd": "sorting_start",
    #         "data": {
    #             "reset": reset,
    #         }
    #     }
    #     return request
    #
    # @send_request
    # def sorting_status(self):
    #     request = {
    #         "cmd": "sorting_status",
    #     }
    #     return request

    def stream_configure(self, mode, roi=0):
        """
        Configure stream of parameters

        :param mode: str all|filtered
        :param roi: int 0|1
        :return: dict request dictionary
        """

        request = {
            "cmd": "stream_configure",
            "data": {
                "mode": mode,
                "roi": roi,
            }
        }

        self.socket.send_json(request)
        reply= self.socket.recv()
        return json.loads(reply.decode('utf-8'))

    def stream_get(self, mode=None):
        """
        Polling of new parameters. Needs prior stream_configure

        :param mode: None|"binary"
        :return: parameter either a json, or binary list of doubles
        """

        if mode == "binary":
            request = {
                "cmd": "stream_get",
                "data": {
                    "mode": mode,
                }
            }
            self.socket.send_json(request)
            mesg = self.socket.recv()
            return mesg

        else:
            request = {
                "cmd": "stream_get",
            }
            self.socket.send_json(request)
            mesg = self.socket.recv()
            return json.loads(mesg.decode('utf-8'))

    def close_socket(self):
        self.socket.close()
        self.context.term()
