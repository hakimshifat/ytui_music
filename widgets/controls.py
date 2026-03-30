"""Player control buttons widget."""

from textual.widgets import Button
from textual.containers import Horizontal
from textual.widgets import Static


class PlayerControls(Static):
    """Container for player buttons.

    Provides playback control buttons: previous, play/pause, next, stop.
    Buttons are clicked only, not focused via Tab.
    """

    def compose(self) -> Static.ComposeResult:
        with Horizontal(classes="controls_bar"):
            yield Button("⏮", id="btn_prev", variant="primary")
            yield Button("⏯", id="btn_play_pause", variant="warning")
            yield Button("⏭", id="btn_next", variant="primary")
            yield Button("Stop", id="btn_stop", variant="error")

    def on_mount(self) -> None:
        """Disable focus on all buttons after mount."""
        for button in self.query(Button):
            button.can_focus = False
