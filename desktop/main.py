"""
Claim360 Desktop Client
Built with PyQt6 — communicates with Claim360 FastAPI backend.
"""
import sys
import os
import json
import webbrowser
import tempfile
from functools import partial
from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox, QCheckBox,
    QFileDialog, QMessageBox, QStackedWidget, QFrame, QSplitter,
    QScrollArea, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QDialog, QDialogButtonBox, QSpinBox, QListWidget,
    QListWidgetItem, QSizePolicy, QTabWidget, QToolButton, QStatusBar,
    QInputDialog, QFormLayout, QGroupBox
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSize, QPropertyAnimation,
    QEasingCurve, QRect, pyqtProperty, QUrl
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QPixmap, QIcon, QFontDatabase,
    QLinearGradient, QPainter, QBrush, QPen, QAction
)

from api_client import Claim360API, APIError

# ─── Constants ────────────────────────────────────────────────────────────────
BACKEND_URL = os.getenv("MAILBLAST_API_URL", "http://localhost:8000")

# Color palette — deep navy + electric cyan + warm white
C = {
    "bg":       "#0D1117",
    "surface":  "#161B22",
    "card":     "#1C2333",
    "border":   "#30363D",
    "accent":   "#00D4FF",
    "accent2":  "#7928CA",
    "success":  "#00E676",
    "warning":  "#FFB300",
    "error":    "#FF3D71",
    "text":     "#E6EDF3",
    "subtext":  "#8B949E",
    "hover":    "#21262D",
    "nav_bg":   "#010409",
    "nav_sel":  "#00D4FF22",
}

STYLESHEET = f"""
QMainWindow, QDialog {{
    background-color: {C['bg']};
    color: {C['text']};
    font-family: 'Segoe UI', 'SF Pro Display', Arial, sans-serif;
    font-size: 13px;
}}
QWidget {{
    background-color: transparent;
    color: {C['text']};
    font-family: 'Segoe UI', 'SF Pro Display', Arial, sans-serif;
    font-size: 13px;
}}
QMainWindow > QWidget, QDialog > QWidget {{
    background-color: {C['bg']};
}}
QLabel {{
    color: {C['text']};
    background: transparent;
}}
QLineEdit, QTextEdit, QSpinBox, QComboBox {{
    background-color: {C['surface']};
    color: {C['text']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: {C['accent']};
    selection-color: {C['bg']};
}}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border-color: {C['accent']};
    outline: none;
}}
QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {C['subtext']};
    margin-right: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {C['surface']};
    border: 1px solid {C['border']};
    color: {C['text']};
    selection-background-color: {C['hover']};
}}
QPushButton {{
    background-color: {C['accent']};
    color: {C['bg']};
    border: none;
    border-radius: 6px;
    padding: 9px 20px;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.3px;
}}
QPushButton:hover {{
    background-color: #33DDFF;
}}
QPushButton:pressed {{
    background-color: #00AACC;
}}
QPushButton:disabled {{
    background-color: {C['border']};
    color: {C['subtext']};
}}
QPushButton.secondary {{
    background-color: {C['surface']};
    color: {C['text']};
    border: 1px solid {C['border']};
}}
QPushButton.secondary:hover {{
    background-color: {C['hover']};
    border-color: {C['accent']};
}}
QPushButton.danger {{
    background-color: {C['error']};
    color: white;
}}
QPushButton.danger:hover {{
    background-color: #FF6B8A;
}}
QPushButton.success {{
    background-color: {C['success']};
    color: {C['bg']};
}}
QTableWidget {{
    background-color: {C['surface']};
    border: 1px solid {C['border']};
    border-radius: 8px;
    gridline-color: {C['border']};
    alternate-background-color: {C['card']};
    color: {C['text']};
    font-size: 12px;
}}
QTableWidget::item {{
    padding: 6px 10px;
    border: none;
}}
QTableWidget::item:selected {{
    background-color: {C['nav_sel']};
    color: {C['accent']};
}}
QHeaderView::section {{
    background-color: {C['card']};
    color: {C['subtext']};
    padding: 8px 10px;
    border: none;
    border-bottom: 1px solid {C['border']};
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
QScrollBar:vertical {{
    background: {C['bg']};
    width: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {C['border']};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {C['subtext']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QProgressBar {{
    background-color: {C['surface']};
    border: 1px solid {C['border']};
    border-radius: 4px;
    height: 8px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {C['accent2']}, stop:1 {C['accent']});
    border-radius: 4px;
}}
QTabWidget::pane {{
    border: 1px solid {C['border']};
    border-radius: 8px;
    background: {C['surface']};
}}
QTabBar::tab {{
    background: {C['card']};
    color: {C['subtext']};
    padding: 8px 18px;
    border: 1px solid {C['border']};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
    font-size: 12px;
}}
QTabBar::tab:selected {{
    background: {C['surface']};
    color: {C['accent']};
    border-bottom: 2px solid {C['accent']};
}}
QGroupBox {{
    border: 1px solid {C['border']};
    border-radius: 8px;
    margin-top: 12px;
    padding: 12px;
    font-size: 12px;
    color: {C['subtext']};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {C['accent']};
    font-weight: 600;
}}
QCheckBox {{
    color: {C['text']};
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {C['border']};
    border-radius: 3px;
    background: {C['surface']};
}}
QCheckBox::indicator:checked {{
    background: {C['accent']};
    border-color: {C['accent']};
}}
QListWidget {{
    background-color: {C['surface']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    color: {C['text']};
    font-size: 12px;
}}
QListWidget::item {{
    padding: 6px 10px;
    border-radius: 4px;
}}
QListWidget::item:selected {{
    background-color: {C['nav_sel']};
    color: {C['accent']};
}}
QStatusBar {{
    background-color: {C['nav_bg']};
    color: {C['subtext']};
    border-top: 1px solid {C['border']};
    font-size: 11px;
    padding: 2px 8px;
}}
"""


def btn(text: str, cls: str = "", parent=None) -> QPushButton:
    b = QPushButton(text, parent)
    if cls:
        b.setProperty("class", cls)
    return b


def label(text: str, size: int = 13, bold: bool = False, color: str = None) -> QLabel:
    lbl = QLabel(text)
    font = QFont()
    font.setPointSize(size)
    if bold:
        font.setBold(True)
    lbl.setFont(font)
    if color:
        lbl.setStyleSheet(f"color: {color};")
    return lbl


def hline() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet(f"background-color: {C['border']}; max-height: 1px;")
    return line


def card_widget(title: str = "") -> QGroupBox:
    g = QGroupBox(title)
    return g


# ─── Worker Threads ────────────────────────────────────────────────────────────

class APIWorker(QThread):
    result = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.result.emit(result)
        except APIError as e:
            self.error.emit(e.message)
        except Exception as e:
            self.error.emit(str(e))


