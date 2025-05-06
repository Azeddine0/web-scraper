import sys
import requests
import os
import datetime
import json
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QPushButton, QLineEdit, QTextEdit,
                            QLabel, QComboBox, QStatusBar, QTabWidget,
                            QProgressBar, QFileDialog, QGroupBox, QCheckBox,
                            QMessageBox, QSplitter, QSlider, QSizePolicy)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPalette, QColor, QFont, QIcon

class ScraperThread(QThread):
    progress_signal = pyqtSignal(int)
    result_signal = pyqtSignal(str, str)
    error_signal = pyqtSignal(str)

    def __init__(self, url, timeout=30, user_agent=None):
        super().__init__()
        self.url = url
        self.timeout = timeout
        self.user_agent = user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

    def run(self):
        try:
            self.progress_signal.emit(10)
            headers = {'User-Agent': self.user_agent}

            self.progress_signal.emit(30)
            response = requests.get(self.url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            self.progress_signal.emit(70)
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            title = soup.title.string if soup.title else 'No title'

            self.progress_signal.emit(100)
            self.result_signal.emit(html_content, title)

        except Exception as e:
            self.error_signal.emit(str(e))
            self.progress_signal.emit(0)

class ExtractorThread(QThread):
    progress_signal = pyqtSignal(int)
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, html_content, selector, extract_text=True, extract_links=True,
                 extract_images=False, extract_html=False):
        super().__init__()
        self.html_content = html_content
        self.selector = selector
        self.extract_text = extract_text
        self.extract_links = extract_links
        self.extract_images = extract_images
        self.extract_html = extract_html

    def run(self):
        try:
            self.progress_signal.emit(20)
            soup = BeautifulSoup(self.html_content, 'html.parser')
            elements = soup.select(self.selector)

            self.progress_signal.emit(50)

            if not elements:
                self.result_signal.emit(f"No elements found matching selector: {self.selector}")
                self.progress_signal.emit(100)
                return

            result = f"Found {len(elements)} elements matching '{self.selector}':\n\n"

            for i, element in enumerate(elements, 1):
                result += f"--- Element {i} ---\n"

                if self.extract_text:
                    result += f"Text: {element.get_text(strip=True)}\n"

                if self.extract_links and element.name == 'a':
                    result += f"Link: {element.get('href', 'No link')}\n"
                elif self.extract_links:
                    links = element.find_all('a')
                    if links:
                        result += "Links found:\n"
                        for j, link in enumerate(links[:5], 1):
                            result += f"  {j}. {link.get('href', 'No link')}\n"
                        if len(links) > 5:
                            result += f"  ... and {len(links) - 5} more links\n"

                if self.extract_images:
                    images = element.find_all('img')
                    if images:
                        result += "Images found:\n"
                        for j, img in enumerate(images[:3], 1):
                            result += f"  {j}. {img.get('src', 'No source')} - Alt: {img.get('alt', 'No alt text')}\n"
                        if len(images) > 3:
                            result += f"  ... and {len(images) - 3} more images\n"

                if self.extract_html:
                    html = str(element)
                    if len(html) > 500:
                        result += f"HTML: {html[:500]}...\n"
                    else:
                        result += f"HTML: {html}\n"

                result += "\n"

            self.progress_signal.emit(100)
            self.result_signal.emit(result)

        except Exception as e:
            self.error_signal.emit(str(e))
            self.progress_signal.emit(0)

# Custom toggle switch for dark/light mode
class ThemeSwitch(QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 30)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw the background
        if self.isChecked():
            # Dark mode
            background_color = QColor(40, 44, 52)
            switch_color = QColor(255, 255, 255)
            text = "Dark"
        else:
            # Light mode
            background_color = QColor(200, 200, 200)
            switch_color = QColor(255, 255, 255)
            text = "Light"

        # Draw rounded rectangle background
        painter.setPen(Qt.NoPen)
        painter.setBrush(background_color)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 15, 15)

        # Draw the switch circle
        if self.isChecked():
            circle_x = self.width() - 25
        else:
            circle_x = 5

        painter.setBrush(switch_color)
        painter.drawEllipse(circle_x, 5, 20, 20)

        # Draw text
        painter.setPen(QColor(255, 255, 255) if self.isChecked() else QColor(0, 0, 0))
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)

        text_x = 10 if self.isChecked() else 30
        painter.drawText(text_x, 20, text)

