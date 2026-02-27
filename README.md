# WhatsApp Chat Analyzer - ASL Team

Herramienta unificada para la extracción, filtrado y visualización de mensajes exportados de WhatsApp (formato CSV).

## Requisitos

- Python 3.x
- Archivos de chat exportados en formato CSV (`tiempo;remitente;mensaje`) dentro del directorio del proyecto.

## Uso del Script Unificado

El script principal es `show_messages.py`. Permite alternar entre diferentes modos de visualización según el canal o tipo de mensaje.

```bash
python show_messages.py [MODO] [OPCIONES]
```

### Modos Disponibles (`mode`)

- **`alerts`**: Extrae alertas oficiales de trading (Compra/Venta) de los canales de Alertas #ASL.
- **`graficos`**: Muestra los mensajes enviados al canal de Gráficos #ASL.
- **`asl`**: Muestra mensajes de otros canales que contienen "#ASL" (ej. Balanz, etc.), excluyendo Alertas y Café.
- **`cafe`**: Muestra específicamente los mensajes del canal Café Platinum #ASL.
- **`general`**: Muestra todos los mensajes que **no** pertenecen a ningún canal de #ASL (mensajes personales o generales).

### Opciones y Filtros

- `-c`, `--console`: Muestra los resultados directamente en la consola (en lugar de generar un CSV).
- `-f`, `--full`: Muestra el mensaje completo en la consola (sin recortar). Requiere `-c`.
- `-n [N]`, `--last [N]`: Limita la visualización a los últimos **N** resultados encontrados.
- `-t [TICKER]`, `--ticker [TICKER]`: Filtra por activo (ej: AAPL, KO). Disponible en modos `alerts` y `graficos`.
- `-s [SENDER]`, `--sender [SENDER]`: Filtra por el nombre del remitente. Disponible en modo `general`.
- `-o [ARCHIVO]`, `--output [ARCHIVO]`: Define un nombre personalizado para el archivo CSV de salida.

---

## Ejemplos Prácticos

### 1. Ver las últimas 10 alertas de trading por consola
```bash
python show_messages.py alerts -c -n 10
```

### 2. Buscar mensajes sobre un ticker específico en Gráficos
```bash
python show_messages.py graficos -t NVDA -c -f
```

### 3. Ver los últimos 5 mensajes del Café Platinum
```bash
python show_messages.py cafe -c -n 5
```

### 4. Filtrar mensajes generales de una persona específica
```bash
python show_messages.py general -s "Arturo" -c -n 10
```

### 5. Exportar todas las alertas a un archivo personalizado
```bash
python show_messages.py alerts -o mis_alertas.csv
```

## Estructura de Datos
El script realiza una limpieza automática de los mensajes (eliminando saltos de línea para compatibilidad con CSV) y aplica una deduplicación diaria para evitar mensajes repetidos el mismo día en el mismo canal.
