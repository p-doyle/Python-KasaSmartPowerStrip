import socket
import json
import struct


class SmartPowerStrip(object):

    def __init__(self, ip, device_id=None, timeout=2.0):
        self.ip = ip
        self.port = 9999
        self.device_id = device_id
        self.sys_info = None
        self.timeout = timeout

        # if the device ID isn't supplied it needs to be queried from
        # the device before any commands can be sent
        if not self.device_id:
            sys_info = json.loads(self.get_system_info())
            self.sys_info = sys_info['system']['get_sysinfo']
            self.device_id = self.sys_info['deviceId']

    def get_system_info(self):
        return self._udp_send_command('{"system":{"get_sysinfo":{}}}')

    def toggle_plug(self, state, plug_num=None, plug_name=None):

        plug_id = None

        if state.lower() == 'on':
            state_int = 1
        elif state.lower() == 'off':
            state_int = 0
        else:
            raise ValueError("invalid state, must be 'on' or 'off'")

        if plug_num and self.device_id:
            plug_id = self.device_id + str(plug_num-1).zfill(2)

        elif plug_name and self.sys_info:
            target_plug = [plug for plug in self.sys_info['children'] if plug['alias'] == plug_name]
            if target_plug:
                plug_id = self.device_id + str(int(target_plug[0]['id']) - 1).zfill(2)
            else:
                print('Unable to find plug with name ' + plug_name)

        if plug_id:
            relay_command = '{"context":{"child_ids":["' + plug_id + '"]},' + \
                        '"system":{"set_relay_state":{"state":' + str(state_int) + '}}}'
            return self._tcp_send_command(relay_command)

    def _tcp_send_command(self, command):
        print command
        sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_tcp.settimeout(self.timeout)
        sock_tcp.connect((self.ip, self.port))
        sock_tcp.send(self._encrypt_command(command))

        data = sock_tcp.recv(2048)
        sock_tcp.close()

        # the first 4 chars are the length of the command so can be excluded
        return self._decrypt_command(data[4:])

    def _udp_send_command(self, command):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.settimeout(self.timeout)

        addr = (self.ip, self.port)

        client_socket.sendto(self._encrypt_command(command, prepend_length=False), addr)

        data, server = client_socket.recvfrom(1024)

        return self._decrypt_command(data)

    @staticmethod
    def _encrypt_command(string, prepend_length=True):
        key = 171
        result = ''

        # when sending get_sysinfo using udp the length of the command is not needed but
        #  with all other commands using tcp it is
        if prepend_length:
            result = struct.pack('>I', len(string))

        for i in string:
            a = key ^ ord(i)
            key = a
            result += chr(a)
        return result

    @staticmethod
    def _decrypt_command(string):
        key = 171
        result = ''
        for i in string:
            a = key ^ ord(i)
            key = ord(i)
            result += chr(a)
        return result