import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit, QComboBox, QMessageBox, QFileDialog
)
from PyQt6.QtGui import QTextDocument, QKeySequence
from PyQt6.QtCore import QTimer, Qt, QEvent
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from deep_translator import GoogleTranslator  # Neue Übersetzungsbibliothek
from utils import get_installed_models, generate_ollama_prompt  # Eigene Hilfsfunktionen

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.dialog_context = []  # Speichert den gesamten Dialogkontext
        self.current_interaction = []  # Speichert nur die aktuelle Interaktion

    def initUI(self):
        self.setWindowTitle('2024 / Ollama-Chatbot 2.1 | by Der Zerfleischer on ')
        self.setFixedSize(800, 890)

        # Globales Stylesheet für alle Widgets
        self.setStyleSheet("""
            QWidget {
                font-size: 14px;
            }
            QPushButton {
                background-color:rgb(31, 84, 30);
                color: rgb(215, 215, 215);
                border: none;
                padding: 8px 16px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 14px;
                margin: 4px 2px;
                cursor: pointer;
                border-radius: 15px;
            }
            QPushButton:hover {
                background-color:rgb(115, 115, 115);
                font-size: 14px;
                color: rgb(215, 215, 215);
            }
            QComboBox {
                font-size: 14px;
                background-color:rgb(61, 0, 0);
                color: rgb(215, 215, 215);
                border: 1px solid rgb(31, 84, 30);
            }
            QTextEdit {
                font-size: 14px;
                color: rgb(215, 215, 215);
                padding: 5px;
                border: 2px solid rgb(31, 84, 30);
                border-radius: 10px;
                background-color: rgb(33, 33, 33);
            }
            QLabel {
                font-size: 14px;
                color: rgb(215, 215, 215);
                margin-bottom: 5px;
            }
        """)

        layout = QVBoxLayout()

        # Modell-Auswahl
        self.model_label = QLabel('Ollama Modelle / Ollama models:')
        layout.addWidget(self.model_label)

        self.model_combo = QComboBox()
        self.model_combo.setMinimumHeight(25)
        self.load_models()
        layout.addWidget(self.model_combo)

        # Sprachauswahl
        self.language_label = QLabel('Sprache auswählen / Select Language:')
        layout.addWidget(self.language_label)

        self.language_combo = QComboBox()
        self.language_combo.addItems([
            'Deutsch',  # de
            'Englisch',  # en
            'Französisch',  # fr
            'Spanisch',  # es
            'Italienisch',  # it
            'Lateinisch'  # la
        ])
        layout.addWidget(self.language_combo)

        # Eingabe-Anweisung
        self.anweisung_label = QLabel('Anweisung / Instruction:')
        layout.addWidget(self.anweisung_label)

        self.anweisung_input = QTextEdit()
        self.anweisung_input.setMaximumHeight(90)
        self.anweisung_input.installEventFilter(self)
        layout.addWidget(self.anweisung_input)

        # Generate Button
        self.generate_button = QPushButton('Generieren / Generate')
        self.generate_button.clicked.connect(self.generate_text)
        layout.addWidget(self.generate_button)

        # Generierte Antwort
        self.generated_text_label = QLabel('Aktuelle Antwort / Current response:')
        layout.addWidget(self.generated_text_label)

        self.generated_text_edit = QTextEdit()
        self.generated_text_edit.setMinimumSize(0, 300)
        layout.addWidget(self.generated_text_edit)

        # Copy to clipboard Button
        self.copy_to_clipboard_button = QPushButton('In Zwischenablage kopieren / Copy to clipboard')
        self.copy_to_clipboard_button.clicked.connect(self.copy_to_clipboard)
        layout.addWidget(self.copy_to_clipboard_button)

        # Drucken und PDF speichern
        self.print_button = QPushButton('Drucken / Print')
        self.print_button.clicked.connect(self.print_result)
        layout.addWidget(self.print_button)

        self.save_pdf_button = QPushButton('Als PDF speichern / Save as PDF')
        self.save_pdf_button.clicked.connect(self.save_as_pdf)
        layout.addWidget(self.save_pdf_button)

        # Konversation zurücksetzen
        self.reset_conversation_button = QPushButton('Neues Gespräch / New conversation')
        self.reset_conversation_button.clicked.connect(self.reset_conversation)
        layout.addWidget(self.reset_conversation_button)

        self.setLayout(layout)

    def load_models(self):
        models = get_installed_models()
        if models:
            self.model_combo.addItems([f"Modell {k}: {v}" for k, v in models.items()])
        else:
            QMessageBox.critical(self, 'Fehler', 'Es sind keine Modelle installiert. Installiere bitte mindestens ein Modell.\nNo models are installed. Please install at least one model.')

    def eventFilter(self, source, event):
        if source == self.anweisung_input and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self.generate_text()
                return True
        return super().eventFilter(source, event)

    def generate_text(self):
        self.generate_button.setStyleSheet("background-color: green")
        QTimer.singleShot(100, self.reset_generate_button_color)

        selected_model = self.model_combo.currentText().split(': ')[1]
        selected_language = self.language_combo.currentText()  # Sprache auswählen
        anweisung = self.anweisung_input.toPlainText().strip()

        if not anweisung:
            QMessageBox.warning(self, 'Fehler', 'Die Anweisung darf nicht leer sein.\nThe instruction must not be empty')
            return

        # Sprachhinweis hinzufügen und Übersetzungslogik je nach Sprache
        language_map = {
            'Deutsch': 'de',
            'Englisch': 'en',
            'Französisch': 'fr',
            'Spanisch': 'es',
            'Italienisch': 'it',
            'Lateinisch': 'la'
        }
        target_language = language_map.get(selected_language, 'en')  # Standard: Englisch

        # Übersetze Benutzeranweisung in die gewünschte Sprache
        try:
            anweisung = GoogleTranslator(source='auto', target=target_language).translate(anweisung)
        except Exception as e:
            QMessageBox.critical(self, 'Übersetzungsfehler', f'Fehler bei der Übersetzung: {str(e)}')
            return

        # Kontext erstellen
        context = "\n".join(self.dialog_context) if self.dialog_context else ""
        prompt = f"{context}\nBitte antworte in {selected_language}.\nBenutzer: {anweisung}\nAI:"

        # Text generieren
        generated_text = generate_ollama_prompt(prompt, '', selected_model)

        if generated_text:
            # Übersetze die Antwort zurück in die gewünschte Sprache (falls nötig)
            try:
                generated_text = GoogleTranslator(source='auto', target=target_language).translate(generated_text)
            except Exception as e:
                QMessageBox.critical(self, 'Übersetzungsfehler', f'Fehler bei der Übersetzung: {str(e)}')
                return # Hinzugefügt: Beende die Funktion, wenn die Übersetzung fehlschlägt

            # Entferne das führende Anführungszeichen, falls vorhanden
            generated_text = generated_text.lstrip().replace('"', '', 1)

            self.dialog_context.append(f"Benutzer: {anweisung}")
            self.dialog_context.append(f"AI: {generated_text}")
            self.current_interaction = [f"Benutzer: {anweisung}", f"AI: {generated_text}"]
            self.generated_text_edit.setPlainText("\n".join(self.current_interaction))
        else:
            QMessageBox.critical(self, 'Fehler', 'Fehler bei der Generierung des Textes!')

    def copy_to_clipboard(self):
        self.copy_to_clipboard_button.setStyleSheet("background-color: green")
        QTimer.singleShot(100, self.reset_clipboard_button_color)

        generated_text = self.generated_text_edit.toPlainText()
        if generated_text:
            clipboard = QApplication.clipboard()
            clipboard.setText(generated_text)
            QMessageBox.information(self, "Erfolg", "Der Text wurde in die Zwischenablage kopiert!")
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

    def reset_conversation(self):
        """Setzt die Konversation zurück und leert die Historie."""
        self.dialog_context = []
        self.current_interaction = []
        self.generated_text_edit.clear()
        self.anweisung_input.clear()
        QMessageBox.information(self, "Gespräch zurückgesetzt", "Das Gespräch wurde erfolgreich zurückgesetzt.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec())