from PyQt5.QtGui import QPainter

class WebScraperApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Web Scraper Pro")
        self.setGeometry(100, 100, 900, 700)

        # Store the HTML content
        self.html_content = None
        self.page_title = None
        self.history = []
        self.load_history()

        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setTabPosition(QTabWidget.North)

        # Create scraper tab
        self.create_scraper_tab()

        # Create history tab
        self.create_history_tab()

        # Create settings tab
        self.create_settings_tab()

        # Add the tab widget to the main layout
        self.layout.addWidget(self.tab_widget)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Set initial theme
        self.current_theme = "Light"
        self.change_theme("Light")

    def create_scraper_tab(self):
        scraper_tab = QWidget()
        scraper_layout = QVBoxLayout(scraper_tab)

        # URL input area
        url_group = QGroupBox("URL Input")
        url_layout = QVBoxLayout()

        url_input_layout = QHBoxLayout()
        self.url_label = QLabel("URL:")
        self.url_label.setFont(QFont("Arial", 10))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter URL to scrape (e.g., https://example.com)")
        self.url_input.setMinimumHeight(30)

        self.scrape_button = QPushButton("Scrape")
        self.scrape_button.setMinimumHeight(30)
        self.scrape_button.clicked.connect(self.scrape_website)

        url_input_layout.addWidget(self.url_label)
        url_input_layout.addWidget(self.url_input)
        url_input_layout.addWidget(self.scrape_button)
        url_layout.addLayout(url_input_layout)

        # Advanced options
        advanced_options = QHBoxLayout()
        self.timeout_label = QLabel("Timeout (s):")
        self.timeout_input = QLineEdit("30")
        self.timeout_input.setMaximumWidth(60)

        self.user_agent_check = QCheckBox("Custom User-Agent")
        self.user_agent_check.stateChanged.connect(self.toggle_user_agent)
        self.user_agent_input = QLineEdit()
        self.user_agent_input.setPlaceholderText("Enter custom User-Agent")
        self.user_agent_input.setEnabled(False)

        advanced_options.addWidget(self.timeout_label)
        advanced_options.addWidget(self.timeout_input)
        advanced_options.addWidget(self.user_agent_check)
        advanced_options.addWidget(self.user_agent_input)
        url_layout.addLayout(advanced_options)

        url_group.setLayout(url_layout)
        scraper_layout.addWidget(url_group)

        # Selector area
        selector_group = QGroupBox("Content Extraction")
        selector_layout = QVBoxLayout()

        selector_input_layout = QHBoxLayout()
        self.selector_label = QLabel("CSS Selector:")
        self.selector_label.setFont(QFont("Arial", 10))
        self.selector_input = QLineEdit()
        self.selector_input.setPlaceholderText("Enter CSS selector (e.g., div.content, h1, a.link)")
        self.selector_input.setMinimumHeight(30)

        self.extract_button = QPushButton("Extract")
        self.extract_button.setMinimumHeight(30)
        self.extract_button.clicked.connect(self.extract_content)

        selector_input_layout.addWidget(self.selector_label)
        selector_input_layout.addWidget(self.selector_input)
        selector_input_layout.addWidget(self.extract_button)
        selector_layout.addLayout(selector_input_layout)

        # Extraction options
        extraction_options = QHBoxLayout()
        self.extract_text = QCheckBox("Text")
        self.extract_text.setChecked(True)
        self.extract_links = QCheckBox("Links")
        self.extract_links.setChecked(True)
        self.extract_images = QCheckBox("Images")
        self.extract_html = QCheckBox("HTML")

        extraction_options.addWidget(self.extract_text)
        extraction_options.addWidget(self.extract_links)
        extraction_options.addWidget(self.extract_images)
        extraction_options.addWidget(self.extract_html)
        extraction_options.addStretch()
        selector_layout.addLayout(extraction_options)

        selector_group.setLayout(selector_layout)
        scraper_layout.addWidget(selector_group)

        # Results area
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()

        self.results_area = QTextEdit()
        self.results_area.setReadOnly(True)
        self.results_area.setFont(QFont("Consolas", 10))
        self.results_area.setMinimumHeight(200)

        results_layout.addWidget(self.results_area)

        # Action buttons
        action_layout = QHBoxLayout()
        self.save_button = QPushButton("Save Results")
        self.save_button.clicked.connect(self.save_results)
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_results)

        action_layout.addWidget(self.save_button)
        action_layout.addWidget(self.clear_button)
        action_layout.addStretch()

        results_layout.addLayout(action_layout)
        results_group.setLayout(results_layout)
        scraper_layout.addWidget(results_group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        scraper_layout.addWidget(self.progress_bar)

        # Theme switch at bottom
        theme_layout = QHBoxLayout()
        self.theme_label = QLabel("Theme:")

        # Create the theme switch
        self.theme_switch = ThemeSwitch()
        self.theme_switch.stateChanged.connect(self.toggle_theme)

        theme_layout.addWidget(self.theme_label)
        theme_layout.addWidget(self.theme_switch)
        theme_layout.addStretch()
        scraper_layout.addLayout(theme_layout)

        # Add the scraper tab
        self.tab_widget.addTab(scraper_tab, "Web Scraper")

    def create_history_tab(self):
        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)

        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)

        # Buttons for history management
        history_buttons = QHBoxLayout()
        self.clear_history_button = QPushButton("Clear History")
        self.clear_history_button.clicked.connect(self.clear_history)
        self.load_url_button = QPushButton("Load Selected URL")
        self.load_url_button.clicked.connect(self.load_url_from_history)

        history_buttons.addWidget(self.clear_history_button)
        history_buttons.addWidget(self.load_url_button)
        history_buttons.addStretch()

        history_layout.addWidget(self.history_text)
        history_layout.addLayout(history_buttons)

        self.tab_widget.addTab(history_tab, "History")
        self.update_history_display()

    def create_settings_tab(self):
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)

        # General settings group
        general_group = QGroupBox("General Settings")
        general_layout = QVBoxLayout()

        # Default timeout
        timeout_layout = QHBoxLayout()
        self.default_timeout_label = QLabel("Default Timeout (seconds):")
        self.default_timeout_input = QLineEdit("30")
        timeout_layout.addWidget(self.default_timeout_label)
        timeout_layout.addWidget(self.default_timeout_input)
        timeout_layout.addStretch()
        general_layout.addLayout(timeout_layout)

        # Default user agent
        user_agent_layout = QHBoxLayout()
        self.default_user_agent_label = QLabel("Default User-Agent:")
        self.default_user_agent_input = QLineEdit("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        user_agent_layout.addWidget(self.default_user_agent_label)
        user_agent_layout.addWidget(self.default_user_agent_input)
        general_layout.addLayout(user_agent_layout)

        # Font settings
        font_layout = QHBoxLayout()
        self.font_size_label = QLabel("Results Font Size:")
        self.font_size_selector = QComboBox()
        self.font_size_selector.addItems(["8", "9", "10", "11", "12", "14", "16"])
        self.font_size_selector.setCurrentText("10")
        self.font_size_selector.currentTextChanged.connect(self.change_font_size)

        font_layout.addWidget(self.font_size_label)
        font_layout.addWidget(self.font_size_selector)
        font_layout.addStretch()
        general_layout.addLayout(font_layout)

        general_group.setLayout(general_layout)
        settings_layout.addWidget(general_group)

        # Save settings button
        self.save_settings_button = QPushButton("Save Settings")
        self.save_settings_button.clicked.connect(self.save_settings)
        settings_layout.addWidget(self.save_settings_button)

        settings_layout.addStretch()
        self.tab_widget.addTab(settings_tab, "Settings")

    def toggle_user_agent(self, state):
        self.user_agent_input.setEnabled(state == Qt.Checked)

    def toggle_theme(self, state):
        theme = "Dark" if state else "Light"
        self.change_theme(theme)

    def scrape_website(self):
        url = self.url_input.text().strip()
        if not url:
            self.status_bar.showMessage("Please enter a URL", 3000)
            return

        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            self.url_input.setText(url)

        try:
            timeout = int(self.timeout_input.text())
        except ValueError:
            self.status_bar.showMessage("Invalid timeout value, using default", 3000)
            timeout = 30

        user_agent = None
        if self.user_agent_check.isChecked():
            user_agent = self.user_agent_input.text()

        self.progress_bar.setValue(0)
        self.status_bar.showMessage("Scraping website...")
        self.scrape_button.setEnabled(False)

        # Create and start the scraper thread
        self.scraper_thread = ScraperThread(url, timeout, user_agent)
        self.scraper_thread.progress_signal.connect(self.update_progress)
        self.scraper_thread.result_signal.connect(self.handle_scrape_result)
        self.scraper_thread.error_signal.connect(self.handle_scrape_error)
        self.scraper_thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def handle_scrape_result(self, html_content, title):
        self.html_content = html_content
        self.page_title = title

        self.results_area.setText(f"Website scraped successfully!\n\nPage title: {title}\n\nUse CSS selector to extract specific content.")
        self.status_bar.showMessage("Website scraped successfully", 3000)
        self.scrape_button.setEnabled(True)

        # Add to history
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.history.append({
            "url": self.url_input.text(),
            "title": title,
            "timestamp": timestamp
        })
        self.save_history()
        self.update_history_display()

    def handle_scrape_error(self, error_message):
        self.status_bar.showMessage(f"Error: {error_message}", 5000)
        self.results_area.setText(f"Error scraping website: {error_message}")
        self.scrape_button.setEnabled(True)

    def extract_content(self):
        if not self.html_content:
            self.status_bar.showMessage("Please scrape a website first", 3000)
            return

        selector = self.selector_input.text().strip()
        if not selector:
            self.status_bar.showMessage("Please enter a CSS selector", 3000)
            return

        self.progress_bar.setValue(0)
        self.status_bar.showMessage("Extracting content...")
        self.extract_button.setEnabled(False)

        # Create and start the extractor thread
        self.extractor_thread = ExtractorThread(
            self.html_content,
            selector,
            self.extract_text.isChecked(),
            self.extract_links.isChecked(),
            self.extract_images.isChecked(),
            self.extract_html.isChecked()
        )
        self.extractor_thread.progress_signal.connect(self.update_progress)
        self.extractor_thread.result_signal.connect(self.handle_extract_result)
        self.extractor_thread.error_signal.connect(self.handle_extract_error)
        self.extractor_thread.start()

    def handle_extract_result(self, result):
        self.results_area.setText(result)
        self.status_bar.showMessage("Content extracted successfully", 3000)
        self.extract_button.setEnabled(True)

    def handle_extract_error(self, error_message):
        self.status_bar.showMessage(f"Error: {error_message}", 5000)
        self.results_area.setText(f"Error extracting content: {error_message}")
        self.extract_button.setEnabled(True)

    def save_results(self):
        if not self.results_area.toPlainText():
            self.status_bar.showMessage("No results to save", 3000)
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Results", "", "Text Files (*.txt);;HTML Files (*.html);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(self.results_area.toPlainText())
                self.status_bar.showMessage(f"Results saved to {file_path}", 3000)
            except Exception as e:
                self.status_bar.showMessage(f"Error saving results: {str(e)}", 5000)

    def clear_results(self):
        self.results_area.clear()
        self.progress_bar.setValue(0)
        self.status_bar.showMessage("Results cleared", 2000)

    def change_theme(self, theme_name):
        app = QApplication.instance()
        palette = QPalette()

        if theme_name == "Dark":
            # Dark theme colors
            palette.setColor(QPalette.Window, QColor(40, 44, 52))
            palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
            palette.setColor(QPalette.Base, QColor(30, 34, 42))
            palette.setColor(QPalette.AlternateBase, QColor(50, 54, 62))
            palette.setColor(QPalette.ToolTipBase, QColor(30, 34, 42))
            palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
            palette.setColor(QPalette.Text, QColor(255, 255, 255))
            palette.setColor(QPalette.Button, QColor(50, 54, 62))
            palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
            palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
            palette.setColor(QPalette.Link, QColor(42, 130, 218))
            palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))

            # Style the buttons with explicit text color
            button_style = "background-color: #4B8BBE; color: white; border-radius: 4px; padding: 5px 15px;"
            self.scrape_button.setStyleSheet(button_style)
            self.extract_button.setStyleSheet(button_style)
            self.save_button.setStyleSheet(button_style)
            self.clear_button.setStyleSheet(button_style)
            self.clear_history_button.setStyleSheet(button_style)
            self.load_url_button.setStyleSheet(button_style)
            self.save_settings_button.setStyleSheet(button_style)

            # Explicitly set text color for all text inputs
            text_input_style = "color: white; background-color: #30343A; border: 1px solid #555;"
            self.url_input.setStyleSheet(text_input_style)
            self.timeout_input.setStyleSheet(text_input_style)
            self.user_agent_input.setStyleSheet(text_input_style)
            self.selector_input.setStyleSheet(text_input_style)
            self.default_timeout_input.setStyleSheet(text_input_style)
            self.default_user_agent_input.setStyleSheet(text_input_style)

            # Set text color for text areas
            text_area_style = "color: white; background-color: #30343A; border: 1px solid #555;"
            self.results_area.setStyleSheet(text_area_style)
            self.history_text.setStyleSheet(text_area_style)

            # Set text color for labels
            label_style = "color: white;"
            self.url_label.setStyleSheet(label_style)
            self.timeout_label.setStyleSheet(label_style)
            self.selector_label.setStyleSheet(label_style)
            self.theme_label.setStyleSheet(label_style)
            self.default_timeout_label.setStyleSheet(label_style)
            self.default_user_agent_label.setStyleSheet(label_style)
            self.font_size_label.setStyleSheet(label_style)

            # Set text color for checkboxes
            checkbox_style = "color: white;"
            self.user_agent_check.setStyleSheet(checkbox_style)
            self.extract_text.setStyleSheet(checkbox_style)
            self.extract_links.setStyleSheet(checkbox_style)
            self.extract_images.setStyleSheet(checkbox_style)
            self.extract_html.setStyleSheet(checkbox_style)

            # Set style for combo boxes
            combobox_style = "color: white; background-color: #30343A; border: 1px solid #555; selection-background-color: #4B8BBE;"
            self.font_size_selector.setStyleSheet(combobox_style)

            # Set style for group boxes
            groupbox_style = "QGroupBox { color: white; border: 1px solid #555; margin-top: 1.5ex; } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 5px; }"
            for group_box in self.findChildren(QGroupBox):
                group_box.setStyleSheet(groupbox_style)

            # Set style for progress bar
            progress_style = "QProgressBar { border: 1px solid #555; border-radius: 3px; text-align: center; color: white; } QProgressBar::chunk { background-color: #4B8BBE; }"
            self.progress_bar.setStyleSheet(progress_style)

            # Fix tab widget styling
            tab_style = """
                QTabWidget::pane { border: 1px solid #555; }
                QTabBar::tab {
                    background-color: #30343A;
                    color: white;
                    padding: 8px 12px;
                    margin-right: 2px;
                    border: 1px solid #555;
                    border-bottom: none;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                }
                QTabBar::tab:selected {
                    background-color: #40444C;
                    border-bottom: none;
                }
                QTabBar::tab:!selected {
                    margin-top: 2px;
                }
            """
            self.tab_widget.setStyleSheet(tab_style)

        else:
            # Light theme - custom light
            palette.setColor(QPalette.Window, QColor(240, 240, 245))
            palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
            palette.setColor(QPalette.Base, QColor(255, 255, 255))
            palette.setColor(QPalette.AlternateBase, QColor(233, 233, 238))
            palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
            palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
            palette.setColor(QPalette.Text, QColor(0, 0, 0))
            palette.setColor(QPalette.Button, QColor(225, 225, 230))
            palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
            palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
            palette.setColor(QPalette.Link, QColor(42, 130, 218))
            palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))

            # Style the buttons with explicit text color
            button_style = "background-color: #2A82DA; color: white; border-radius: 4px; padding: 5px 15px;"
            self.scrape_button.setStyleSheet(button_style)
            self.extract_button.setStyleSheet(button_style)

            normal_button_style = "color: black; padding: 5px 15px;"
            self.save_button.setStyleSheet(normal_button_style)
            self.clear_button.setStyleSheet(normal_button_style)
            self.clear_history_button.setStyleSheet(normal_button_style)
            self.load_url_button.setStyleSheet(normal_button_style)
            self.save_settings_button.setStyleSheet(normal_button_style)

            # Explicitly set text color for all text inputs
            text_input_style = "color: black; background-color: white; border: 1px solid #CCC;"
            self.url_input.setStyleSheet(text_input_style)
            self.timeout_input.setStyleSheet(text_input_style)
            self.user_agent_input.setStyleSheet(text_input_style)
            self.selector_input.setStyleSheet(text_input_style)
            self.default_timeout_input.setStyleSheet(text_input_style)
            self.default_user_agent_input.setStyleSheet(text_input_style)

            # Set text color for text areas
            text_area_style = "color: black; background-color: white; border: 1px solid #CCC;"
            self.results_area.setStyleSheet(text_area_style)
            self.history_text.setStyleSheet(text_area_style)

            # Set text color for labels
            label_style = "color: black;"
            self.url_label.setStyleSheet(label_style)
            self.timeout_label.setStyleSheet(label_style)
            self.selector_label.setStyleSheet(label_style)
            self.theme_label.setStyleSheet(label_style)
            self.default_timeout_label.setStyleSheet(label_style)
            self.default_user_agent_label.setStyleSheet(label_style)
            self.font_size_label.setStyleSheet(label_style)

            # Set text color for checkboxes
            checkbox_style = "color: black;"
            self.user_agent_check.setStyleSheet(checkbox_style)
            self.extract_text.setStyleSheet(checkbox_style)
            self.extract_links.setStyleSheet(checkbox_style)
            self.extract_images.setStyleSheet(checkbox_style)
            self.extract_html.setStyleSheet(checkbox_style)

            # Set style for combo boxes
            combobox_style = "color: black; background-color: white; border: 1px solid #CCC;"
            self.font_size_selector.setStyleSheet(combobox_style)

            # Set style for group boxes
            groupbox_style = "QGroupBox { color: black; border: 1px solid #CCC; margin-top: 1.5ex; } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 5px; }"
            for group_box in self.findChildren(QGroupBox):
                group_box.setStyleSheet(groupbox_style)

            # Set style for progress bar
            progress_style = "QProgressBar { border: 1px solid #CCC; border-radius: 3px; text-align: center; color: black; } QProgressBar::chunk { background-color: #2A82DA; }"
            self.progress_bar.setStyleSheet(progress_style)

            # Fix tab widget styling
            tab_style = """
                QTabWidget::pane { border: 1px solid #CCC; }
                QTabBar::tab {
                    background-color: #F0F0F5;
                    color: black;
                    padding: 8px 12px;
                    margin-right: 2px;
                    border: 1px solid #CCC;
                    border-bottom: none;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                }
                QTabBar::tab:selected {
                    background-color: white;
                    border-bottom: none;
                }
                QTabBar::tab:!selected {
                    margin-top: 2px;
                }
            """
            self.tab_widget.setStyleSheet(tab_style)

        app.setPalette(palette)
        self.current_theme = theme_name

        # Update the theme switch state without triggering the signal
        self.theme_switch.blockSignals(True)
        self.theme_switch.setChecked(theme_name == "Dark")
        self.theme_switch.blockSignals(False)

        self.status_bar.showMessage(f"Theme changed to {theme_name}", 2000)

    def change_font_size(self, size):
        font = QFont("Consolas", int(size))
        self.results_area.setFont(font)
        self.history_text.setFont(font)

    def save_settings(self):
        # In a real app, you would save these to a config file
        QMessageBox.information(self, "Settings", "Settings saved successfully!")

    def load_history(self):
        try:
            if os.path.exists("scraper_history.json"):
                with open("scraper_history.json", "r") as file:
                    self.history = json.load(file)
        except Exception:
            self.history = []

    def save_history(self):
        try:
            with open("scraper_history.json", "w") as file:
                json.dump(self.history, file)
        except Exception as e:
            print(f"Error saving history: {e}")

    def update_history_display(self):
        if not self.history:
            self.history_text.setText("No scraping history yet.")
            return

        history_text = "Scraping History:\n\n"
        for i, entry in enumerate(reversed(self.history), 1):
            history_text += f"{i}. {entry['url']} - {entry['title']}\n"
            history_text += f"   Time: {entry['timestamp']}\n\n"

        self.history_text.setText(history_text)

    def clear_history(self):
        reply = QMessageBox.question(
            self, "Clear History",
            "Are you sure you want to clear all history?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.history = []
            self.save_history()
            self.update_history_display()
            self.status_bar.showMessage("History cleared", 2000)

    def load_url_from_history(self):
        if self.history:
            self.url_input.setText(self.history[0]["url"])
            self.tab_widget.setCurrentIndex(0)  # Switch to scraper tab
            self.status_bar.showMessage("URL loaded from history", 2000)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WebScraperApp()
    window.show()
    sys.exit(app.exec_())