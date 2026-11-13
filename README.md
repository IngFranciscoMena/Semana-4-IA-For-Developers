# Normalización y exploración de transacciones multifuente

Aplicación web desarrollada con Django para cargar transacciones en formato JSON procedentes de distintas fuentes, validar y normalizar sus datos, y explorar los resultados desde una interfaz con indicadores y filtros.

## Funcionalidades principales

- Carga un archivo JSON que contiene una lista de transacciones.
- Reconoce nombres alternativos para identificador (`id`, `transaction_id`, `ref`), monto (`amount`, `total`), moneda (`currency`, `currency_code`), fecha (`timestamp`, `created_at`, `date`) y estado (`status`, `state`, `result`).
- Normaliza los montos a USD. La conversión configurada para EUR utiliza una tasa fija de 1 EUR = 1.05 USD; USD se conserva sin conversión.
- Estandariza estados como `SUCCESS`, `FAILED` y `PENDING`.
- Muestra el total de transacciones procesadas, válidas e inválidas, gráficos por validez y estado, totales por moneda y una tabla con filtros y paginación.
- Las transacciones con datos no reconocidos o inválidos se reportan como inválidas en lugar de normalizarse.

## Requisitos

- Python instalado.
- `pip`, incluido con las instalaciones habituales de Python.

## Crear el ambiente e instalar dependencias

Abre PowerShell en la carpeta raíz del proyecto y ejecuta:

```powershell
python -m venv env
.\env\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Si PowerShell no permite activar el ambiente, puedes abrir una terminal de Command Prompt y ejecutar `env\Scripts\activate.bat`.

## Preparar y levantar el proyecto

Desde la carpeta raíz, entra al directorio de Django, aplica las migraciones y levanta el servidor de desarrollo:

```powershell
cd normalizador
python manage.py migrate
python manage.py runserver
```

Abre [http://127.0.0.1:8000/](http://127.0.0.1:8000/) en el navegador. Para detener el servidor, presiona `Ctrl+C` en la terminal.

## Formato del archivo de entrada

El archivo debe ser JSON válido y su elemento superior debe ser una lista. Por ejemplo:

```json
[
  {
    "transaction_id": "tx-001",
    "amount": "25.50",
    "currency": "USD",
    "created_at": "2025-01-15T10:30:00",
    "status": "completed",
    "source": "tienda-a"
  }
]
```

Cada transacción necesita un identificador, un monto, una fecha y un estado. La moneda puede indicarse como `USD` o `EUR`; si se omite, se infiere únicamente cuando el monto incluye el símbolo `$` o `€`. Los estados reconocidos incluyen `success`, `completed`, `ok`, `failed`, `error`, `fallido`, `rechazado`, `pending` y `pendiente`. Si no se proporciona `source`, se utiliza el nombre del archivo cargado.
