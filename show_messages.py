import os
import csv
import re
import argparse
import glob

# Configuración base
BASE_DIR = os.getcwd()

def extract_ticker(text):
    match = re.search(r'\$([A-Z0-9]{1,6})\b', text)
    if match:
        return match.group(1).upper()
    match = re.search(r'(?:Compra|Venta| de | \b)([A-Z]{2,6})\b', text, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return "N/A"

def determine_action(text):
    text_upper = text.upper()
    if "COMPRA" in text_upper or "COMPRAMOS" in text_upper:
        return "COMPRA"
    if any(x in text_upper for x in ["VENTA", "VENDEMOS", "SALIDA", "STOP LOSS"]):
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
    
    files = [f for f in os.listdir(BASE_DIR) if "WhatsApp" in f and f.endswith(".csv")]
    return sorted(files)

def process_messages():
    parser = argparse.ArgumentParser(description="Herramienta unificada para visualizar mensajes de WhatsApp.")
    parser.add_argument('mode', choices=['alertas', 'graficos', 'asl', 'general', 'cafe'], help='Modo de visualización')
    parser.add_argument('input', nargs='*', help='Archivos de entrada')
    parser.add_argument('-t', '--ticker', help='Filtrar por ticker (modos: alerts, graficos)')
    parser.add_argument('-s', '--sender', help='Filtrar por remitente (modo: general)')
    parser.add_argument('-c', '--console', action='store_true', help='Mostrar en consola')
    parser.add_argument('-f', '--full', action='store_true', help='Mensaje completo en consola')
    parser.add_argument('-n', '--last', type=int, help='Mostrar solo los últimos N resultados')
    parser.add_argument('-o', '--output', help='Archivo de salida (opcional)')

    args = parser.parse_args()

    files_to_process = get_target_files(args.input)
    if not files_to_process:
        print("No se encontraron archivos para procesar.")
        return

    results = []
    seen_ids = set()
    
    # Patrones específicos
    p_trade = re.compile(r"\b(COMPRA|VENTA|RECOMPRA|SALIDA|STOP LOSS|VENDEMOS|COMPRAMOS)\b", re.IGNORECASE)
    p_alert_channel = re.compile(r'Alertas.*?#ASL', re.IGNORECASE)

    if not args.console:
        print(f"Modo [{args.mode}] - Procesando {len(files_to_process)} archivo(s)...")

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
                
                time, sender, message = row[0], row[1], row[2].strip()
                # Limpiamos el mensaje de saltos de línea
                clean_msg = message.replace('\n', ' ').replace('\r', ' ')
                clean_msg = ' '.join(clean_msg.split())
                if not clean_msg: continue

                # Lógica por modo
                if args.mode == 'alertas':
                    if not p_alert_channel.search(sender) or not p_trade.search(clean_msg):
                        continue
                    activo = extract_ticker(clean_msg)
                    if args.ticker and args.ticker.upper() != activo:
                        continue
                    msg_id = f"{date_str}|{clean_msg}"
                    if msg_id in seen_ids: continue
                    seen_ids.add(msg_id)
                    results.append({
                        "Fecha": date_str, "Hora": time, 
                        "Tipo": "45'" if "45" in sender else "Diaria",
                        "Activo": activo, "Acción": determine_action(clean_msg), 
                        "Mensaje": clean_msg
                    })

                elif args.mode == 'graficos':
                    if "Gráficos" not in sender or "#ASL" not in sender:
                        continue
                    if args.ticker and args.ticker.upper() not in clean_msg.upper():
                        continue
                    msg_id = f"{date_str}|{sender}|{clean_msg}"
                    if msg_id in seen_ids: continue
                    seen_ids.add(msg_id)
                    results.append({"Fecha": date_str, "Hora": time, "Mensaje": clean_msg})

                elif args.mode == 'asl':
                    if "#ASL" not in sender or any(x in sender for x in ["Café", "Alertas"]):
                        continue
                    if args.sender and args.sender.upper() not in sender.upper():
                        continue
                    msg_id = f"{date_str}|{sender}|{clean_msg}"
                    if msg_id in seen_ids: continue
                    seen_ids.add(msg_id)
                    parts = sender.split(': ')
                    canal = parts[0].split(' (')[0].strip()
                    remitente = parts[1].strip('~ \u202f') if len(parts) > 1 else "N/A"
                    results.append({"Fecha": date_str, "Hora": time, "Canal": canal, "Remitente": remitente, "Mensaje": clean_msg})

                elif args.mode == 'cafe':
                    if "Café" not in sender or "#ASL" not in sender:
                        continue
                    if args.sender and args.sender.upper() not in sender.upper():
                        continue
                    msg_id = f"{date_str}|{sender}|{clean_msg}"
                    if msg_id in seen_ids: continue
                    seen_ids.add(msg_id)
                    parts = sender.split(': ')
                    canal = parts[0].split(' (')[0].strip()
                    remitente = parts[1].strip('~ \u202f') if len(parts) > 1 else "N/A"
                    results.append({"Fecha": date_str, "Hora": time, "Canal": canal, "Remitente": remitente, "Mensaje": clean_msg})

                elif args.mode == 'general':
                    if "#ASL" in sender:
                        continue
                    if args.sender and args.sender.upper() not in sender.upper():
                        continue
                    msg_id = f"{date_str}|{sender}|{clean_msg}"
                    if msg_id in seen_ids: continue
                    seen_ids.add(msg_id)
                    results.append({"Fecha": date_str, "Hora": time, "Remitente": sender.split(' (')[0].strip(), "Mensaje": clean_msg})

    if not results:
        print("No se encontraron resultados que coincidan.")
        return

    # Límite
    if args.last and args.last > 0:
        results = results[-args.last:]

    # Salida
    if args.console:
        if args.mode == 'alertas':
            header = f"{'FECHA':<12} | {'HORA':<8} | {'TIPO':<7} | {'ACTIVO':<8} | {'ACCIÓN':<8} | {'MENSAJE'}"
            def get_fmt(r): return f"{r['Fecha']:<12} | {r['Hora']:<8} | {r['Tipo']:<7} | {r['Activo']:<8} | {r['Acción']:<8} | "
        elif args.mode in ['general']:
            header = f"{'FECHA':<12} | {'HORA':<8} | {'REMITENTE':<30} | {'MENSAJE'}"
            def get_fmt(r): return f"{r['Fecha']:<12} | {r['Hora']:<8} | {r['Remitente'][:30]:<30} | "
        elif args.mode in ['asl', 'cafe']:
            header = f"{'FECHA':<12} | {'HORA':<8} | {'CANAL':<20} | {'REMITENTE':<20} | {'MENSAJE'}"
            def get_fmt(r): return f"{r['Fecha']:<12} | {r['Hora']:<8} | {r['Canal'][:20]:<20} | {r.get('Remitente', 'N/A')[:20]:<20} | "
        else: # graficos
            header = f"{'FECHA':<12} | {'HORA':<8} | {'MENSAJE'}"
            def get_fmt(r): return f"{r['Fecha']:<12} | {r['Hora']:<8} | "

        print("\n" + header)
        print("-" * 120)
        for r in results:
            msg_display = r['Mensaje'] if args.full else f"{r['Mensaje'][:80]}..."
            print(get_fmt(r) + msg_display)
        print("-" * 120)
        print(f"Total: {len(results)} resultados mostrados.\n")
    else:
        output_file = args.output or f"resultados_{args.mode}.csv"
        fieldnames = results[0].keys()
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            writer.writerows(results)
        print(f"Finalizado: Se guardaron {len(results)} resultados en {output_file}.")

if __name__ == "__main__":
    process_messages()
