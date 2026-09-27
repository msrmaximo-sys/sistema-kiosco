# Sistema de gestión de kiosco

Aplicación local de inventario y punto de venta (POS) desarrollada en Python y Streamlit. Permite administrar productos, registrar ventas y consultar el rendimiento del negocio desde el navegador. La interfaz utiliza el nombre «Inventario La Esquinita».

## Funcionalidades

- **Inventario:** alta, edición y eliminación de productos, categorías, precios de compra y venta, unidades de medida, reposición y stock mínimo. Búsqueda y filtros por categoría o stock bajo.
- **Proveedores:** registro de empresa, vendedor y datos de contacto; asociación con productos.
- **Ventas:** búsqueda de productos, carrito, cantidades y precios editables, control de stock al confirmar y cálculo de vuelto.
- **Pagos parciales:** registro del cliente y saldo pendiente, filtro de deudas y opción de saldarlas en el historial.
- **Historial:** consulta del detalle de las últimas 100 ventas y eliminación de operaciones con confirmación.
- **Reportes:** importes vendidos, costo de mercadería, margen, unidades vendidas, valoración del inventario y gráficos por fecha, categoría y producto.
- **Herramientas:** alertas de stock, selección de paleta visual y exportación/restauración de copias JSON.

## Tecnologías

| Componente | Uso |
| --- | --- |
| Python | Lógica de la aplicación |
| Streamlit | Interfaz web y navegación entre pantallas |
| SQLite (`sqlite3` de Python) | Persistencia local, sin servidor de base de datos separado |
| pandas | Preparación de tablas y datos para gráficos |
| Plotly | Gráficos interactivos |
| HTML y CSS integrados en Python | Personalización visual de la interfaz |

Las dependencias declaradas están en `requirements.txt`. Se detectó un entorno local con Python 3.14.3, Streamlit 1.60.0, pandas 3.0.5 y Plotly 6.9.0; esto no constituye una matriz de compatibilidad. Las dependencias usan mínimos (`>=`), por lo que una instalación nueva puede resolver otras versiones.

## Instalación y ejecución

Descargá o cloná este repositorio y abrí una terminal en su carpeta raíz. Necesitás Python con `pip` y `venv`.

### Windows (PowerShell o CMD)

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

Si `py` no está disponible, usá `python -m venv .venv`. No hace falta activar el entorno ni modificar la política de ejecución de PowerShell.

Después de instalar las dependencias, también podés abrir **`iniciar.bat`** con doble clic. Usa la carpeta donde está guardado y no contiene rutas personales. Es un script de inicio, no un ejecutable que incluya Python o las dependencias.

### Linux / macOS

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1
```

Abrí la dirección que indique Streamlit, normalmente `http://127.0.0.1:8501`. Para detenerlo, presioná `Ctrl+C` en la terminal. Los comandos anteriores limitan el acceso a la computadora local.

## Datos y comportamiento actual

La aplicación crea `inventario.db` junto a `database.py` cuando no existe. Esa base contiene los datos de trabajo y **no se distribuye en Git**.

`app.py` llama a `seed_demo_data()` en cada ejecución: agrega los proveedores y productos de ejemplo que falten por nombre. Por eso, eliminar o renombrar uno puede hacer que vuelva a aparecer en una ejecución posterior. Para usar exclusivamente un catálogo propio, quitá esa llamada antes de cargar datos reales; esto no elimina los ejemplos ya guardados.

Al registrar una venta, el stock se descuenta dentro de una transacción y se valida su disponibilidad. En el POS, dejar el monto abonado en cero significa **pago exacto**, no una venta totalmente impaga. Los pagos parciales requieren un importe positivo menor al total y un nombre de cliente.

Aunque algunas etiquetas dicen «Resumen del día» y «Ganancia neta», los indicadores del inicio acumulan el historial completo, y la ganancia representa venta menos costo de mercadería: no descuenta gastos operativos ni impuestos. Los ingresos incluyen ventas con saldo pendiente; no equivalen necesariamente al dinero cobrado.

Desde la barra lateral se puede guardar una copia JSON o recuperar una existente. **Recuperar datos reemplaza los datos actuales.** Guardá una copia previa fuera del repositorio. Eliminar ventas o reiniciar estadísticas borra registros, pero **no devuelve unidades al stock**.

La versión actual no incorpora inicio de sesión ni roles de usuario; está orientada al uso local. No incluye integración de facturación fiscal ni una suite automatizada de pruebas en este repositorio.

## Estructura

```text
.
├── app.py                    # Inicio, dashboard, navegación y copias de seguridad
├── database.py               # SQLite, validaciones y operaciones del negocio
├── theme.py                  # Tema visual, HTML/CSS y componentes compartidos
├── pages/
│   ├── inventario.py
│   ├── venta_libre.py
│   ├── historial_ventas.py
│   ├── proveedores.py
│   └── ganancias.py
├── docs/
│   ├── DESARROLLO.md          # Participación humana, IA e historial Git
│   └── PUBLICACION.md        # Preparación del repositorio y privacidad
├── requirements.txt
├── iniciar.bat               # Inicio portable para Windows
├── .gitignore
└── README.md
```

`.venv/`, `inventario.db` y el lanzador personal `AbrirKiosco.bat` permanecen locales y están excluidos. Se conserva una estructura pequeña: las pantallas están separadas de los datos y de la presentación compartida. Si el sistema crece, se puede dividir `database.py` en persistencia y servicios mediante un cambio específico, acompañado de verificaciones.

## Desarrollo y autoría

Este proyecto se construyó de forma incremental, en distintas sesiones, con asistencia de IA en gran parte del código. Mi participación incluyó guiar las decisiones de diseño y funcionalidad, revisar y ajustar el código y realizar cambios manuales, especialmente en el HTML y el frontend. No fue generado de una sola vez: se agregaron y corrigieron funciones a lo largo del proceso.

La documentación distingue ese proceso del historial Git disponible. Ver [desarrollo e historial](docs/DESARROLLO.md) y [publicación sin datos privados](docs/PUBLICACION.md).
