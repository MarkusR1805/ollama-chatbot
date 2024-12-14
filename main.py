import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit, QComboBox, QMessageBox, QFileDialog
)
from PyQt6.QtGui import QFont, QPageLayout, QTextDocument
from PyQt6.QtCore import QTimer
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
from utils import get_installed_models, generate_ollama_prompt


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('2024 / Ollama-Chatbot 1.0 | by Der Zerfleischer on ')
        self.setFixedSize(800, 600)

        layout = QVBoxLayout()

        self.model_label = QLabel('Ollama Modelle / Ollama models:')
        layout.addWidget(self.model_label)

        self.model_combo = QComboBox()#
        self.model_combo.setMinimumHeight(25)
        self.load_models()
        layout.addWidget(self.model_combo)

        self.anweisung_label = QLabel('Anweisung / Instruction:')
        layout.addWidget(self.anweisung_label)

        self.anweisung_input = QTextEdit()
        self.anweisung_input.setMaximumHeight(90)
        layout.addWidget(self.anweisung_input)

        self.generate_button = QPushButton('Generieren / Generate')
        self.generate_button.clicked.connect(self.generate_text)
        layout.addWidget(self.generate_button)

        self.generated_text_label = QLabel('Generierter Prompt / Generated prompt:')
        layout.addWidget(self.generated_text_label)

        self.generated_text_edit = QTextEdit()
        self.generated_text_edit.setMinimumSize(0, 70)
        layout.addWidget(self.generated_text_edit)

        self.copy_to_clipboard_button = QPushButton('In Zwischenablage kopieren / Copy to clipboard')
        self.copy_to_clipboard_button.clicked.connect(self.copy_to_clipboard)
        layout.addWidget(self.copy_to_clipboard_button)

        # Buttons für Drucken und PDF-Speichern
        self.print_button = QPushButton('Drucken / Print')
        self.print_button.clicked.connect(self.print_result)
        layout.addWidget(self.print_button)

        self.save_pdf_button = QPushButton('Als PDF speichern / Save as PDF')
        self.save_pdf_button.clicked.connect(self.save_as_pdf)
        layout.addWidget(self.save_pdf_button)

        self.setLayout(layout)

    def load_models(self):
        models = get_installed_models()
        if models:
            self.model_combo.addItems([f"Modell {k}: {v}" for k, v in models.items()])
        else:
            QMessageBox.critical(self, 'Fehler', 'Es sind keine Modelle installiert. Installiere bitte mindestens ein Modell.\nNo models are installed. Please install at least one model.')

    def generate_text(self):
        self.generate_button.setStyleSheet("background-color: green")
        QTimer.singleShot(100, self.reset_generate_button_color)

        selected_model = self.model_combo.currentText().split(': ')[1]
        anweisung = self.anweisung_input.toPlainText().strip()

        if not anweisung:
            QMessageBox.warning(self, 'Fehler', 'Die Anweisung darf nicht leer sein.\nThe instruction must not be empty')
            return

        generated_text = generate_ollama_prompt(anweisung, '', selected_model)

        if generated_text:
            self.generated_text_edit.setPlainText(generated_text)
        else:
            QMessageBox.critical(self, 'Fehler', 'Fehler bei der Generierung des Textes!')

    def copy_to_clipboard(self):
        self.copy_to_clipboard_button.setStyleSheet("background-color: green")
        QTimer.singleShot(100, self.reset_clipboard_button_color)

        generated_text = self.generated_text_edit.toPlainText()
        if generated_text:
            clipboard = QApplication.clipboard()
            clipboard.setText(generated_text)
        else:
            QMessageBox.warning(self, 'Fehler', 'Es gibt keinen generierten Text, der in die Zwischenablage kopiert werden kann.\nThere is no generated text that can be copied to the clipboard.')

    def print_result(self):
        dialog = QPrintDialog()
        if dialog.exec():
            printer = dialog.printer()
            document = QTextDocument()
            document.setPlainText(self.generated_text_edit.toPlainText())
            document.print(printer)

    def save_as_pdf(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Als PDF speichern", "", "PDF-Dateien (*.pdf)")
        if file_path:
            printer = QPrinter()
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(file_path)

            document = QTextDocument()
            document.setPlainText(self.generated_text_edit.toPlainText())
            document.print(printer)

            QMessageBox.information(self, "Erfolg", "Die Datei wurde erfolgreich gespeichert!")

    def reset_generate_button_color(self):
        self.generate_button.setStyleSheet("")

    def reset_clipboard_button_color(self):
        self.copy_to_clipboard_button.setStyleSheet("")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec())
