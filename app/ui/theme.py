"""Dark space-themed look and feel, applied once globally via
QApplication.setStyleSheet -- every dialog inherits it automatically."""

BG_SPACE = "#0B0E1A"
BG_PANEL = "#12172B"
BG_FIELD = "#0F1428"
BORDER = "#232A45"
TEXT = "#E8ECF7"
TEXT_MUTED = "#8892B0"
ACCENT_CYAN = "#22D3EE"
ACCENT_MAGENTA = "#EC4899"
ACCENT_GREEN = "#34D399"

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {BG_SPACE};
    color: {TEXT};
    font-family: "Segoe UI";
    font-size: 10.5pt;
}}

QDialog {{
    background-color: {BG_PANEL};
}}

#mainForeground {{
    background: transparent;
}}

QLabel {{
    background: transparent;
    color: {TEXT};
}}

QTabWidget::pane {{
    background-color: {BG_PANEL};
    border: 1px solid {BORDER};
    border-radius: 10px;
    top: -1px;
}}

QTabBar::tab {{
    background: transparent;
    color: {TEXT_MUTED};
    padding: 8px 18px;
    margin-right: 4px;
    border-bottom: 2px solid transparent;
    font-weight: 600;
}}

QTabBar::tab:selected {{
    color: {TEXT};
    border-bottom: 2px solid {ACCENT_CYAN};
}}

QTabBar::tab:hover {{
    color: {TEXT};
}}

QPushButton {{
    background-color: {BG_FIELD};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 7px 16px;
    font-weight: 600;
}}

QPushButton:hover {{
    border: 1px solid {ACCENT_CYAN};
    color: {ACCENT_CYAN};
}}

QPushButton:pressed {{
    background-color: {BORDER};
}}

QPushButton:disabled {{
    color: {TEXT_MUTED};
    border: 1px solid {BORDER};
}}

QLineEdit, QTextEdit, QSpinBox, QTimeEdit {{
    background-color: {BG_FIELD};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 5px 8px;
    selection-background-color: {ACCENT_CYAN};
    selection-color: {BG_SPACE};
}}

QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QTimeEdit:focus {{
    border: 1px solid {ACCENT_CYAN};
}}

QListWidget {{
    background-color: {BG_FIELD};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    outline: none;
}}

QListWidget::item {{
    padding: 6px 4px;
    border-radius: 4px;
}}

QListWidget::item:selected {{
    background-color: {BORDER};
    color: {ACCENT_CYAN};
}}

QListWidget::item:hover {{
    background-color: {BG_PANEL};
}}

QProgressBar {{
    background-color: {BG_FIELD};
    border: 1px solid {BORDER};
    border-radius: 8px;
    text-align: center;
    color: {TEXT};
    height: 16px;
}}

QProgressBar::chunk {{
    border-radius: 7px;
    background-color: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT_CYAN}, stop:1 {ACCENT_MAGENTA}
    );
}}

QCheckBox {{
    color: {TEXT};
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {BORDER};
    border-radius: 4px;
    background-color: {BG_FIELD};
}}

QCheckBox::indicator:checked {{
    background-color: {ACCENT_CYAN};
    border: 1px solid {ACCENT_CYAN};
}}

QMessageBox {{
    background-color: {BG_PANEL};
}}

QMenu {{
    background-color: {BG_PANEL};
    color: {TEXT};
    border: 1px solid {BORDER};
}}

QMenu::item:selected {{
    background-color: {BORDER};
    color: {ACCENT_CYAN};
}}

QScrollBar:vertical {{
    background: {BG_SPACE};
    width: 10px;
}}

QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 5px;
    min-height: 24px;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
"""
