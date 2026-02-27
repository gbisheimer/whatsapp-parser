import os
import csv
import re
import argparse
import glob

# Configuración base
BASE_DIR = r"C:\Users\gbisheimer\Google Drive\Inversiones\Chats"
DEFAULT_OUTPUT = "mensajes_asl.csv"

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
    
    # Busca archivos que contengan "WhatsApp" y terminen en ".csv"
    files = [f for f in os.listdir(BASE_DIR) if "WhatsApp" in f and f.endswith(".csv")]
    return sorted(files)

def generate_asl_messages(input_files, output_filename, to_console=False, last_n=None):
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
                
                # Criterios de filtrado de canal: Termina en #ASL y NO es Café Platinum ni Alertas
                if "#ASL" not in sender:
                    continue
                if "Café Platinum" in sender or "Café" in sender:
                    continue
                if "Alertas" in sender: # Excluimos Alertas porque ya tienen su propio script
                    continue
                
                # Limpiar mensaje (quitar saltos de línea para el CSV)
                clean_msg = ' '.join(message.replace('\n', ' ').replace('\r', ' ').split())
                
                if not clean_msg: # Ignorar mensajes vacíos
                    continue

                # Deduplicación: Evita el mismo mensaje exacto el mismo día en el mismo canal
                msg_id = f"{date_str}|{sender}|{clean_msg}"
                if msg_id in seen_ids:
                    continue
                seen_ids.add(msg_id)
                
                all_messages.append({
                    "Fecha": date_str,
                    "Hora": time,
                    "Canal": sender.split(' (')[0].strip(), # Limpieza básica del nombre del canal
                    "Mensaje": clean_msg
                })

    if not all_messages:
        print("No se encontraron mensajes en los archivos seleccionados.")
        return

    # Aplicar límite de resultados si se especifica
    if last_n and last_n > 0:
        all_messages = all_messages[-last_n:]

    if to_console:
        header = f"{'FECHA':<12} | {'HORA':<8} | {'CANAL':<30} | {'MENSAJE'}"
        print("\n" + header)
        print("-" * 120)
        for m in all_messages:
            print(f"{m['Fecha']:<12} | {m['Hora']:<8} | {m['Canal'][:30]:<30} | {m['Mensaje'][:60]}...")
        print("-" * 120)
        print(f"Total: {len(all_messages)} mensajes mostrados.\n")
    else:
        fieldnames = ["Fecha", "Hora", "Canal", "Mensaje"]
        with open(output_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';', extrasaction='ignore')
            writer.writeheader()
            writer.writerows(all_messages)
        print(f"Finalizado: Se guardaron {len(all_messages)} mensajes en {output_filename}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Muestra todos los mensajes de otros canales #ASL desde show_asl.py.")
    parser.add_argument('input', nargs='*', help='Archivos de entrada o patrones glob (ej: *WhatsApp*.csv)')
    parser.add_argument('-o', '--output', default=DEFAULT_OUTPUT, help=f'Nombre del archivo de salida (por defecto: {DEFAULT_OUTPUT})')
    parser.add_argument('-c', '--console', action='store_true', help='Muestra el resultado por consola en lugar de exportar a CSV')
    parser.add_argument('-n', '--last', type=int, help='Visualizar solo los N últimos resultados')
    
    args = parser.parse_args()
    generate_asl_messages(args.input, args.output, args.console, args.last)
