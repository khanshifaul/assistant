import sounddevice as sd
import numpy as np
import queue
import logging

class AudioStream:
    def __init__(self, device_index=None, sample_rate=16000, block_size=1024):
        self.device_index = device_index
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.audio_queue = queue.Queue()
        self.running = False
        self.stream = None

    def callback(self, indata, frames, time, status):
        if status:
            logging.warning(f"Audio callback status: {status}")
        self.audio_queue.put(indata.copy())

    def start(self):
        if self.running:
            return
        
        try:
            self.stream = sd.InputStream(
                device=self.device_index,
                channels=1,
                samplerate=self.sample_rate,
                callback=self.callback,
                blocksize=self.block_size,
                dtype=np.float32
            )
            self.stream.start()
            self.running = True
            logging.info(f"Audio stream started on device {self.device_index}")
        except Exception as e:
            logging.error(f"Failed to start audio stream: {e}")
            raise

    def stop(self):
        if not self.running:
            return
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.running = False
        logging.info("Audio stream stopped")

    def get_audio_chunk(self):
        try:
            return self.audio_queue.get(timeout=0.5)
        except queue.Empty:
            return None

    @staticmethod
    def list_devices():
        return sd.query_devices()
