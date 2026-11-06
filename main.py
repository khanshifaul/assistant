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
WHISPER_SIZE = "tiny" # Faster model with multilingual support

def transcription_worker(audio_stream, transcriber, transcript_queue, ui):
    # VAD Parameters
    FRAME_DURATION = 0.1 # 100ms
    SILENCE_THRESHOLD = 0.005 
    SILENCE_DURATION = 0.5 
    MAX_DURATION = 3.0 # Reduced for faster updates
    
    audio_buffer = np.array([], dtype=np.float32)
    silence_counter = 0
    is_speaking = False
    
    logging.info("Transcription worker started with VAD")

    while audio_stream.running:
        chunk = audio_stream.get_audio_chunk()
        if chunk is not None:
            chunk = chunk.flatten()
            
            # Calculate RMS for UI and VAD
            rms = np.sqrt(np.mean(chunk**2))
            ui.update_audio_level(rms)
            
            # VAD Logic
            if rms > SILENCE_THRESHOLD:
                is_speaking = True
                silence_counter = 0
            else:
                if is_speaking:
                    silence_counter += len(chunk) / 16000.0 
            
            audio_buffer = np.concatenate((audio_buffer, chunk))
            buffer_duration = len(audio_buffer) / 16000.0
            
            should_transcribe = False
            
            if is_speaking and silence_counter >= SILENCE_DURATION:
                should_transcribe = True
            elif buffer_duration >= MAX_DURATION:
                should_transcribe = True

            if should_transcribe and len(audio_buffer) > 0:
                try:
                    segments = transcriber.transcribe(audio_buffer)
                    for segment in segments:
                        text = segment['text'].strip()
                        if text and len(text) > 1 and text not in ["You", "Thank you.", "Bye."]:
                            transcript_queue.put(text)
                            ui.update_transcript(text)
                except Exception as e:
                    logging.error(f"Transcription error: {e}")
                
                audio_buffer = np.array([], dtype=np.float32)
                is_speaking = False
                silence_counter = 0

def logic_worker(transcript_queue, slm, ui):
    full_transcript = ""
    while True:
        try:
            text = transcript_queue.get(timeout=1.0)
            full_transcript += text + " "
            
            if slm.is_question(text):
                ui.set_question(text)
                ui.set_answer("...") # Reset answer display
                
                # Stream the answer
                for chunk in slm.generate_answer(text, context=full_transcript[-2000:]):
                    ui.update_answer_stream(chunk)
                
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

    # Main Loop
    try:
        import msvcrt
        os.system('cls') # Clear console before starting UI
        with Live(ui.generate_view(), refresh_per_second=10, screen=True) as live:
            while True:
                # Handle keyboard input
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    if key == b'\xe0':  # Arrow key prefix
                        arrow = msvcrt.getch()
                        if arrow == b'K':  # LEFT arrow
                            ui.cycle_focus(-1)
                        elif arrow == b'M':  # RIGHT arrow
                            ui.cycle_focus(1)
                        elif arrow == b'H':  # UP arrow
                            ui.scroll(-1)
                        elif arrow == b'P':  # DOWN arrow
                            ui.scroll(1)
                
                live.update(ui.generate_view())
                time.sleep(0.05)
    except KeyboardInterrupt:
        logging.info("Stopping...")
    finally:
        audio_stream.stop()

if __name__ == "__main__":
    main()
