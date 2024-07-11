from ctypes import *
import platform


class FreeDV700D:
    def __init__(self):
        libname = None
        system = platform.system()

        if system == 'Linux':
            libname = './lib/libcodec2.so'
        elif system == 'Windows':
            libname = './lib/libcodec2.dll'

        assert libname is not None

        self.c_lib = CDLL(libname)

        self.c_lib.freedv_open.argtype = [c_int]
        self.c_lib.freedv_open.restype = c_void_p

        self.c_lib.freedv_close.argtype = [c_void_p]
        self.c_lib.freedv_close.restype = c_void_p

        self.c_lib.freedv_get_n_max_speech_samples.argtype = [c_void_p]
        self.c_lib.freedv_get_n_max_speech_samples.restype = c_int

        self.c_lib.freedv_get_n_speech_samples.argtype = [c_void_p]
        self.c_lib.freedv_get_n_speech_samples.restype = c_int

        self.c_lib.freedv_get_n_nom_modem_samples.argtype = [c_void_p]
        self.c_lib.freedv_get_n_nom_modem_samples.restype = c_int

        self.c_lib.freedv_get_sync.argtype = [c_void_p]
        self.c_lib.freedv_get_sync.restype = c_int

        self.c_lib.freedv_get_rx_status.argtype = [c_void_p]
        self.c_lib.freedv_get_rx_status.restype = c_int

        self.c_lib.freedv_nin.argtype = [c_void_p]
        self.c_lib.freedv_nin.restype = c_int

        self.c_lib.freedv_rx.argtype = [c_void_p, c_char_p, c_char_p]
        self.c_lib.freedv_rx.restype = c_int

        self.c_lib.freedv_tx.argtype = [c_void_p, c_char_p, c_char_p]
        self.c_lib.freedv_tx.restype = c_void_p

        FREEDV_MODE_700D = 7  # from freedv_api.h
        self.freedv = cast(self.c_lib.freedv_open(FREEDV_MODE_700D), c_void_p)

        self.n_speech_samples = self.c_lib.freedv_get_n_speech_samples(self.freedv)

        self.n_max_speech_samples = self.c_lib.freedv_get_n_max_speech_samples(self.freedv)
        self.speech_out = create_string_buffer(2 * self.n_max_speech_samples)

        self.n_nom_modem_samples = self.c_lib.freedv_get_n_nom_modem_samples(self.freedv)
        self.mod_out = create_string_buffer(2 * self.n_nom_modem_samples)

        self.analog_listen = False

    def close(self):
        self.c_lib.freedv_close(self.freedv)

    def get_sync(self):
        return self.c_lib.freedv_get_sync(self.freedv)

    def get_rx_status(self):
        return self.c_lib.freedv_get_rx_status(self.freedv)

    def get_nin(self):
        return self.c_lib.freedv_nin(self.freedv)

    def get_n_speech_samples(self):
        return self.n_speech_samples

    def listen_to_analog(self, val: bool):
        self.analog_listen = val

    def rx(self, demod_in):
        nin = self.get_nin()
        assert len(demod_in) == nin * 2

        nout = self.c_lib.freedv_rx(self.freedv, self.speech_out, demod_in)

        if self.get_rx_status() == 6 or self.analog_listen:
            return self.speech_out[:nout * 2]

        else:
            return b'\x00\x00'

    def tx(self, speech_in):
        assert len(speech_in) == self.get_n_speech_samples() * 2

        self.c_lib.freedv_tx(self.freedv, self.mod_out, speech_in)
        return self.mod_out
