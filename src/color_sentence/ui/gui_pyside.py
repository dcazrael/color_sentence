from __future__ import annotations

from dataclasses import replace

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from color_sentence.config.config import ComputeConfig
from color_sentence.config.types import ComputeMode, ComputeResult
from color_sentence.core.engine import compute_color, prepare_engine
from color_sentence.tts.tts_gtts import GttsSynthesizer
from color_sentence.tts.tts_runner import TtsRunner
from color_sentence.config.gui_config import (
    WINDOW_MIN_WIDTH,
    FONT_POINT_SIZE,
    PADDING_PX,
    SPACING_PX,
    INPUT_MIN_HEIGHT,
    BUTTON_SIZE_PX,
    COLOR_BOX_MIN_W,
    COLOR_BOX_MIN_H,
    LUMINANCE_DARK_TEXT_THRESHOLD,
)


class MainWindow(QMainWindow):
    """PySide6 GUI for the Color Sentence app."""

    def __init__(self) -> None:
        super().__init__()
        self._cfg: ComputeConfig = ComputeConfig()
        self._init_window()
        self._create_fonts()
        self._create_widgets()
        self._assemble_layout()
        self._setup_tts()

    def _init_window(self) -> None:
        """Apply static window properties."""
        self.setWindowTitle("Color Sentence")
        self.setMinimumWidth(WINDOW_MIN_WIDTH)

    def _create_fonts(self) -> None:
        """Prepare base font used across the UI."""
        family: str = self.font().family()
        self._base_font: QFont = QFont(family, FONT_POINT_SIZE)

    def _create_widgets(self) -> None:
        """Create widgets without wiring."""
        self.input_edit: QLineEdit = QLineEdit()
        self.input_edit.setPlaceholderText("Satz eingeben …")
        self.input_edit.setFont(self._base_font)
        self.input_edit.setMinimumHeight(INPUT_MIN_HEIGHT)
        self.input_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.compute_btn: QPushButton = QPushButton("Farbe\nberechnen")
        self.compute_btn.setFixedSize(BUTTON_SIZE_PX, BUTTON_SIZE_PX)
        self.compute_btn.clicked.connect(self._on_compute)

        self.hex_label: QLabel = QLabel("Hex: —")
        self.hex_label.setFont(self._base_font)
        self.name_label: QLabel = QLabel("Name: —")
        self.name_label.setFont(self._base_font)
        self.rgb_label: QLabel = QLabel("RGB: —")
        self.rgb_label.setFont(self._base_font)

        self.color_box: QLabel = QLabel("—")
        self.color_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.color_box.setMinimumSize(COLOR_BOX_MIN_W, COLOR_BOX_MIN_H)
        self.color_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.color_box.setFont(self._base_font)
        self._apply_box_style("#808080", dark_text=True)

        self.mode_label: QLabel = QLabel("Modus:")
        self.mode_label.setFont(self._base_font)

        self.mode_combo: QComboBox = QComboBox()
        self.mode_combo.addItems(["Frequenz", "Anker"])
        self.mode_combo.setCurrentIndex(0)
        self.mode_combo.setFont(self._base_font)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)

    def _assemble_layout(self) -> None:
        """Place widgets into layouts and assign the central widget."""
        input_row: QHBoxLayout = QHBoxLayout()
        input_row.setSpacing(SPACING_PX)
        input_row.addWidget(self.input_edit, 4)
        input_row.addWidget(self.compute_btn, 1)

        labels_col: QVBoxLayout = QVBoxLayout()
        labels_col.setSpacing(SPACING_PX)
        labels_col.addWidget(self.hex_label)
        labels_col.addWidget(self.name_label)
        labels_col.addWidget(self.rgb_label)

        result_row: QHBoxLayout = QHBoxLayout()
        result_row.setSpacing(SPACING_PX)
        result_row.addLayout(labels_col, 3)
        result_row.addWidget(self.color_box, 2)

        mode_row: QHBoxLayout = QHBoxLayout()
        mode_row.setSpacing(SPACING_PX)
        mode_row.addWidget(self.mode_label)
        mode_row.addWidget(self.mode_combo)
        mode_row.addStretch(1)

        root: QVBoxLayout = QVBoxLayout()
        root.setContentsMargins(PADDING_PX, PADDING_PX, PADDING_PX, PADDING_PX)
        root.setSpacing(SPACING_PX)
        root.addLayout(input_row)
        root.addLayout(result_row)
        root.addLayout(mode_row)

        container: QWidget = QWidget()
        container.setLayout(root)
        self.setCentralWidget(container)

    def _setup_tts(self) -> None:
        """Enable non-blocking TTS and warm up the engine."""
        backend: GttsSynthesizer = GttsSynthesizer()
        runner: TtsRunner = TtsRunner(backend=backend)
        self._cfg = replace(
            self._cfg,
            speak_enabled=True,
            tts_backend=backend,
            tts_async=True,
            tts_runner=runner,
        )
        prepare_engine(self._cfg)

    def _apply_box_style(self, hex_code: str, *, dark_text: bool) -> None:
        """Apply background color and readable foreground to the color box."""
        text_color: str = "#000000" if dark_text else "white"
        self.color_box.setStyleSheet(
            "QLabel { "
            f"background:{hex_code}; color:{text_color}; "
            "border-radius:10px; padding:8px; }"
        )
        self.color_box.setText(hex_code)

    def _update_result(self, result: ComputeResult) -> None:
        """Update labels and color box from a ComputeResult."""
        red: int = result.rgb[0]
        green: int = result.rgb[1]
        blue: int = result.rgb[2]
        luminance: float = 0.2126 * float(red) + 0.7152 * float(green) + 0.0722 * float(blue)
        use_dark_text: bool = luminance > LUMINANCE_DARK_TEXT_THRESHOLD
        self._apply_box_style(result.hex, dark_text=use_dark_text)
        self.hex_label.setText(f"Hex: {result.hex}")
        self.name_label.setText(f"Name: {result.name}")
        self.rgb_label.setText(f"RGB: {result.rgb}")

    def _on_mode_changed(self, index: int) -> None:
        """Switch between frequency and anchor mode."""
        mode: ComputeMode = ComputeMode.FREQ if index == 0 else ComputeMode.ANCHOR
        self._cfg = replace(self._cfg, mode=mode)

    def _on_compute(self) -> None:
        """Compute color for the input text and update the UI."""
        text: str = self.input_edit.text().strip()
        if not text:
            return
        result: ComputeResult = compute_color(text, self._cfg)
        self._update_result(result)


def run() -> None:
    """Run the PySide6 application."""
    app: QApplication = QApplication([])
    window: MainWindow = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":  # pragma: no cover
    run()
