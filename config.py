# Audio configuration, these should be self-explanatory

audio_input_device = 0
audio_output_device = 0
tx_volume = 100

# Rig configuration

# Keep port as default!
# https://hamlib.sourceforge.net/html/rigctld.1.html

rigctld_cmd = ""  # put your rigctld command here
default_freq = 14236  # KHz
default_mode = 'USB'  # USB or LSB

# Don't touch anything below for regular use
if __name__ == '__main__':
    import pyaudio
    pa = pyaudio.PyAudio()

    print(f'Current selected input device (from radio): {audio_input_device}')
    print(f'Current selected output device (to radio): {audio_output_device}')
    print('Devices: ')

    for i in range(pa.get_device_count()):
        device_info = pa.get_device_info_by_index(i)

        print(f'Device {device_info['index']}: {device_info['name']}')