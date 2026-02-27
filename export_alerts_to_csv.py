import os
import csv
import re
import argparse
import glob
from datetime import datetime

# Configuración base
BASE_DIR = r"C:\Users\gbisheimer\Google Drive\Inversiones\Chats"
DEFAULT_OUTPUT = "alertas.csv"

def extract_ticker(text):
    match = re.search(r'\$([A-Z0-9]{1,6})\b', text)
    if match:
        return match.group(1)
    match = re.search(r'(?:Compra|Venta| de | \b)([A-Z]{2,6})\b', text, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return "N/A"

def determine_action(text):
    text_upper = text.upper()
    if "COMPRA" in text_upper or "COMPRAMOS" in text_upper:
        return "COMPRA"
    if "VENTA" in text_upper or "VENDEMOS" in text_upper or "SALIDA" in text_upper or "STOP LOSS" in text_upper:
        return "VENTA"
    return "OTRO"

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
    
    files = [f for f in os.listdir(BASE_DIR) if f.endswith("-WhatsApp.csv")]
    return sorted(files)

def generate_alerts(input_files, output_filename, to_console=False):
    files_to_process = get_target_files(input_files)
    
    if not files_to_process:
        print("No se encontraron archivos para procesar.")
        return

    all_alerts = []
    seen_ids = set()
    
    p_trade = re.compile(r"\b(COMPRA|VENTA|RECOMPRA|SALIDA|STOP LOSS|VENDEMOS|COMPRAMOS)\b", re.IGNORECASE)
    p_channel = re.compile(r'Alertas.*?#ASL', re.IGNORECASE)

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
                
                match_channel = p_channel.search(sender)
                if not match_channel:
                    continue
                
                channel_name = match_channel.group(0)
                
                if not p_trade.search(message):
                    continue

                temporalidad = "45'" if "45" in channel_name else "Diaria"
                clean_msg = ' '.join(message.replace('\n', ' ').replace('\r', ' ').split())
                
                msg_id = f"{date_str}|{time[:5]}|{clean_msg[:40]}"
                if msg_id in seen_ids:
                    continue
                seen_ids.add(msg_id)
                
                all_alerts.append({
                    "Fecha": date_str,
                    "Hora": time,
                    "Tipo": temporalidad,
                    "Activo": extract_ticker(clean_msg),
                    "Acción": determine_action(clean_msg),
                    "Mensaje": clean_msg
                })

    if not all_alerts:
        print("No se encontraron alertas oficiales en los archivos seleccionados.")
        return

    if to_console:
        # Imprimir en consola con formato de tabla simple
        header = f"{'FECHA':<12} | {'HORA':<8} | {'TIPO':<7} | {'ACTIVO':<8} | {'ACCIÓN':<8} | {'MENSAJE'}"
        print("\n" + header)
        print("-" * 100)
        for a in all_alerts:
            print(f"{a['Fecha']:<12} | {a['Hora']:<8} | {a['Tipo']:<7} | {a['Activo']:<8} | {a['Acción']:<8} | {a['Mensaje'][:80]}...")
        print("-" * 100)
        print(f"Total: {len(all_alerts)} alertas encontradas.\n")
    else:
        fieldnames = ["Fecha", "Hora", "Tipo", "Activo", "Acción", "Mensaje"]
        with open(output_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';', extrasaction='ignore')
            writer.writeheader()
            writer.writerows(all_alerts)
        print(f"Finalizado: Se guardaron {len(all_alerts)} alertas en {output_filename}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Exporta alertas de chats de WhatsApp a CSV o consola.")
    parser.add_argument('input', nargs='*', help='Archivos de entrada o patrones glob (ej: *WhatsApp.csv)')
    parser.add_argument('-o', '--output', default=DEFAULT_OUTPUT, help=f'Nombre del archivo de salida (por defecto: {DEFAULT_OUTPUT})')
    parser.add_argument('-c', '--console', action='store_true', help='Muestra el resultado por consola en lugar de exportar a CSV')
    
    args = parser.parse_args()
    generate_alerts(args.input, args.output, args.console)
