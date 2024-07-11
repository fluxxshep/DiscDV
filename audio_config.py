audio_input_device = 3
audio_output_device = 6

if __name__ == '__main__':
    import pyaudio
    pa = pyaudio.PyAudio()

    print(f'Current selected input device (from radio): {audio_input_device}')
    print(f'Current selected output device (to radio): {audio_output_device}')
    print('Devices: ')

    for i in range(pa.get_device_count()):
        device_info = pa.get_device_info_by_index(i)

        print(f'Device {device_info['index']}: {device_info['name']}')
