import abc
import subprocess
import sys
import os

# Eddystone Protocol specification
# https://github.com/google/eddystone/blob/master/protocol-specification.md
# Bluetooth Service UUID used by Eddystone
#  16bit: 0xfeaa (65194)
#  64bit: 0000FEAA-0000-1000-8000-00805F9B34FB


class BleCommunication(object):
    '''Bluetooth LE communication'''
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_data(mac):
        pass

    @abc.abstractmethod
    def find_ble_devices():
        pass


class BleCommunicationDummy(BleCommunication):
    '''TODO: Find some working BLE implementation for Windows and OSX'''

    @staticmethod
    def get_data(mac):
        return '0x0201060303AAFE1616AAFE10EE037275752E7669232A6843744641424644'

    @staticmethod
    def find_ble_devices():
        return [
            ('BC:2C:6A:1E:59:3D', ''),
            ('AA:2C:6A:1E:59:3D', '')
        ]


class BleCommunicationNix(BleCommunication):
    '''Bluetooth LE communication for Linux'''

    @staticmethod
    def start():
        print('Start receiving broadcasts')
        DEVNULL = subprocess.DEVNULL if sys.version_info > (3, 0) else open(os.devnull, 'wb')

        subprocess.call("sudo hciconfig hci0 reset", shell = True, stdout = DEVNULL)
        hcitool = subprocess.Popen(["sudo", "-n", "hcitool", "lescan", "--duplicates"], stdout = DEVNULL)
        hcidump = subprocess.Popen(['sudo', '-n', 'hcidump', '--raw'], stdout=subprocess.PIPE)
        return (hcitool, hcidump)

    @staticmethod
    def get_lines(hcidump):
        data = None
        try:
            for line in hcidump.stdout:
                line = line.decode()
                if line.startswith('> '):
                    yield data
                    data = line[2:].strip().replace(' ', '')
                elif line.startswith('< '):
                    data = None
                else:
                    if data:
                        data += line.strip().replace(' ', '')
        except KeyboardInterrupt as ex:
            return
        except Exception as ex:
            print(ex)
            return

    @staticmethod
    def stop(hcitool, hcidump):
        print('Stop receiving broadcasts')
        subprocess.call(['sudo', 'kill', str(hcidump.pid), '-s', 'SIGINT'])
        subprocess.call(["sudo", "-n", "kill", str(hcitool.pid), "-s", "SIGINT"])

    @staticmethod
    def get_data(mac):
        procs = BleCommunicationNix.start()

        data = None
        for line in BleCommunicationNix.get_lines(procs[1]):
            try:
                reverse_mac = line[14:][:12]
                correct_mac = ''.join(
                    reversed([reverse_mac[i:i + 2] for i in range(0, len(reverse_mac), 2)]))
            except:
                continue

            if mac.replace(':', '') == correct_mac:
                print('Data found')
                data = line[26:]
                break

        BleCommunicationNix.stop(procs[0], procs[1])
        return data

    @staticmethod
    def find_ble_devices():
        pass
