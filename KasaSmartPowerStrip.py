import socket
import json
import struct
from builtins import bytes

class SmartPowerStrip(object):

    def __init__(self, ip, device_id=None, timeout=2.0, protocol='tcp'):
        self.ip = ip
        self.port = 9999
        self.protocol = protocol
        self.device_id = device_id
        self.sys_info = None
        self.timeout = timeout

        self.sys_info = self.get_system_info()['system']['get_sysinfo']

        if not self.device_id:
            self.device_id = self.sys_info['deviceId']

    def set_wifi_credentials(self, ssid, psk, key_type='3'):
        '''
        :param ssid: router ssid
        :param psk: router passkey
        :param key_type: 3 is WPA2, 2 might be WPA and 1 might be WEP?
        :return: command response
        '''

        wifi_command = '{"netif":{"set_stainfo":{"ssid":"' + ssid + '","password":"' + \
                       psk + '","key_type":' + key_type + '}}}'

        return self.send_command(wifi_command, self.protocol)

    def set_cloud_server_url(self, server_url=''):

        server_command = '{"cnCloud":{"set_server_url":{"server":"' + server_url + '"}}}'

        return self.send_command(server_command, self.protocol)

    def get_system_info(self):

        return self._udp_send_command('{"system":{"get_sysinfo":{}}}')

    def get_realtime_energy_info(self, plug_num=None, plug_name=None):

        plug_id = self._get_plug_id(plug_num=plug_num, plug_name=plug_name)

        energy_command = '{"context":{"child_ids":["' + plug_id + '"]},"emeter":{"get_realtime":{}}}'

        response = self.send_command(energy_command, self.protocol)

        realtime_energy_data = response['emeter']['get_realtime']

        return realtime_energy_data

    def get_historical_energy_info(self, month, year, plug_num=None, plug_name=None):

        plug_id = self._get_plug_id(plug_num=plug_num, plug_name=plug_name)

        energy_command = '{"context":{"child_ids":["' + plug_id + '"]},' + \
                         '"emeter":{"get_daystat":{"month": ' + month + ',"year":' + year + '}}}'

        response = self.send_command(energy_command, self.protocol)

        historical_energy_data = response['emeter']['get_daystat']['day_list']

        return historical_energy_data

    def toggle_relay_leds(self, state):

        state_int = self._get_plug_state_int(state, reverse=True)

        led_command = '{"system":{"set_led_off":{"off":' + str(state_int) + '}}}'

        return self.send_command(led_command, self.protocol)

    def set_plug_name(self, plug_num, plug_name):

        plug_id = self._get_plug_id(plug_num=plug_num)

        set_name_command = '{"context":{"child_ids":["' + plug_id + \
                           '"]},"system":{"set_dev_alias":{"alias":"' + plug_name + '"}}}'

        return self.send_command(set_name_command, self.protocol)

    def get_plug_info(self, plug_num):

        target_plug = [plug for plug in self.sys_info['children'] if plug['id'] == str(int(plug_num)-1).zfill(2)]

        return target_plug

    # toggle multiple plugs by id or name
    def toggle_plugs(self, state, plug_num_list=None, plug_name_list=None):

        state_int = self._get_plug_state_int(state)

        plug_id_list_str = self._get_plug_id_list_str(plug_num_list=plug_num_list, plug_name_list=plug_name_list)

        all_relay_command = '{"context":{"child_ids":' + plug_id_list_str + '},' + \
                            '"system":{"set_relay_state":{"state":' + str(state_int) + '}}}'

        return self.send_command(all_relay_command, self.protocol)

    # toggle a single plug
    def toggle_plug(self, state, plug_num=None, plug_name=None):

        state_int = self._get_plug_state_int(state)

        plug_id = self._get_plug_id(plug_num=plug_num, plug_name=plug_name)

        relay_command = '{"context":{"child_ids":["' + plug_id + '"]},' + \
                    '"system":{"set_relay_state":{"state":' + str(state_int) + '}}}'

        return self.send_command(relay_command, self.protocol)

    def reboot(self, delay=1):
        reboot_command = '{"system":{"reboot":{"delay":' + str(delay) + '}}}'
        return self.send_command(reboot_command, self.protocol)

    # manually send a command
    def send_command(self, command, protocol='tcp'):

        if protocol == 'tcp':
            return self._tcp_send_command(command)
        elif protocol == 'udp':
            return self._udp_send_command(command)
        else:
            raise ValueError("Protocol must be 'tcp' or 'udp'")

    def _get_plug_state_int(self, state, reverse=False):

        if state.lower() == 'on':
            if reverse:
                state_int = 0
            else:
                state_int = 1
        elif state.lower() == 'off':
            if reverse:
                state_int = 1
            else:
                state_int = 0
        else:
            raise ValueError("Invalid state, must be 'on' or 'off'")

        return state_int

    # create a string with a list of plug_ids that can be inserted directly into a command
    def _get_plug_id_list_str(self, plug_num_list=None, plug_name_list=None):

        plug_id_list = []

        if plug_num_list:
            for plug_num in plug_num_list:

                # add as str to remove the leading u
                plug_id_list.append(str(self._get_plug_id(plug_num=plug_num)))

        elif plug_name_list:

            for plug_name in plug_name_list:
                # add as str to remove the leading u
                plug_id_list.append(str(self._get_plug_id(plug_name=plug_name)))

        # convert to double quotes and turn the whole list into a string
        plug_id_list_str = str(plug_id_list).replace("'", '"')

        return plug_id_list_str

    # get the plug child_id to be used with commands
    def _get_plug_id(self, plug_num=None, plug_name=None):

        if plug_num and self.device_id:
            plug_id = self.device_id + str(plug_num-1).zfill(2)

        elif plug_name and self.sys_info:
            target_plug = [plug for plug in self.sys_info['children'] if plug['alias'] == plug_name]
            if target_plug:
                plug_id = self.device_id + target_plug[0]['id']
            else:
                raise ValueError('Unable to find plug with name ' + plug_name)
        else:
            raise ValueError('Unable to find plug.  Provide a valid plug_num or plug_name')

        return plug_id

    def _tcp_send_command(self, command):

        sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_tcp.settimeout(self.timeout)
        sock_tcp.connect((self.ip, self.port))

        sock_tcp.send(self._encrypt_command(command))

        data = sock_tcp.recv(2048)
        sock_tcp.close()

        # the first 4 chars are the length of the command so can be excluded
        return json.loads(self._decrypt_command(data[4:]))

    def _udp_send_command(self, command):

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.settimeout(self.timeout)

        addr = (self.ip, self.port)

        client_socket.sendto(self._encrypt_command(command, prepend_length=False), addr)

        data, server = client_socket.recvfrom(2048)

        return json.loads(self._decrypt_command(data))

    @staticmethod
    def _encrypt_command(string, prepend_length=True):

        key = 171
        result = b''

        # when sending get_sysinfo using udp the length of the command is not needed but
        #  with all other commands using tcp it is
        if prepend_length:
            result = struct.pack(">I", len(string))

        for i in bytes(string.encode('latin-1')):
            a = key ^ i
            key = a
            result += bytes([a])
        return result

    @staticmethod
    def _decrypt_command(string):

        key = 171
        result = b''
        for i in bytes(string):
            a = key ^ i
            key = i
            result += bytes([a])
        return result.decode('latin-1')
