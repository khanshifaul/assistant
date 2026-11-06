from faster_whisper import WhisperModel
import numpy as np
import logging
import time

class RealTimeTranscriber:
    def __init__(self, model_size="base.en", device="cpu", compute_type="int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        logging.info(f"Loading Whisper model: {model_size} on {device} with {compute_type}")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        logging.info("Whisper model loaded")

    def transcribe(self, audio_data):
        """
        Transcribes audio data.
        audio_data: numpy array of float32
        """
        if len(audio_data) == 0:
            return []

        # faster-whisper expects a float32 numpy array
        segments, info = self.model.transcribe(audio_data, beam_size=5)
        
        result = []
        for segment in segments:
            result.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text
            })
        return result
