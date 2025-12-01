from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.align import Align
from rich.table import Table
from rich.progress import BarColumn, Progress, TextColumn
from datetime import datetime
import math

class AssistantUI:
    def __init__(self):
        self.console = Console()
        self.layout = Layout()
        self.start_time = datetime.now()
        
        # State
        self.active_speakers = 1
        self.audio_level_db = -60.0
        self.audio_peak_db = -60.0
        self.history = [] # List of (time, speaker, text)
        self.live_transcript = [] # List of (time, speaker, text)
        self.current_question = "Waiting for question..."
        self.current_answer = "..."
        self.status = "ONLINE"
        
        self.setup_layout()

    def setup_layout(self):
        # Root layout: Top (Header+Monitor), Middle (History+Interaction), Bottom (Live Feed)
        self.layout.split_column(
            Layout(name="top", size=10),
            Layout(name="middle", ratio=1),
            Layout(name="bottom", size=10)
        )
        
        # Top: Left (Header/Status/Speakers), Right (Audio Monitor)
        self.layout["top"].split_row(
            Layout(name="header_panel", ratio=1),
            Layout(name="audio_monitor", ratio=1)
        )
        
        # Middle: Left (History), Right (Current Interaction)
        self.layout["middle"].split_row(
            Layout(name="history", ratio=1),
            Layout(name="interaction", ratio=1)
        )

    def update_audio_level(self, rms):
        # Convert RMS to dB
        if rms > 0:
            db = 20 * math.log10(rms)
        else:
            db = -60
        
        self.audio_level_db = max(-60, db)
        self.audio_peak_db = max(self.audio_peak_db, self.audio_level_db)
        # Decay peak slowly
        self.audio_peak_db -= 0.5

    def update_transcript(self, text_segment, speaker="SPEAKER_0"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.live_transcript.append((timestamp, speaker, text_segment))
        if len(self.live_transcript) > 10:
            self.live_transcript.pop(0)

    def add_history(self, speaker, text):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.history.append((timestamp, speaker, text))
        if len(self.history) > 10:
            self.history.pop(0)

    def set_active_speakers(self, count):
        self.active_speakers = count

    def set_question(self, question):
        self.current_question = question
        self.add_history("S0", question)

    def set_answer(self, answer):
        self.current_answer = answer
        self.add_history("ANS", answer)

    def get_duration(self):
        delta = datetime.now() - self.start_time
        return str(delta).split('.')[0]

    def generate_header_panel(self):
        grid = Table.grid(expand=True)
        grid.add_column()
        
        # Header Info
        grid.add_row(f"[bold]INTERVIEW ASSISTANT v1.3.0[/bold] - {self.status}")
        grid.add_row(f"SESSION ID: int-20231027-002 | DURATION: {self.get_duration()}")
        grid.add_row(Text("-" * 40, style="dim"))
        
        # Speakers
        grid.add_row(f"[bold]SPEAKERS DETECTED: {self.active_speakers}[/bold]")
        grid.add_row("  - SPEAKER_0 (Interviewer) [Active]")
        grid.add_row("  - SPEAKER_1 (Candidate)   [Listening]")
        
        return Panel(grid, title="SYSTEM STATUS", border_style="blue")

    def generate_audio_monitor(self):
        grid = Table.grid(expand=True)
        grid.add_column()
        
        # Stats
        grid.add_row(f"PEAK: {self.audio_peak_db:.1f}dB | AVG: {self.audio_level_db:.1f}dB")
        grid.add_row("CHANNELS: 1 (Mono) | RATE: 16kHz")
        grid.add_row(Text("-" * 40, style="dim"))
        
        # Visualizer Bar
        # Map -60dB to 0dB range to 0-20 chars
        width = 40
        normalized = (self.audio_level_db + 60) / 60 # 0 to 1
        filled = int(normalized * width)
        filled = max(0, min(width, filled))
        
        bar = "█" * filled + "░" * (width - filled)
        grid.add_row(f"[L] {bar} [R]")
        grid.add_row(f"    [-60dB]{' '*(width-12)}[0dB]")
        
        return Panel(grid, title="AUDIO INPUT MONITOR", border_style="cyan")

    def generate_history_panel(self):
        text = Text()
        for t, s, c in self.history:
            if s == "ANS":
                text.append(f"[{t}] ", style="dim")
                text.append(f"ANS: {c}\n", style="green")
            else:
                text.append(f"[{t}] ", style="dim")
                text.append(f"{s}: {c}\n", style="white")
        
        return Panel(text, title="CONVERSATION HISTORY", border_style="white")

    def generate_interaction_panel(self):
        grid = Table.grid(expand=True)
        grid.add_column()
        
        grid.add_row("[bold]SPEAKER_0 (Interviewer):[/bold]")
        grid.add_row(Text("-" * 30, style="dim"))
        grid.add_row(f"[bold white]{self.current_question}[/bold white]")
        grid.add_row("")
        grid.add_row("[bold]MODEL (Ollama):[/bold]")
        grid.add_row(Text("-" * 30, style="dim"))
        grid.add_row(f"[green]{self.current_answer}[/green]")
        
        return Panel(grid, title="CURRENT INTERACTION", border_style="yellow")

    def generate_live_feed(self):
        text = Text()
        for t, s, c in self.live_transcript:
            text.append(f"[{t}] {s}: ", style="bold cyan")
            text.append(f"{c}\n")
            
        return Panel(text, title="LIVE TRANSCRIPTION & SPEAKER FEED", border_style="magenta")

    def generate_view(self):
        self.layout["header_panel"].update(self.generate_header_panel())
        self.layout["audio_monitor"].update(self.generate_audio_monitor())
        self.layout["history"].update(self.generate_history_panel())
        self.layout["interaction"].update(self.generate_interaction_panel())
        self.layout["bottom"].update(self.generate_live_feed())
        
        return self.layout
