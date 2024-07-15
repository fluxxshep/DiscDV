import numpy as np
import queue
from collections import deque
import discord
import resampy
import freedv


def generate_silence(nframes):
    return b'\x00\x00' * nframes


def stereo_to_mono(samples: bytes, output_bytes: bool = True):
    lchannel = b''
    rchannel = b''

    for i in range(0, len(samples), 4):
        lchannel += samples[i:i + 2]
        rchannel += samples[i + 2:i + 4]

    output = np.frombuffer(lchannel, dtype=np.int16)
    output = output + np.frombuffer(rchannel, dtype=np.int16)

    if not output_bytes:
        return output
    else:
        return output.tobytes()


def mono_to_stereo(samples: bytes):
    output = b''

    for i in range(0, len(samples), 2):
        output += samples[i:i + 2] * 2

    return output


class FreeDVSource(discord.AudioSource):
    def __init__(self, q: queue.Queue, _freedv: freedv.FreeDV700D):
        super().__init__()
        self.rx_queue = q
        self.fdv = _freedv

        self.n_samples_per_read = 3840
        self.audio_buffer = deque()

    def read(self) -> bytes:
        output = b''
        n_available_receive_samples = self.rx_queue.qsize()

        if n_available_receive_samples > self.fdv.get_nin() * 2:
            receive_samples = get_bytes_from_queue_nowait(self.rx_queue, self.fdv.get_nin() * 2)
            decoded_speech = self.fdv.rx(receive_samples)

            output_samples = mono_to_stereo(
                resampy.resample(np.frombuffer(decoded_speech, dtype=np.int16),
                                 8000, 48000).astype(np.int16).tobytes()
            )

            for sample in output_samples:
                self.audio_buffer.append(sample.to_bytes(1))

        if len(self.audio_buffer) > self.n_samples_per_read:
            for i in range(self.n_samples_per_read):
                output += self.audio_buffer.popleft()
        else:
            output += b'\x00' * self.n_samples_per_read

        return output


class FreeDVSink(discord.sinks.Sink):
    def __init__(self, q: queue.Queue, record_user_ids, _freedv: freedv.FreeDV700D):
        super().__init__()
        self.tx_queue = q
        self.record_user_ids = record_user_ids
        self.fdv = _freedv
        self.tx_enabled = False
        self.ptt = False
        self.tx_volume = 100

    def tx(self):
        nsamples = self.fdv.get_n_speech_samples() * 2
        audios_int16 = []

        for user_id, audio in self.audio_data.items():
            if user_id not in self.record_user_ids:
                continue

            audio.file.seek(0)

            audio_samples = audio.file.read(nsamples * 6 * 2)

            audio.file.seek(0)
            audio.file.truncate()

            if len(audio_samples) < nsamples * 6 * 2:
                audio_samples += b'\x00' * ((nsamples * 6 * 2) - len(audio_samples))

            audio_int16 = stereo_to_mono(audio_samples, output_bytes=False)
            audio_int16 = resampy.resample(audio_int16, 48000, 8000).astype(np.int16)

            if not np.array_equal(audio_int16, np.zeros(len(audio_int16), dtype=np.int16)):
                audios_int16.append(audio_int16)

        try:
            output_len = len(audios_int16[0])
            output_audio = np.zeros(output_len, dtype=np.int16)

            for audio in audios_int16:
                output_audio += audio

            output_audio = output_audio.tobytes()
            tx_data = self.fdv.tx(output_audio) if self.tx_enabled else None

        except IndexError:
            tx_data = None

        if tx_data:
            tx_int16 = np.frombuffer(tx_data, dtype=np.int16) * (self.tx_volume / 100)
            tx_data = tx_int16.tobytes()

            for data in tx_data:
                self.tx_queue.put(data)

            self.ptt = True

        else:
            self.ptt = False

        return self.ptt

    def set_tx_volume(self, level: int):
        self.tx_volume = level

    def enable_tx(self, value: bool):
        self.tx_enabled = value

    def cleanup(self):
        self.finished = True
        for file in self.audio_data.values():
            file.cleanup()


def get_bytes_from_queue_nowait(q: queue.Queue, num_items: int):
    output = b''
    for i in range(num_items):
        try:
            byte = q.get_nowait()
            output += byte
        except queue.Empty:
            break

    return output
