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
        
        # Focus and Scroll State (for panel navigation like pm2 monit)
        self.scrollable_panels = ["history", "interaction", "live"]
        self.focus_index = 0  # 0=history, 1=interaction, 2=live
        self.scroll_offsets = {"history": 0, "interaction": 0, "live": 0}
        self.panel_heights = {"history": 10, "interaction": 10, "live": 8}

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


    def cycle_focus(self, direction):
        """Direction: -1 for LEFT, 1 for RIGHT"""
        self.focus_index = (self.focus_index + direction) % len(self.scrollable_panels)
        # Reset scroll when changing panels
        
    def scroll(self, direction):
        """Direction: -1 for UP (older), 1 for DOWN (newer)"""
        panel = self.scrollable_panels[self.focus_index]
        
        if direction < 0:  # UP - see older content
            self.scroll_offsets[panel] += 1
        else:  # DOWN - see newer content
            self.scroll_offsets[panel] -= 1
        
        # Calculate max scroll based on content
        data_len = 0
        if panel == "history":
            data_len = len(self.history)
        elif panel == "interaction":
            # Count lines in current answer
            data_len = len(self.current_answer.split('\n'))
        elif panel == "live":
            data_len = len(self.live_transcript)
        
        max_offset = max(0, data_len - self.panel_heights[panel])
        self.scroll_offsets[panel] = max(0, min(self.scroll_offsets[panel], max_offset))

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
        # Keep more history for scrolling
        if len(self.live_transcript) > 100:
            self.live_transcript.pop(0)

    def add_history(self, speaker, text):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.history.append((timestamp, speaker, text))
        # Keep more history for scrolling
        if len(self.history) > 100:
            self.history.pop(0)

    def set_active_speakers(self, count):
        self.active_speakers = count

    def set_question(self, question):
        self.current_question = question
        self.add_history("S0", question)

    def set_answer(self, answer):
        self.current_answer = answer
        self.add_history("ANS", answer)

    def update_answer_stream(self, chunk):
        if self.current_answer == "...":
            self.current_answer = ""
        self.current_answer += chunk
        # We don't add to history yet, only when done or we can update the last history item?
        # For simplicity, let's just update the display.
        # If we want history to update, we'd need to update the last item if it's ANS.
        if self.history and self.history[-1][1] == "ANS":
             self.history[-1] = (self.history[-1][0], "ANS", self.current_answer)
        else:
             self.add_history("ANS", self.current_answer)

    def get_duration(self):
        delta = datetime.now() - self.start_time
        return str(delta).split('.')[0]

    def generate_header_panel(self):
        grid = Table.grid(expand=True)
        grid.add_column()
        
        # Header Info
        grid.add_row(f"[bold]INTERVIEW ASSISTANT v1.3.0[/bold] - {self.status}")
        grid.add_row(f"SESSION ID: int-20231027-002 | DURATION: {self.get_duration()}")
        grid.add_row("[dim]Controls: [←→] Switch Panel | [↑↓] Scroll | [Ctrl+C] Quit[/dim]")
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
        
        # Apply scroll window
        offset = self.scroll_offsets["history"]
        height = self.panel_heights["history"]
        start = max(0, len(self.history) - height - offset)
        end = len(self.history) - offset if offset > 0 else len(self.history)
        visible = self.history[start:end]
        
        for t, s, c in visible:
            if s == "ANS":
                text.append(f"[{t}] ", style="dim")
                text.append(f"ANS: {c}\n", style="green")
            else:
                text.append(f"[{t}] ", style="dim")
                text.append(f"{s}: {c}\n", style="white")
        
        # Show focus indicator
        is_focused = self.scrollable_panels[self.focus_index] == "history"
        title = "CONVERSATION HISTORY [FOCUSED]" if is_focused else "CONVERSATION HISTORY"
        border = "green" if is_focused else "white"
        
        return Panel(text, title=title, border_style=border)

    def generate_interaction_panel(self):
        grid = Table.grid(expand=True)
        grid.add_column()
        
        grid.add_row("[bold]SPEAKER_0 (Interviewer):[/bold]")
        grid.add_row(Text("-" * 30, style="dim"))
        grid.add_row(f"[bold white]{self.current_question}[/bold white]")
        grid.add_row("")
        grid.add_row("[bold]MODEL (Ollama):[/bold]")
        grid.add_row(Text("-" * 30, style="dim"))
        
        # Apply scroll to answer if it's long
        answer_lines = self.current_answer.split('\n')
        offset = self.scroll_offsets["interaction"]
        height = self.panel_heights["interaction"]
        start = max(0, len(answer_lines) - height - offset)
        end = len(answer_lines) - offset if offset > 0 else len(answer_lines)
        visible_answer = '\n'.join(answer_lines[start:end])
        
        grid.add_row(f"[green]{visible_answer}[/green]")
        
        # Show focus indicator
        is_focused = self.scrollable_panels[self.focus_index] == "interaction"
        title = "CURRENT INTERACTION [FOCUSED]" if is_focused else "CURRENT INTERACTION"
        border = "green" if is_focused else "yellow"
        
        return Panel(grid, title=title, border_style=border)

    def generate_live_feed(self):
        text = Text()
        
        # Apply scroll window
        offset = self.scroll_offsets["live"]
        height = self.panel_heights["live"]
        start = max(0, len(self.live_transcript) - height - offset)
        end = len(self.live_transcript) - offset if offset > 0 else len(self.live_transcript)
        visible = self.live_transcript[start:end]
        
        for t, s, c in visible:
            text.append(f"[{t}] {s}: ", style="bold cyan")
            text.append(f"{c}\n")
        
        # Show focus indicator
        is_focused = self.scrollable_panels[self.focus_index] == "live"
        title = "LIVE TRANSCRIPTION [FOCUSED]" if is_focused else "LIVE TRANSCRIPTION & SPEAKER FEED"
        border = "green" if is_focused else "magenta"
        
        return Panel(text, title=title, border_style=border)

    def generate_view(self):
        self.layout["header_panel"].update(self.generate_header_panel())
        self.layout["audio_monitor"].update(self.generate_audio_monitor())
        self.layout["history"].update(self.generate_history_panel())
        self.layout["interaction"].update(self.generate_interaction_panel())
        self.layout["bottom"].update(self.generate_live_feed())
        
        return self.layout