class CampaignSendWorker(QThread):
    progress = pyqtSignal(str, str)  # email, status
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, api: Claim360API, campaign_id: int):
        super().__init__()
        self.api = api
        self.campaign_id = campaign_id
        self._running = True

    def run(self):
        try:
            # Start campaign
            self.api.start_campaign(self.campaign_id)

            # Poll for updates
            import time
            while self._running:
                logs = self.api.get_campaign_logs(self.campaign_id)
                campaigns = self.api.list_campaigns()
                campaign = next((c for c in campaigns if c["id"] == self.campaign_id), None)

                for log in logs:
                    self.progress.emit(log["recipient_email"], log["status"])

                if campaign and campaign["status"] in ("completed", "failed"):
                    self.finished.emit(campaign)
                    break

                time.sleep(2)

        except APIError as e:
            self.error.emit(e.message)
        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        self._running = False


# ─── Nav Menu ────────────────────────────────────────────────────────────────

class NavMenu(QWidget):
    page_changed = pyqtSignal(int)

    PAGES = [
        ("⚙", "Configuration"),
        ("📊", "Data & Variables"),
        ("📝", "Templates"),
        ("👁", "Preview"),
        ("✉", "Send Email"),
        ("📈", "Tracking & Logs"),
        ("🛡", "Admin Panel"),
    ]

    def __init__(self):
        super().__init__()
        self.setFixedWidth(220)
        self.setStyleSheet(f"background-color: {C['nav_bg']}; border-right: 1px solid {C['border']};")
        self._current = 0
        self._buttons = []
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo
        logo_widget = QWidget()
        logo_widget.setFixedHeight(70)
        logo_widget.setStyleSheet(f"background: {C['nav_bg']}; border-bottom: 1px solid {C['border']};")
        ll = QHBoxLayout(logo_widget)
        ll.setContentsMargins(16, 0, 16, 0)
        logo = QLabel("✉ Claim360")
        logo.setStyleSheet(f"color: {C['accent']}; font-size: 17px; font-weight: 700; letter-spacing: 1px;")
        ll.addWidget(logo)
        layout.addWidget(logo_widget)

        # Nav items
        for i, (icon, name) in enumerate(self.PAGES):
            nav_btn = QPushButton(f"  {icon}  {name}")
            nav_btn.setFixedHeight(46)
            nav_btn.setCheckable(True)
            nav_btn.setStyleSheet(self._nav_style(False))
            nav_btn.clicked.connect(partial(self._select, i))
            self._buttons.append(nav_btn)
            layout.addWidget(nav_btn)

        layout.addStretch()

        # Version
        ver = QLabel("v1.0.0  ·  Claim360")
        ver.setStyleSheet(f"color: {C['subtext']}; font-size: 10px; padding: 8px 16px;")
        layout.addWidget(ver)

        self._select(0)

    def _nav_style(self, active: bool) -> str:
        if active:
            return f"""
                QPushButton {{
                    background-color: {C['nav_sel']};
                    color: {C['accent']};
                    border: none;
                    border-left: 3px solid {C['accent']};
                    text-align: left;
                    padding-left: 18px;
                    font-size: 13px;
                    font-weight: 600;
                }}
            """
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {C['subtext']};
                border: none;
                border-left: 3px solid transparent;
                text-align: left;
                padding-left: 18px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {C['hover']};
                color: {C['text']};
                border-left: 3px solid {C['border']};
            }}
        """

    def _select(self, index: int):
        for i, b in enumerate(self._buttons):
            b.setStyleSheet(self._nav_style(i == index))
        self._current = index
        self.page_changed.emit(index)

    def set_admin_visible(self, visible: bool):
        if len(self._buttons) > 6:
            self._buttons[6].setVisible(visible)


# ─── Individual Pages ─────────────────────────────────────────────────────────

class ConfigPage(QWidget):
    def __init__(self, api: Claim360API):
        super().__init__()
        self.api = api
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)

        layout.addWidget(label("Configuration", 20, True))
        layout.addWidget(label("Manage your Gmail OAuth connection and server settings.", color=C["subtext"]))
        layout.addWidget(hline())

        # Server config
        server_box = QGroupBox("Backend Server")
        sb_layout = QFormLayout(server_box)
        self.server_url_input = QLineEdit(BACKEND_URL)
        sb_layout.addRow("API URL:", self.server_url_input)
        check_btn = btn("Test Connection")
        check_btn.clicked.connect(self._test_connection)
        sb_layout.addRow("", check_btn)
        self.conn_status = QLabel("Not tested")
        self.conn_status.setStyleSheet(f"color: {C['subtext']};")
        sb_layout.addRow("Status:", self.conn_status)
        layout.addWidget(server_box)

        # Gmail OAuth
        gmail_box = QGroupBox("Gmail OAuth 2.0")
        gb_layout = QVBoxLayout(gmail_box)

        self.gmail_status_label = QLabel("Checking...")
        self.gmail_status_label.setStyleSheet(f"color: {C['subtext']};")
        gb_layout.addWidget(self.gmail_status_label)

        btn_row = QHBoxLayout()
        self.connect_btn = btn("🔗  Connect Gmail")
        self.connect_btn.clicked.connect(self._connect_gmail)
        self.disconnect_btn = btn("Disconnect", "secondary")
        self.disconnect_btn.clicked.connect(self._disconnect_gmail)
        self.disconnect_btn.setVisible(False)
        btn_row.addWidget(self.connect_btn)
        btn_row.addWidget(self.disconnect_btn)
        btn_row.addStretch()
        gb_layout.addLayout(btn_row)

        note = QLabel("OAuth will open a browser window. After authorizing, return to this app.")
        note.setStyleSheet(f"color: {C['subtext']}; font-size: 11px;")
        note.setWordWrap(True)
        gb_layout.addWidget(note)
        layout.addWidget(gmail_box)

        layout.addStretch()
        self._refresh_status()

    def _test_connection(self):
        url = self.server_url_input.text().strip()
        self.api.base_url = url
        healthy = self.api.check_health()
        if healthy:
            self.conn_status.setText("✅ Connected")
            self.conn_status.setStyleSheet(f"color: {C['success']};")
        else:
            self.conn_status.setText("❌ Cannot reach server")
            self.conn_status.setStyleSheet(f"color: {C['error']};")

    def _connect_gmail(self):
        try:
            url = self.api.get_oauth_url()
            webbrowser.open(url)
            QMessageBox.information(self, "Gmail OAuth",
                "Your browser has opened. Please authorize Claim360 to access Gmail.\n\n"
                "After completing authorization, click OK to refresh your connection status.")
            self._refresh_status()
        except APIError as e:
            QMessageBox.critical(self, "Error", e.message)

    def _disconnect_gmail(self):
        reply = QMessageBox.question(self, "Disconnect Gmail",
            "Disconnect your Gmail account?\nYou won't be able to send emails until reconnecting.")
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.api.disconnect_oauth()
                self._refresh_status()
            except APIError as e:
                QMessageBox.critical(self, "Error", e.message)

    def _refresh_status(self):
        if not self.api.token:
            return
        try:
            me = self.api.get_me()
            if me.get("gmail_connected"):
                gmail = me.get("gmail_email", "Connected")
                self.gmail_status_label.setText(f"✅  Connected as: {gmail}")
                self.gmail_status_label.setStyleSheet(f"color: {C['success']}; font-weight: 600;")
                self.connect_btn.setVisible(False)
                self.disconnect_btn.setVisible(True)
            else:
                self.gmail_status_label.setText("⚠  Not connected — click below to authorize Gmail")
                self.gmail_status_label.setStyleSheet(f"color: {C['warning']};")
                self.connect_btn.setVisible(True)
                self.disconnect_btn.setVisible(False)
        except Exception:
            pass


class DataPage(QWidget):
    contacts_updated = pyqtSignal(list, list)  # contacts, variable_names

    def __init__(self, api: Claim360API):
        super().__init__()
        self.api = api
        self.contacts: List[Dict] = []
        self.variable_names: List[str] = []
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)
        layout.addWidget(label("Data & Variables Setup", 20, True))
        layout.addWidget(hline())

        tabs = QTabWidget()
        tabs.addTab(self._build_variables_tab(), "Custom Variables")
        tabs.addTab(self._build_upload_tab(), "Excel Upload")
        tabs.addTab(self._build_dummy_tab(), "Dummy Data Generator")
        layout.addWidget(tabs)

    def _build_variables_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        layout.addWidget(label("Define your merge variables (used as {{variable}} in templates):", color=C["subtext"]))

        row = QHBoxLayout()
        self.var_input = QLineEdit()
        self.var_input.setPlaceholderText("e.g. name, company, position, custom1...")
        self.var_input.returnPressed.connect(self._add_variable)
        add_btn = btn("Add Variable")
        add_btn.clicked.connect(self._add_variable)
        row.addWidget(self.var_input)
        row.addWidget(add_btn)
        layout.addLayout(row)

        self.var_list = QListWidget()
        self.var_list.setMaximumHeight(200)
        layout.addWidget(self.var_list)

        rem_btn = btn("Remove Selected", "secondary")
        rem_btn.clicked.connect(self._remove_variable)
        layout.addWidget(rem_btn)

        layout.addWidget(label("Sample download uses these variables as columns.", color=C["subtext"], size=11))
        dl_btn = btn("⬇  Download Sample Excel")
        dl_btn.clicked.connect(self._download_sample)
        layout.addWidget(dl_btn)

        layout.addStretch()
        return w

    def _add_variable(self):
        text = self.var_input.text().strip().lower().replace(" ", "_")
        if not text:
            return
        if text in self.variable_names:
            QMessageBox.warning(self, "Duplicate", f"Variable '{text}' already exists.")
            return
        self.variable_names.append(text)
        self.var_list.addItem(f"  {{{{{text}}}}}")
        self.var_input.clear()

    def _remove_variable(self):
        row = self.var_list.currentRow()
        if row >= 0:
            self.var_list.takeItem(row)
            self.variable_names.pop(row)

    def _download_sample(self):
        if not self.variable_names:
            QMessageBox.warning(self, "No Variables", "Add at least one variable first.")
            return
        try:
            content = self.api.get_sample_excel(",".join(self.variable_names))
            path, _ = QFileDialog.getSaveFileName(self, "Save Sample Excel", "sample_contacts.xlsx",
                "Excel Files (*.xlsx)")
            if path:
                with open(path, "wb") as f:
                    f.write(content)
                QMessageBox.information(self, "Downloaded", f"Saved to:\n{path}")
        except APIError as e:
            QMessageBox.critical(self, "Error", e.message)

    def _build_upload_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        upload_row = QHBoxLayout()
        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet(f"color: {C['subtext']};")
        choose_btn = btn("Choose Excel / CSV", "secondary")
        choose_btn.clicked.connect(self._choose_file)
        upload_row.addWidget(self.file_label)
        upload_row.addWidget(choose_btn)
        layout.addLayout(upload_row)

        parse_btn = btn("📂  Parse & Preview")
        parse_btn.clicked.connect(self._parse_file)
        layout.addWidget(parse_btn)

        self.errors_label = QLabel("")
        self.errors_label.setStyleSheet(f"color: {C['warning']}; font-size: 11px;")
        self.errors_label.setWordWrap(True)
        layout.addWidget(self.errors_label)

        self.preview_table = QTableWidget()
        self.preview_table.setAlternatingRowColors(True)
        layout.addWidget(self.preview_table)

        self.use_data_btn = btn("✅  Use This Data for Campaign")
        self.use_data_btn.setEnabled(False)
        self.use_data_btn.clicked.connect(self._use_data)
        layout.addWidget(self.use_data_btn)

        self._selected_file = None
        self._parsed_data = None
        return w

    def _choose_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select File", "",
            "Spreadsheet Files (*.xlsx *.xls *.csv)")
        if path:
            self._selected_file = path
            self.file_label.setText(os.path.basename(path))
            self.file_label.setStyleSheet(f"color: {C['text']};")

    def _parse_file(self):
        if not self._selected_file:
            QMessageBox.warning(self, "No File", "Please select a file first.")
            return
        try:
            result = self.api.parse_excel(self._selected_file)
            self._parsed_data = result
            rows = result["rows"]
            headers = result["headers"]

            self.preview_table.clear()
            self.preview_table.setColumnCount(len(headers))
            self.preview_table.setHorizontalHeaderLabels(headers)
            self.preview_table.setRowCount(min(len(rows), 20))

            for r, row in enumerate(rows[:20]):
                for c, h in enumerate(headers):
                    self.preview_table.setItem(r, c, QTableWidgetItem(str(row.get(h, ""))))

            self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

            errors = result.get("errors", [])
            if errors:
                self.errors_label.setText("⚠ " + "\n".join(errors[:5]))
            else:
                self.errors_label.setText(f"✅ {result['total_rows']} rows parsed successfully")
                self.errors_label.setStyleSheet(f"color: {C['success']}; font-size: 11px;")

            self.use_data_btn.setEnabled(True)
        except APIError as e:
            QMessageBox.critical(self, "Parse Error", e.message)

    def _use_data(self):
        if not self._parsed_data:
            return
        rows = self._parsed_data["rows"]
        headers = self._parsed_data["headers"]
        email_col = next((h for h in headers if "email" in h.lower()), None)
        if not email_col:
            QMessageBox.warning(self, "No Email Column", "Could not find an email column.")
            return

        contacts = []
        for row in rows:
            email = row.get(email_col, "").strip()
            if not email:
                continue
            variables = {k: v for k, v in row.items() if k != email_col}
            contacts.append({"email": email, "variables": variables, "cc_emails": []})

        self.contacts = contacts
        # Infer variable names from non-email headers
        var_names = [h for h in headers if h != email_col]
        for v in var_names:
            if v not in self.variable_names:
                self.variable_names.append(v)
                self.var_list.addItem(f"  {{{{{v}}}}}")

        self.contacts_updated.emit(contacts, self.variable_names)
        QMessageBox.information(self, "Data Loaded",
            f"✅ {len(contacts)} contacts loaded and ready for campaign setup.")

    def _build_dummy_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        layout.addWidget(label("Generate fake test data based on your variables:", color=C["subtext"]))

        count_row = QHBoxLayout()
        count_row.addWidget(QLabel("Records:"))
        self.dummy_count = QSpinBox()
        self.dummy_count.setRange(1, 100)
        self.dummy_count.setValue(10)
        count_row.addWidget(self.dummy_count)
        count_row.addStretch()
        layout.addLayout(count_row)

        gen_btn = btn("🎲  Generate Dummy Data")
        gen_btn.clicked.connect(self._generate_dummy)
        layout.addWidget(gen_btn)

        self.dummy_table = QTableWidget()
        self.dummy_table.setAlternatingRowColors(True)
        layout.addWidget(self.dummy_table)

        use_btn = btn("✅  Use This Dummy Data")
        use_btn.clicked.connect(self._use_dummy)
        layout.addWidget(use_btn)

        self._dummy_data = None
        return w

    def _generate_dummy(self):
        if not self.variable_names:
            QMessageBox.warning(self, "No Variables", "Define variables first in the Variables tab.")
            return
        try:
            result = self.api.generate_dummy(self.variable_names, self.dummy_count.value())
            rows = result["rows"]
            self._dummy_data = rows
            headers = list(rows[0].keys()) if rows else []

            self.dummy_table.clear()
            self.dummy_table.setColumnCount(len(headers))
            self.dummy_table.setHorizontalHeaderLabels(headers)
            self.dummy_table.setRowCount(len(rows))

            for r, row in enumerate(rows):
                for c, h in enumerate(headers):
                    self.dummy_table.setItem(r, c, QTableWidgetItem(str(row.get(h, ""))))

            self.dummy_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        except APIError as e:
            QMessageBox.critical(self, "Error", e.message)

    def _use_dummy(self):
        if not self._dummy_data:
            return
        contacts = []
        for row in self._dummy_data:
            email = row.pop("email", "")
            if email:
                contacts.append({"email": email, "variables": row, "cc_emails": []})
        self.contacts = contacts
        self.contacts_updated.emit(contacts, self.variable_names)
        QMessageBox.information(self, "Dummy Data Loaded",
            f"✅ {len(contacts)} test contacts loaded.")


class TemplatePage(QWidget):
    def __init__(self, api: Claim360API):
        super().__init__()
        self.api = api
        self.templates = []
        self.attachments = []
        self._build()
        self._refresh()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)
        layout.addWidget(label("Templates", 20, True))
        layout.addWidget(hline())

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: list
        left = QWidget()
        left.setStyleSheet(f"background: {C['surface']}; border-radius: 8px;")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.addWidget(label("My Templates", bold=True))

        self.template_list = QListWidget()
        self.template_list.currentRowChanged.connect(self._on_template_select)
        left_layout.addWidget(self.template_list)

        list_btns = QHBoxLayout()
        new_btn = btn("New")
        new_btn.clicked.connect(self._new_template)
        del_btn = btn("Delete", "danger")
        del_btn.clicked.connect(self._delete_template)
        list_btns.addWidget(new_btn)
        list_btns.addWidget(del_btn)
        left_layout.addLayout(list_btns)
        splitter.addWidget(left)

        # Right: editor
        right = QWidget()
        right.setStyleSheet(f"background: {C['surface']}; border-radius: 8px;")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(10)
        right_layout.addWidget(label("Template Editor", bold=True))

        form = QFormLayout()
        self.tpl_name = QLineEdit()
        self.tpl_name.setPlaceholderText("Template name")
        self.tpl_subject = QLineEdit()
        self.tpl_subject.setPlaceholderText("Email subject — use {{variable}} for merge")
        self.tpl_shared = QCheckBox("Shared (visible to all users)")
        form.addRow("Name:", self.tpl_name)
        form.addRow("Subject:", self.tpl_subject)
        form.addRow("", self.tpl_shared)
        right_layout.addLayout(form)

        var_hint = QLabel("Insert variable: {{name}}  {{company}}  {{position}}  (type {{ to start)")
        var_hint.setStyleSheet(f"color: {C['subtext']}; font-size: 11px;")
        right_layout.addWidget(var_hint)

        self.tpl_body = QTextEdit()
        self.tpl_body.setPlaceholderText("Write your email body here.\nUse {{variable}} for personalization.\nHTML is supported.")
        self.tpl_body.setMinimumHeight(200)
        right_layout.addWidget(self.tpl_body)

        # Attachments
        att_box = QGroupBox("Attachments")
        att_layout = QVBoxLayout(att_box)
        self.att_list = QListWidget()
        self.att_list.setMaximumHeight(100)
        att_layout.addWidget(self.att_list)
        att_btns = QHBoxLayout()
        upload_att_btn = btn("Upload File", "secondary")
        upload_att_btn.clicked.connect(self._upload_attachment)
        remove_att_btn = btn("Remove", "secondary")
        remove_att_btn.clicked.connect(self._remove_attachment)
        att_btns.addWidget(upload_att_btn)
        att_btns.addWidget(remove_att_btn)
        att_layout.addLayout(att_btns)
        right_layout.addWidget(att_box)

        save_btn = btn("💾  Save Template")
        save_btn.clicked.connect(self._save_template)
        right_layout.addWidget(save_btn)

        splitter.addWidget(right)
        splitter.setSizes([240, 600])
        layout.addWidget(splitter)

        self._editing_id = None
        self._selected_att_ids = []

    def _refresh(self):
        try:
            self.templates = self.api.list_templates()
            self.attachments = self.api.list_attachments()
            self.template_list.clear()
            for t in self.templates:
                icon = "🌐" if t["is_shared"] else "📝"
                self.template_list.addItem(f"{icon} {t['name']}")
        except Exception:
            pass

    def _on_template_select(self, row: int):
        if row < 0 or row >= len(self.templates):
            return
        t = self.templates[row]
        self._editing_id = t["id"]
        self.tpl_name.setText(t["name"])
        self.tpl_subject.setText(t["subject"])
        self.tpl_body.setHtml(t["body_html"])
        self.tpl_shared.setChecked(t.get("is_shared", False))
        self._selected_att_ids = [a["id"] for a in t.get("attachments", [])]
        self._refresh_att_list()

    def _refresh_att_list(self):
        self.att_list.clear()
        for att_id in self._selected_att_ids:
            att = next((a for a in self.attachments if a["id"] == att_id), None)
            if att:
                size_kb = att["file_size"] // 1024
                self.att_list.addItem(f"📎 {att['original_filename']} ({size_kb}KB)")

    def _upload_attachment(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Attachment", "",
            "All Files (*.*)")
        if path:
            try:
                att = self.api.upload_attachment(path)
                self.attachments.append(att)
                self._selected_att_ids.append(att["id"])
                self._refresh_att_list()
                QMessageBox.information(self, "Uploaded", f"✅ {att['original_filename']} uploaded")
            except APIError as e:
                QMessageBox.critical(self, "Error", e.message)

    def _remove_attachment(self):
        row = self.att_list.currentRow()
        if row >= 0 and row < len(self._selected_att_ids):
            self._selected_att_ids.pop(row)
            self._refresh_att_list()

    def _new_template(self):
        self._editing_id = None
        self.tpl_name.clear()
        self.tpl_subject.clear()
        self.tpl_body.clear()
        self.tpl_shared.setChecked(False)
        self._selected_att_ids = []
        self._refresh_att_list()
        self.template_list.clearSelection()

    def _save_template(self):
        name = self.tpl_name.text().strip()
        subject = self.tpl_subject.text().strip()
        body = self.tpl_body.toHtml()
        if not name or not subject:
            QMessageBox.warning(self, "Incomplete", "Name and Subject are required.")
            return
        data = {
            "name": name,
            "subject": subject,
            "body_html": body,
            "body_text": self.tpl_body.toPlainText(),
            "is_shared": self.tpl_shared.isChecked(),
            "attachment_ids": self._selected_att_ids,
        }
        try:
            if self._editing_id:
                self.api.update_template(self._editing_id, data)
                QMessageBox.information(self, "Saved", "✅ Template updated!")
            else:
                self.api.create_template(data)
                QMessageBox.information(self, "Created", "✅ Template created!")
            self._refresh()
        except APIError as e:
            QMessageBox.critical(self, "Error", e.message)

    def _delete_template(self):
        row = self.template_list.currentRow()
        if row < 0:
            return
        t = self.templates[row]
        reply = QMessageBox.question(self, "Delete", f"Delete template '{t['name']}'?")
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.api.delete_template(t["id"])
                self._refresh()
            except APIError as e:
                QMessageBox.critical(self, "Error", e.message)

    def get_templates(self):
        return self.templates


class PreviewPage(QWidget):
    def __init__(self, api: Claim360API):
        super().__init__()
        self.api = api
        self.templates = []
        self.contacts = []
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)
        layout.addWidget(label("Email Preview", 20, True))
        layout.addWidget(label("Preview how your email will look for a specific recipient.", color=C["subtext"]))
        layout.addWidget(hline())

        select_row = QHBoxLayout()
        select_row.addWidget(QLabel("Template:"))
        self.template_combo = QComboBox()
        select_row.addWidget(self.template_combo)
        select_row.addWidget(QLabel("Recipient:"))
        self.recipient_combo = QComboBox()
        select_row.addWidget(self.recipient_combo)
        preview_btn = btn("Render Preview")
        preview_btn.clicked.connect(self._render)
        select_row.addWidget(preview_btn)
        select_row.addStretch()
        layout.addLayout(select_row)

        self.subject_label = QLabel("")
        self.subject_label.setStyleSheet(f"background: {C['card']}; color: {C['text']}; "
            f"padding: 10px 16px; border-radius: 6px; font-weight: 600; font-size: 14px;")
        layout.addWidget(self.subject_label)

        atts_row = QHBoxLayout()
        atts_row.addWidget(label("Attachments:", color=C["subtext"]))
        self.atts_label = QLabel("None")
        self.atts_label.setStyleSheet(f"color: {C['subtext']};")
        atts_row.addWidget(self.atts_label)
        atts_row.addStretch()
        layout.addLayout(atts_row)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMinimumHeight(350)
        layout.addWidget(self.preview_text)

    def update_data(self, templates, contacts):
        self.templates = templates
        self.contacts = contacts
        self.template_combo.clear()
        self.recipient_combo.clear()
        for t in templates:
            self.template_combo.addItem(t["name"])
        for c in contacts:
            self.recipient_combo.addItem(c["email"])

    def _render(self):
        import re

        t_idx = self.template_combo.currentIndex()
        c_idx = self.recipient_combo.currentIndex()
        if t_idx < 0 or c_idx < 0:
            return

        template = self.templates[t_idx]
        contact = self.contacts[c_idx] if c_idx < len(self.contacts) else {}
        variables = contact.get("variables", {})

        def sub(text):
            return re.sub(r'\{\{(\w+)\}\}', lambda m: variables.get(m.group(1), m.group(0)), text)

        subject = sub(template.get("subject", ""))
        body = sub(template.get("body_html", ""))

        self.subject_label.setText(f"Subject: {subject}")
        self.preview_text.setHtml(body)

        atts = template.get("attachments", [])
        if atts:
            self.atts_label.setText(", ".join(a["original_filename"] for a in atts))
        else:
            self.atts_label.setText("None")


class SendPage(QWidget):
    def __init__(self, api: Claim360API):
        super().__init__()
        self.api = api
        self.contacts = []
        self.variable_names = []
        self.templates = []
        self._worker = None
        self._campaign_id = None
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)
        layout.addWidget(label("Send Email Campaign", 20, True))
        layout.addWidget(hline())

        form_box = QGroupBox("Campaign Setup")
        form = QFormLayout(form_box)
        self.campaign_name = QLineEdit()
        self.campaign_name.setPlaceholderText("My Q1 Outreach")
        self.template_combo = QComboBox()
        self.recipients_label = QLabel("No contacts loaded")
        self.recipients_label.setStyleSheet(f"color: {C['subtext']};")
        form.addRow("Campaign Name:", self.campaign_name)
        form.addRow("Template:", self.template_combo)
        form.addRow("Recipients:", self.recipients_label)
        layout.addWidget(form_box)

        send_btn = btn("🚀  Start Sending Campaign")
        send_btn.setMinimumHeight(44)
        send_btn.clicked.connect(self._start_send)
        layout.addWidget(send_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_log = QTableWidget(0, 3)
        self.status_log.setHorizontalHeaderLabels(["Recipient", "Status", "Time"])
        self.status_log.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.status_log.setAlternatingRowColors(True)
        layout.addWidget(self.status_log)

        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet(f"font-size: 13px; font-weight: 600;")
        layout.addWidget(self.summary_label)

    def update_data(self, contacts, variable_names, templates):
        self.contacts = contacts
        self.variable_names = variable_names
        self.templates = templates
        self.recipients_label.setText(f"{len(contacts)} contacts loaded")
        self.template_combo.clear()
        for t in templates:
            self.template_combo.addItem(t["name"])

    def _start_send(self):
        if not self.contacts:
            QMessageBox.warning(self, "No Contacts", "Load contacts in Data & Variables first.")
            return
        name = self.campaign_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Name Required", "Enter a campaign name.")
            return
        t_idx = self.template_combo.currentIndex()
        template_id = self.templates[t_idx]["id"] if t_idx >= 0 and self.templates else None

        reply = QMessageBox.question(self, "Confirm Send",
            f"Send campaign '{name}' to {len(self.contacts)} recipients?\n\n"
            f"Emails will be sent with a 3-second delay between each.")
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Create campaign
        try:
            campaign = self.api.create_campaign({
                "name": name,
                "template_id": template_id,
                "contacts": self.contacts,
                "variable_names": self.variable_names,
                "extra_attachment_ids": [],
            })
            self._campaign_id = campaign["id"]
        except APIError as e:
            QMessageBox.critical(self, "Error", f"Failed to create campaign:\n{e.message}")
            return

        # Start worker
        self.status_log.setRowCount(0)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(self.contacts))
        self.progress_bar.setValue(0)
        self.summary_label.setText("")

        self._worker = CampaignSendWorker(self.api, self._campaign_id)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_progress(self, email: str, status: str):
        row = self.status_log.rowCount()
        self.status_log.insertRow(row)
        self.status_log.setItem(row, 0, QTableWidgetItem(email))

        status_item = QTableWidgetItem(status.upper())
        colors = {"sent": C["success"], "failed": C["error"], "sending": C["accent"], "pending": C["subtext"]}
        status_item.setForeground(QColor(colors.get(status, C["text"])))
        self.status_log.setItem(row, 1, status_item)

        from datetime import datetime
        self.status_log.setItem(row, 2, QTableWidgetItem(datetime.now().strftime("%H:%M:%S")))
        self.status_log.scrollToBottom()

        sent = sum(1 for r in range(self.status_log.rowCount())
            if self.status_log.item(r, 1) and self.status_log.item(r, 1).text() == "SENT")
        self.progress_bar.setValue(sent)

    def _on_finished(self, campaign: dict):
        self.progress_bar.setVisible(False)
        sent = campaign.get("sent_count", 0)
        failed = campaign.get("failed_count", 0)
        self.summary_label.setText(
            f"✅ Campaign complete — Sent: {sent}   Failed: {failed}"
        )
        self.summary_label.setStyleSheet(f"color: {C['success']}; font-size: 13px; font-weight: 600;")

    def _on_error(self, msg: str):
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Send Error", msg)


class TrackingPage(QWidget):
    def __init__(self, api: Claim360API):
        super().__init__()
        self.api = api
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)
        layout.addWidget(label("Tracking & Logs", 20, True))
        layout.addWidget(hline())

        top_row = QHBoxLayout()
        self.campaign_combo = QComboBox()
        self.campaign_combo.currentIndexChanged.connect(self._load_logs)
        refresh_btn = btn("🔄  Refresh", "secondary")
        refresh_btn.clicked.connect(self._refresh_campaigns)
        top_row.addWidget(QLabel("Campaign:"))
        top_row.addWidget(self.campaign_combo, 1)
        top_row.addWidget(refresh_btn)
        layout.addLayout(top_row)

        # Stats row
        self.stats_row = QHBoxLayout()
        self._stat_labels = {}
        for stat in ["Total", "Sent", "Opened", "Failed"]:
            card = QWidget()
            card.setStyleSheet(f"background: {C['card']}; border-radius: 8px; border: 1px solid {C['border']};")
            cv = QVBoxLayout(card)
            cv.setContentsMargins(16, 12, 16, 12)
            num = QLabel("—")
            num.setStyleSheet(f"color: {C['accent']}; font-size: 22px; font-weight: 700;")
            lbl = QLabel(stat)
            lbl.setStyleSheet(f"color: {C['subtext']}; font-size: 11px;")
            cv.addWidget(num)
            cv.addWidget(lbl)
            self._stat_labels[stat.lower()] = num
            self.stats_row.addWidget(card)
        layout.addLayout(self.stats_row)

        self.logs_table = QTableWidget(0, 6)
        self.logs_table.setHorizontalHeaderLabels(["Recipient", "CC", "Subject", "Status", "Sent At", "Opened At"])
        self.logs_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.logs_table.setAlternatingRowColors(True)
        layout.addWidget(self.logs_table)

        self.campaigns = []
        self._refresh_campaigns()

    def _refresh_campaigns(self):
        try:
            self.campaigns = self.api.list_campaigns()
            self.campaign_combo.clear()
            for c in self.campaigns:
                self.campaign_combo.addItem(f"{c['name']} ({c['status']})", c["id"])
            if self.campaigns:
                self._load_logs(0)
        except Exception:
            pass

    def _load_logs(self, idx: int):
        if idx < 0 or idx >= len(self.campaigns):
            return
        c = self.campaigns[idx]
        self._stat_labels["total"].setText(str(c["total_emails"]))
        self._stat_labels["sent"].setText(str(c["sent_count"]))
        self._stat_labels["opened"].setText(str(c["opened_count"]))
        self._stat_labels["failed"].setText(str(c["failed_count"]))

        try:
            logs = self.api.get_campaign_logs(c["id"])
            self.logs_table.setRowCount(len(logs))
            STATUS_COLORS = {
                "sent": C["success"], "opened": C["accent"],
                "failed": C["error"], "pending": C["subtext"], "sending": C["warning"]
            }
            for r, log in enumerate(logs):
                self.logs_table.setItem(r, 0, QTableWidgetItem(log["recipient_email"]))
                cc = ", ".join(log.get("cc_emails", []))
                self.logs_table.setItem(r, 1, QTableWidgetItem(cc))
                self.logs_table.setItem(r, 2, QTableWidgetItem(log.get("subject", "") or ""))
                status = log.get("status", "")
                status_item = QTableWidgetItem(status.upper())
                status_item.setForeground(QColor(STATUS_COLORS.get(status, C["text"])))
                self.logs_table.setItem(r, 3, status_item)
                self.logs_table.setItem(r, 4, QTableWidgetItem(log.get("sent_at") or ""))
                self.logs_table.setItem(r, 5, QTableWidgetItem(log.get("opened_at") or ""))
        except Exception:
            pass


class AdminPage(QWidget):
    def __init__(self, api: Claim360API):
        super().__init__()
        self.api = api
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)
        layout.addWidget(label("Admin Panel", 20, True))
        layout.addWidget(label("Restricted — Admin Only", color=C["error"]))
        layout.addWidget(hline())

        tabs = QTabWidget()
        tabs.addTab(self._build_stats_tab(), "📊 Overview")
        tabs.addTab(self._build_users_tab(), "👥 Users")
        tabs.addTab(self._build_campaigns_tab(), "✉ All Campaigns")
        layout.addWidget(tabs)

    def _build_stats_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)

        refresh_btn = btn("🔄  Refresh Stats", "secondary")
        refresh_btn.clicked.connect(self._load_stats)
        layout.addWidget(refresh_btn)

        grid = QGridLayout()
        self._stats_labels = {}
        metrics = [
            ("total_users", "Total Users", C["accent"]),
            ("total_campaigns", "Campaigns", C["accent2"]),
            ("total_sent", "Emails Sent", C["success"]),
            ("total_opened", "Opened", C["warning"]),
            ("total_failed", "Failed", C["error"]),
        ]
        for i, (key, label_text, color) in enumerate(metrics):
            card = QWidget()
            card.setStyleSheet(f"background: {C['card']}; border-radius: 10px; border: 1px solid {C['border']};")
            cv = QVBoxLayout(card)
            cv.setContentsMargins(20, 16, 20, 16)
            num = QLabel("—")
            num.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: 700;")
            lbl = QLabel(label_text)
            lbl.setStyleSheet(f"color: {C['subtext']}; font-size: 12px;")
            cv.addWidget(num)
            cv.addWidget(lbl)
            self._stats_labels[key] = num
            grid.addWidget(card, i // 3, i % 3)
        layout.addLayout(grid)
        layout.addStretch()
        self._load_stats()
        return w

    def _load_stats(self):
        try:
            stats = self.api.admin_stats()
            for key, lbl in self._stats_labels.items():
                lbl.setText(str(stats.get(key, "—")))
        except Exception:
            pass

    def _build_users_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        refresh_btn = btn("🔄  Refresh", "secondary")
        refresh_btn.clicked.connect(self._load_users)
        layout.addWidget(refresh_btn)

        self.users_table = QTableWidget(0, 7)
        self.users_table.setHorizontalHeaderLabels(
            ["ID", "Email", "Name", "Admin", "Active", "Campaigns", "Emails Sent"]
        )
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.users_table.setAlternatingRowColors(True)
        layout.addWidget(self.users_table)

        btns_row = QHBoxLayout()
        toggle_admin_btn = btn("Toggle Admin", "secondary")
        toggle_admin_btn.clicked.connect(self._toggle_admin)
        toggle_active_btn = btn("Toggle Active", "secondary")
        toggle_active_btn.clicked.connect(self._toggle_active)
        btns_row.addWidget(toggle_admin_btn)
        btns_row.addWidget(toggle_active_btn)
        btns_row.addStretch()
        layout.addLayout(btns_row)

        self._users_data = []
        self._load_users()
        return w

    def _load_users(self):
        try:
            self._users_data = self.api.admin_list_users()
            self.users_table.setRowCount(len(self._users_data))
            for r, u in enumerate(self._users_data):
                self.users_table.setItem(r, 0, QTableWidgetItem(str(u["id"])))
                self.users_table.setItem(r, 1, QTableWidgetItem(u["email"]))
                self.users_table.setItem(r, 2, QTableWidgetItem(u["full_name"]))
                self.users_table.setItem(r, 3, QTableWidgetItem("✓" if u["is_admin"] else ""))
                self.users_table.setItem(r, 4, QTableWidgetItem("✓" if u["is_active"] else "✗"))
                self.users_table.setItem(r, 5, QTableWidgetItem(str(u["campaigns"])))
                self.users_table.setItem(r, 6, QTableWidgetItem(str(u["emails_sent"])))
        except Exception:
            pass

    def _toggle_admin(self):
        row = self.users_table.currentRow()
        if row < 0 or row >= len(self._users_data):
            return
        u = self._users_data[row]
        try:
            self.api.admin_toggle_admin(u["id"])
            self._load_users()
        except APIError as e:
            QMessageBox.critical(self, "Error", e.message)

    def _toggle_active(self):
        row = self.users_table.currentRow()
        if row < 0 or row >= len(self._users_data):
            return
        u = self._users_data[row]
        try:
            self.api.admin_toggle_active(u["id"])
            self._load_users()
        except APIError as e:
            QMessageBox.critical(self, "Error", e.message)

    def _build_campaigns_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)

        refresh_btn = btn("🔄  Refresh", "secondary")
        refresh_btn.clicked.connect(self._load_all_campaigns)
        layout.addWidget(refresh_btn)

        self.all_campaigns_table = QTableWidget(0, 7)
        self.all_campaigns_table.setHorizontalHeaderLabels(
            ["ID", "Name", "User", "Status", "Total", "Sent", "Failed"]
        )
        self.all_campaigns_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.all_campaigns_table.setAlternatingRowColors(True)
        layout.addWidget(self.all_campaigns_table)

        self._load_all_campaigns()
        return w

    def _load_all_campaigns(self):
        try:
            campaigns = self.api.admin_all_campaigns()
            self.all_campaigns_table.setRowCount(len(campaigns))
            for r, c in enumerate(campaigns):
                self.all_campaigns_table.setItem(r, 0, QTableWidgetItem(str(c["id"])))
                self.all_campaigns_table.setItem(r, 1, QTableWidgetItem(c["name"]))
                self.all_campaigns_table.setItem(r, 2, QTableWidgetItem(c.get("user_email", "")))
                self.all_campaigns_table.setItem(r, 3, QTableWidgetItem(c["status"].upper()))
                self.all_campaigns_table.setItem(r, 4, QTableWidgetItem(str(c["total_emails"])))
                self.all_campaigns_table.setItem(r, 5, QTableWidgetItem(str(c["sent_count"])))
                self.all_campaigns_table.setItem(r, 6, QTableWidgetItem(str(c["failed_count"])))
        except Exception:
            pass


# ─── Login Dialog ──────────────────────────────────────────────────────────────

class LoginDialog(QDialog):
    def __init__(self, api: Claim360API):
        super().__init__()
        self.api = api
        self.setWindowTitle("Claim360 — Sign In")
        self.setFixedSize(420, 520)
        self.setStyleSheet(STYLESHEET + f"""
            QDialog {{
                background-color: {C['bg']};
            }}
        """)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)

        logo = QLabel("✉ Claim360")
        logo.setStyleSheet(f"color: {C['accent']}; font-size: 26px; font-weight: 700; letter-spacing: 2px;")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)

        tagline = QLabel("Bulk Email Intelligence")
        tagline.setStyleSheet(f"color: {C['subtext']}; font-size: 12px;")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(tagline)

        layout.addSpacing(16)

        self.tabs = QTabWidget()

        # Login tab
        login_w = QWidget()
        ll = QVBoxLayout(login_w)
        ll.setContentsMargins(12, 16, 12, 12)
        ll.setSpacing(12)
        self.login_email = QLineEdit()
        self.login_email.setPlaceholderText("Email address")
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("Password")
        self.login_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_password.returnPressed.connect(self._do_login)
        login_btn = btn("Sign In")
        login_btn.setMinimumHeight(42)
        login_btn.clicked.connect(self._do_login)
        ll.addWidget(self.login_email)
        ll.addWidget(self.login_password)
        ll.addWidget(login_btn)
        self.tabs.addTab(login_w, "Sign In")

        # Register tab
        reg_w = QWidget()
        rl = QVBoxLayout(reg_w)
        rl.setContentsMargins(12, 16, 12, 12)
        rl.setSpacing(12)
        self.reg_name = QLineEdit()
        self.reg_name.setPlaceholderText("Full name")
        self.reg_email = QLineEdit()
        self.reg_email.setPlaceholderText("Email address")
        self.reg_password = QLineEdit()
        self.reg_password.setPlaceholderText("Password (min 8 chars)")
        self.reg_password.setEchoMode(QLineEdit.EchoMode.Password)
        reg_btn = btn("Create Account")
        reg_btn.setMinimumHeight(42)
        reg_btn.clicked.connect(self._do_register)
        rl.addWidget(self.reg_name)
        rl.addWidget(self.reg_email)
        rl.addWidget(self.reg_password)
        rl.addWidget(reg_btn)
        self.tabs.addTab(reg_w, "Register")

        layout.addWidget(self.tabs)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {C['error']}; font-size: 12px;")
        self.error_label.setWordWrap(True)
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.error_label)
        layout.addStretch()

    def _do_login(self):
        self.error_label.setText("")
        try:
            self.api.login(self.login_email.text().strip(), self.login_password.text())
            self.accept()
        except APIError as e:
            self.error_label.setText(f"❌ {e.message}")

    def _do_register(self):
        self.error_label.setText("")
        if len(self.reg_password.text()) < 8:
            self.error_label.setText("❌ Password must be at least 8 characters")
            return
        try:
            self.api.register(
                self.reg_email.text().strip(),
                self.reg_name.text().strip(),
                self.reg_password.text()
            )
            self.accept()
        except APIError as e:
            self.error_label.setText(f"❌ {e.message}")


# ─── Main Window ──────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self, api: Claim360API):
        super().__init__()
        self.api = api
        self.setWindowTitle("Claim360 Email WebApp")
        self.setMinimumSize(1100, 720)
        self.setStyleSheet(STYLESHEET)
        self._build()
        self._refresh_user()

    def _build(self):
        central = QWidget()
        central.setStyleSheet(f"background-color: {C['bg']};")
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Nav
        self.nav = NavMenu()
        self.nav.page_changed.connect(self._switch_page)
        main_layout.addWidget(self.nav)

        # Pages
        self.pages = QStackedWidget()
        self.pages.setStyleSheet(f"background-color: {C['bg']};")
        main_layout.addWidget(self.pages, 1)

        self._config_page = ConfigPage(self.api)
        self._data_page = DataPage(self.api)
        self._template_page = TemplatePage(self.api)
        self._preview_page = PreviewPage(self.api)
        self._send_page = SendPage(self.api)
        self._tracking_page = TrackingPage(self.api)
        self._admin_page = AdminPage(self.api)

        for p in [self._config_page, self._data_page, self._template_page,
                  self._preview_page, self._send_page, self._tracking_page, self._admin_page]:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(p)
            scroll.setStyleSheet(f"QScrollArea {{ border: none; background: {C['bg']}; }}")
            self.pages.addWidget(scroll)

        # Wire data flow
        self._data_page.contacts_updated.connect(self._on_contacts_updated)

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready")

        # Logout menu
        logout_action = QAction("Logout", self)
        logout_action.triggered.connect(self._logout)
        menubar = self.menuBar()
        menubar.setStyleSheet(f"background: {C['nav_bg']}; color: {C['text']};")
        account_menu = menubar.addMenu("Account")
        account_menu.addAction(logout_action)

    def _refresh_user(self):
        try:
            me = self.api.get_me()
            self.setWindowTitle(f"Claim360 Email WebApp — {me['full_name']} ({me['email']})")
            self.nav.set_admin_visible(me.get("is_admin", False))
            if not me.get("is_admin"):
                pass  # already hidden
            self.status.showMessage(f"Logged in as {me['email']}")
        except Exception:
            pass

    def _switch_page(self, idx: int):
        self.pages.setCurrentIndex(idx)
        # Refresh preview/send data when switching to those pages
        if idx == 3:  # Preview
            self._preview_page.update_data(
                self._template_page.get_templates(),
                self._data_page.contacts
            )
        elif idx == 4:  # Send
            self._send_page.update_data(
                self._data_page.contacts,
                self._data_page.variable_names,
                self._template_page.get_templates(),
            )
        elif idx == 5:  # Tracking
            self._tracking_page._refresh_campaigns()
        elif idx == 6:  # Admin
            self._admin_page._load_stats()

    def _on_contacts_updated(self, contacts, variable_names):
        self._send_page.update_data(contacts, variable_names, self._template_page.get_templates())
        self._preview_page.update_data(self._template_page.get_templates(), contacts)
        self.status.showMessage(f"✅ {len(contacts)} contacts loaded")

    def _logout(self):
        self.api.clear_token()
        self.hide()
        _show_login(self.api)
        self.show()


def _show_login(api: Claim360API):
    dlg = LoginDialog(api)
    if dlg.exec() != QDialog.DialogCode.Accepted:
        sys.exit(0)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Claim360 Email WebApp")
    app.setStyle("Fusion")

    # Dark palette for native widgets
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(C["bg"]))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(C["text"]))
    palette.setColor(QPalette.ColorRole.Base, QColor(C["surface"]))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(C["card"]))
    palette.setColor(QPalette.ColorRole.Text, QColor(C["text"]))
    palette.setColor(QPalette.ColorRole.Button, QColor(C["surface"]))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(C["text"]))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(C["accent"]))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(C["bg"]))
    app.setPalette(palette)
    app.setStyleSheet(STYLESHEET)

    api = Claim360API(BACKEND_URL)

    # Login
    _show_login(api)

    window = MainWindow(api)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
