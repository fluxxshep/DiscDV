import socket
import subprocess
import shlex
import platform


class RigControl:
    def __init__(self, rigctld_cmd):
        system = platform.system()
        self.rigctld = None

        if system == 'Linux':
            self.rigctld = subprocess.Popen(shlex.split(rigctld_cmd))
        elif system == 'Windows':
            self.rigctld = subprocess.Popen(rigctld_cmd)

        assert isinstance(self.rigctld, subprocess.Popen)

        self.rigctld_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.rigctld_socket.connect(('localhost', 4532))
        self.busy = False

    def close(self):
        while self.busy:
            pass

        self.rigctld_socket.close()
        self.rigctld.terminate()

    def receive_line(self, decode: bool = True):
        recv_data = b''
        self.busy = True

        while True:
            data = self.rigctld_socket.recv(1)
            recv_data += data

            if data.decode() == '\n':
                break

        self.busy = False

        return recv_data.decode() if decode else recv_data

    def set_ptt(self, value: bool):
        ptt = 1 if value else 0
        self.rigctld_socket.send(f'T {ptt}\n'.encode())
        return self.receive_line()

    def get_ptt(self):
        self.rigctld_socket.send('t\n'.encode())
        return bool(int(self.receive_line()))

    def get_freq(self):
        self.rigctld_socket.send('f\n'.encode())
        return int(self.receive_line())

    def set_freq(self, freq: int):
        self.rigctld_socket.send(f'F {freq}\n'.encode())
        return self.receive_line()

    def get_mode(self):
        self.rigctld_socket.send('m\n'.encode())
        recv = self.receive_line()
        # recv_split = recv.split(' ')
        # mode = recv_split[0]
        # passband = int(recv_split[1])
        #
        # return mode, passband
        return recv

    def set_mode(self, mode: str, passband: int):
        self.rigctld_socket.send(f'M {mode} {passband}\n'.encode())
        return self.receive_line()
