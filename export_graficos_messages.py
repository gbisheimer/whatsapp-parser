import os
import csv
import re
import argparse
import glob

# Configuración base
BASE_DIR = r"C:\Users\gbisheimer\Google Drive\Inversiones\Chats"
DEFAULT_OUTPUT = "mensajes_graficos.csv"

def extract_ticker(text):
    match = re.search(r'\$([A-Z0-9]{1,6})\b', text)
    if match:
        return match.group(1).upper()
    # Busca patrones comunes como "AAPL" o "KO" en mayúsculas
    match = re.search(r'\b([A-Z]{2,6})\b', text)
    if match:
        return match.group(1).upper()
    return None

def get_target_files(input_args):
    if input_args:
        target_files = []
        for arg in input_args:
            path_pattern = os.path.join(BASE_DIR, arg)
            found = glob.glob(path_pattern)
            if not found and not any(c in arg for c in "*?[]"):
                if os.path.exists(os.path.join(BASE_DIR, arg)):
                    target_files.append(arg)
            else:
                target_files.extend([os.path.basename(f) for f in found])
        return sorted(list(set(target_files)))
    
    files = [f for f in os.listdir(BASE_DIR) if "WhatsApp" in f and f.endswith(".csv")]
    return sorted(files)

def generate_graficos_messages(input_files, output_filename, ticker_filter=None, to_console=False, full_message=False):
    files_to_process = get_target_files(input_files)
    
    if not files_to_process:
        print("No se encontraron archivos para procesar.")
        return

    all_messages = []
    seen_ids = set()
    
    if not to_console:
        print(f"Procesando {len(files_to_process)} archivo(s)...")

    for filename in files_to_process:
        date_str = filename[:10] if re.match(r'\d{4}-\d{2}-\d{2}', filename) else filename
        file_path = os.path.join(BASE_DIR, filename)
        
        if not os.path.isfile(file_path):
            continue

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f, delimiter=';', quotechar='"')
            for row in reader:
                if len(row) < 3:
                    continue
                
                time = row[0]
                sender = row[1]
                message = row[2].strip()
                
                # Filtrar solo por el canal de Gráficos
                if "Gráficos" not in sender or "#ASL" not in sender:
                    continue
                
                clean_msg = ' '.join(message.replace('\n', ' ').replace('\r', ' ').split())
                if not clean_msg:
                    continue

                # Filtrado por Ticker si se especifica
                if ticker_filter:
                    if ticker_filter.upper() not in clean_msg.upper():
                        continue

                msg_id = f"{date_str}|{sender}|{clean_msg}"
                if msg_id in seen_ids:
                    continue
                seen_ids.add(msg_id)
                
                all_messages.append({
                    "Fecha": date_str,
                    "Hora": time,
                    "Mensaje": clean_msg
                })

    if not all_messages:
        print("No se encontraron mensajes que coincidan con los criterios.")
        return

    if to_console:
        header = f"{'FECHA':<12} | {'HORA':<8} | {'MENSAJE'}"
        print("\n" + header)
        print("-" * 120)
        for m in all_messages:
            msg_display = m['Mensaje'] if full_message else f"{m['Mensaje'][:100]}..."
            print(f"{m['Fecha']:<12} | {m['Hora']:<8} | {msg_display}")
        print("-" * 120)
        print(f"Total: {len(all_messages)} mensajes encontrados.\n")
    else:
        fieldnames = ["Fecha", "Hora", "Mensaje"]
        with open(output_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';', extrasaction='ignore')
            writer.writeheader()
            writer.writerows(all_messages)
        print(f"Finalizado: Se guardaron {len(all_messages)} mensajes en {output_filename}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Exporta mensajes del canal Gráficos #ASL.")
    parser.add_argument('input', nargs='*', help='Archivos de entrada')
    parser.add_argument('-o', '--output', default=DEFAULT_OUTPUT, help=f'Archivo de salida')
    parser.add_argument('-t', '--ticker', help='Filtrar por ticker (ej: AAPL)')
    parser.add_argument('-c', '--console', action='store_true', help='Mostrar en consola')
    parser.add_argument('-f', '--full', action='store_true', help='Muestra el mensaje completo en consola')
    
    args = parser.parse_args()
    generate_graficos_messages(args.input, args.output, args.ticker, args.console, args.full)
