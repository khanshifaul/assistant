import threading
import queue
import time
import logging
import os
import sys
import numpy as np
from rich.live import Live

from src.audio_capture import AudioStream
from src.transcriber import RealTimeTranscriber
from src.llm_engine import InterviewAssistantSLM
from src.ui import AssistantUI

# Configuration
OLLAMA_MODEL = "phi3"
WHISPER_SIZE = "base.en"

def transcription_worker(audio_stream, transcriber, transcript_queue, ui):
    while audio_stream.running:
        chunk = audio_stream.get_audio_chunk()
        if chunk is not None:
            # Calculate RMS for UI
            rms = np.sqrt(np.mean(chunk**2))
            ui.update_audio_level(rms)
            
            segments = transcriber.transcribe(chunk.flatten())
            for segment in segments:
                text = segment['text']
                transcript_queue.put(text)
                ui.update_transcript(text)

def logic_worker(transcript_queue, slm, ui):
    full_transcript = ""
    while True:
        try:
            text = transcript_queue.get(timeout=1.0)
            full_transcript += text + " "
            
            if slm.is_question(text):
                ui.set_question(text)
                answer = slm.generate_answer(text, context=full_transcript[-2000:]) # Pass last 2000 chars as context
                ui.set_answer(answer)
                
        except queue.Empty:
            continue
        except Exception as e:
            logging.error(f"Logic worker error: {e}")

def main():
    # Setup logging
    logging.basicConfig(filename='assistant.log', level=logging.INFO)
    
    # Initialize components
    print("Initializing components...")
    try:
        ui = AssistantUI()
        ui.set_active_speakers(2) # Simulated for now
        audio_stream = AudioStream() # Default device
        transcriber = RealTimeTranscriber(model_size=WHISPER_SIZE)
        slm = InterviewAssistantSLM(model_name=OLLAMA_MODEL)
    except Exception as e:
        print(f"Initialization failed: {e}")
        return

    transcript_queue = queue.Queue()

    # Start threads
    audio_stream.start()
    
    t_transcribe = threading.Thread(
        target=transcription_worker, 
        args=(audio_stream, transcriber, transcript_queue, ui),
        daemon=True
    )
    t_transcribe.start()
    
    t_logic = threading.Thread(
        target=logic_worker, 
        args=(transcript_queue, slm, ui),
        daemon=True
    )
    t_logic.start()

    # Run UI
    try:
        with Live(ui.generate_view(), refresh_per_second=4) as live:
            while True:
                live.update(ui.generate_view())
                time.sleep(0.25)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        audio_stream.stop()

if __name__ == "__main__":
    main()
