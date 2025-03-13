import subprocess
import os
import re
import logging
from datetime import datetime
import ollama

# Logging konfigurieren
logging.basicConfig(
    filename='script.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_installed_models():
    try:
        result = subprocess.run(
            ['/usr/local/bin/ollama', 'list'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        lines = result.stdout.strip().split('\n')
        if len(lines) <= 1:
            logging.warning("Keine Modelle gefunden.")
            return {}
        models = lines[1:]
        model_dict = {str(i + 1): model_line.split()[0] for i, model_line in enumerate(models)}
        logging.info(f"{len(model_dict)} Modelle gefunden.")
        return model_dict
    except subprocess.CalledProcessError as e:
        logging.error(f"Fehler beim Abrufen der Modelle: {e.stderr}")
        return {}
    except Exception as e:
        logging.error(f"Unbekannter Fehler beim Abrufen der Modelle: {e}")
        return {}

def generate_ollama_prompt(selected_anweisung, user_input, selected_model):
    try:
        client = ollama.Client()
        prompt = f"{selected_anweisung.strip()}\n{user_input.strip()}"
        response = client.generate(model=selected_model, prompt=prompt)
        if 'response' in response:
            generated_text = response['response'].strip()
            generated_text = generated_text.strip()  # Entfernt führende und nachfolgende Leerzeichen
            if generated_text.endswith('\n.'):
                generated_text = generated_text.replace('\n.', '').strip()  # Entfernt die Zeile mit dem Punkt am Ende (bei manchen LLM's ein häufiges Vorkommen)
            generated_text = generated_text.lstrip().lstrip('"').rstrip('"')  # Anführungszeichen am Anfang und am Ende entfernen
            return generated_text
    except Exception as e:
        logging.error(f"Fehler bei der Generierung des Textes: {e}")
        return None
