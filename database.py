"""
database.py - Capa de acceso a datos para el sistema de Inventario y Punto de Venta.

Maneja:
 - Conexión y creación de la base de datos SQLite (inventario.db)
 - CRUD de proveedores, productos, ventas y notificaciones
 - Lógica de alertas automáticas de stock bajo
 - Descuento atómico de stock al confirmar una venta
 - Respaldo (backup) y restauración de datos en formato JSON
"""

import sqlite3
import json
import os
import math
import re
import streamlit as st
from datetime import datetime
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventario.db")
SIN_CATEGORIA = "Sin categoría"
MAX_TEXTO = 120
MAX_BUSQUEDA = 100


class StockInsuficienteError(Exception):
    """Se lanza cuando se intenta vender más stock del disponible."""
    pass


def _texto(valor, campo, *, requerido=True, maximo=MAX_TEXTO):
    """Normaliza texto de entrada y evita datos inválidos o excesivos."""
    if not isinstance(valor, str):
        raise ValueError(f"{campo} debe ser texto válido.")
    valor = " ".join(valor.strip().split())
    if requerido and not valor:
        raise ValueError(f"{campo} es obligatorio.")
    if len(valor) > maximo:
        raise ValueError(f"{campo} no puede superar {maximo} caracteres.")
    return valor


def _numero(valor, campo, *, minimo=0):
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        raise ValueError(f"{campo} debe ser un número válido.") from None
    if not math.isfinite(numero) or numero < minimo:
        raise ValueError(f"{campo} debe ser un número finito mayor o igual a {minimo}.")
    return numero


def _id(valor, campo="El identificador"):
    if isinstance(valor, bool):
        raise ValueError(f"{campo} no es válido.")
    try:
        valor = int(valor)
    except (TypeError, ValueError):
        raise ValueError(f"{campo} no es válido.") from None
    if valor <= 0:
        raise ValueError(f"{campo} no es válido.")
    return valor


@contextmanager
def get_connection():
    """Provee una conexión SQLite con foreign keys activas y filas tipo diccionario."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# INICIALIZACIÓN DE LA BASE DE DATOS
# ---------------------------------------------------------------------------

def init_db():
    """Crea todas las tablas necesarias si no existen todavía."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS proveedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_empresa TEXT NOT NULL,
                vendedor TEXT DEFAULT '',
                telefono TEXT DEFAULT '',
                correo TEXT DEFAULT ''
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS categorias (
                nombre TEXT PRIMARY KEY
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                categoria TEXT NOT NULL,
                unidad_medida TEXT NOT NULL,
                proveedor_id INTEGER,
                precio_compra REAL NOT NULL DEFAULT 0,
                precio_venta REAL NOT NULL DEFAULT 0,
                stock_actual REAL NOT NULL DEFAULT 0,
                stock_minimo REAL NOT NULL DEFAULT 0,
                FOREIGN KEY (proveedor_id) REFERENCES proveedores(id) ON DELETE SET NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                total_venta REAL NOT NULL DEFAULT 0,
                ganancia_total REAL NOT NULL DEFAULT 0,
                monto_pagado REAL NOT NULL DEFAULT 0,
                cliente_nombre TEXT DEFAULT '',
                estado_pago TEXT NOT NULL DEFAULT 'Pagado'
            )
        """)
        columnas_ventas = {fila["name"] for fila in cur.execute("PRAGMA table_info(ventas)")}
        migraciones_ventas = {
            "monto_pagado": "ALTER TABLE ventas ADD COLUMN monto_pagado REAL NOT NULL DEFAULT 0",
            "cliente_nombre": "ALTER TABLE ventas ADD COLUMN cliente_nombre TEXT DEFAULT ''",
            "estado_pago": "ALTER TABLE ventas ADD COLUMN estado_pago TEXT NOT NULL DEFAULT 'Pagado'",
        }
        for columna, sentencia in migraciones_ventas.items():
            if columna not in columnas_ventas:
                cur.execute(sentencia)
        cur.execute("UPDATE ventas SET monto_pagado = total_venta WHERE monto_pagado = 0 AND estado_pago = 'Pagado'")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_productos_nombre ON productos(nombre)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_productos_categoria ON productos(categoria)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha)")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS detalle_ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venta_id INTEGER NOT NULL,
                producto_id INTEGER,
                producto_nombre TEXT NOT NULL,
                categoria TEXT NOT NULL DEFAULT 'Sin categoría',
                cantidad REAL NOT NULL,
                precio_unitario REAL NOT NULL,
                costo_unitario REAL NOT NULL,
                subtotal REAL NOT NULL,
                ganancia_subtotal REAL NOT NULL,
                FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE CASCADE,
                FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE SET NULL
            )
        """)
        columnas_detalle = {fila["name"] for fila in cur.execute("PRAGMA table_info(detalle_ventas)")}
        if "categoria" not in columnas_detalle:
            cur.execute("ALTER TABLE detalle_ventas ADD COLUMN categoria TEXT NOT NULL DEFAULT 'Sin categoría'")
        cur.execute("UPDATE detalle_ventas SET categoria = ? WHERE categoria IS NULL OR TRIM(categoria) = ''", (SIN_CATEGORIA,))
        cur.execute("""
            CREATE TABLE IF NOT EXISTS notificaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id INTEGER,
                mensaje TEXT NOT NULL,
                fecha TEXT NOT NULL,
                leida INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE
            )
        """)
        conn.commit()
    _sync_categorias_desde_productos()


def _sync_categorias_desde_productos():
    """Migra categorías existentes en productos hacia la tabla unificada de categorías."""
    with get_connection() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO categorias (nombre)
            SELECT DISTINCT categoria FROM productos WHERE TRIM(categoria) <> ''
        """)
    get_categorias.clear()


def seed_demo_data():
    """Carga datos de ejemplo una sola vez, sin duplicar los que ya existan."""
    proveedores = [
        ("Distribuidora Central", "Sofía", "11 4000-1001", "ventas@central.test"),
        ("Mayorista del Barrio", "Martín", "11 4000-1002", "pedidos@barrio.test"),
        ("Alimentos Frescos", "Laura", "11 4000-1003", "ventas@frescos.test"),
        ("Higiene Hogar", "Diego", "11 4000-1004", "contacto@higiene.test"),
        ("Lácteos del Día", "Carla", "11 4000-1005", "pedidos@lacteos.test"),
    ]
    productos = [
        # nombre, categoría, unidad, proveedor, compra, venta, stock, mínimo
        ("Lavandina 1 L", "Limpieza", "botella", "Higiene Hogar", 850, 1250, 24, 5),
        ("Detergente limón", "Limpieza", "botella", "Higiene Hogar", 1100, 1650, 18, 4),
        ("Esponja multiuso", "Limpieza", "unidad", "Higiene Hogar", 420, 650, 30, 6),
        ("Desinfectante floral", "Limpieza", "botella", "Higiene Hogar", 1250, 1850, 15, 4),
        ("Jabón para ropa", "Limpieza", "botella", "Higiene Hogar", 2100, 3100, 12, 3),
        ("Agua mineral 1,5 L", "Bebidas", "botella", "Distribuidora Central", 700, 1100, 36, 8),
        ("Gaseosa cola 2,25 L", "Bebidas", "botella", "Distribuidora Central", 1550, 2300, 28, 6),
        ("Jugo de naranja", "Bebidas", "caja", "Distribuidora Central", 900, 1400, 20, 5),
        ("Cerveza rubia lata", "Bebidas", "lata", "Mayorista del Barrio", 1050, 1650, 24, 6),
        ("Té frío limón", "Bebidas", "botella", "Mayorista del Barrio", 850, 1300, 16, 4),
        ("Arroz largo fino 1 kg", "Comida", "paquete", "Mayorista del Barrio", 1150, 1750, 25, 5),
        ("Fideos tirabuzón 500 g", "Comida", "paquete", "Mayorista del Barrio", 720, 1150, 32, 7),
        ("Aceite de girasol 900 ml", "Comida", "botella", "Alimentos Frescos", 1650, 2500, 18, 4),
        ("Salsa de tomate", "Comida", "caja", "Alimentos Frescos", 620, 980, 26, 6),
        ("Galletitas surtidas", "Comida", "paquete", "Alimentos Frescos", 950, 1450, 22, 5),
        ("Papel higiénico x4", "Higiene", "paquete", "Higiene Hogar", 1650, 2450, 18, 4),
        ("Jabón de tocador", "Higiene", "unidad", "Higiene Hogar", 580, 900, 28, 6),
        ("Shampoo familiar", "Higiene", "botella", "Higiene Hogar", 2200, 3300, 14, 3),
        ("Pasta dental", "Higiene", "unidad", "Higiene Hogar", 980, 1500, 20, 5),
        ("Toallitas femeninas", "Higiene", "paquete", "Higiene Hogar", 1800, 2700, 16, 4),
        ("Leche entera 1 L", "Lacteos", "caja", "Lácteos del Día", 900, 1350, 30, 7),
        ("Yogur firme frutilla", "Lacteos", "unidad", "Lácteos del Día", 620, 950, 24, 5),
        ("Queso cremoso 500 g", "Lacteos", "paquete", "Lácteos del Día", 2800, 4200, 10, 2),
        ("Manteca 200 g", "Lacteos", "unidad", "Lácteos del Día", 1450, 2200, 14, 3),
        ("Postre de vainilla", "Lacteos", "unidad", "Lácteos del Día", 550, 850, 20, 5),
    ]

    with get_connection() as conn:
        for nombre, vendedor, telefono, correo in proveedores:
            existe = conn.execute("SELECT id FROM proveedores WHERE nombre_empresa = ?", (nombre,)).fetchone()
            if not existe:
                conn.execute(
                    "INSERT INTO proveedores (nombre_empresa, vendedor, telefono, correo) VALUES (?, ?, ?, ?)",
                    (nombre, vendedor, telefono, correo),
                )

        proveedores_ids = {
            row["nombre_empresa"]: row["id"]
            for row in conn.execute("SELECT id, nombre_empresa FROM proveedores").fetchall()
        }
        for nombre, categoria, unidad, proveedor, compra, venta, stock, minimo in productos:
            existe = conn.execute("SELECT id FROM productos WHERE nombre = ?", (nombre,)).fetchone()
            if not existe:
                conn.execute(
                    """INSERT INTO productos
                    (nombre, categoria, unidad_medida, proveedor_id, precio_compra, precio_venta, stock_actual, stock_minimo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (nombre, categoria, unidad, proveedores_ids[proveedor], compra, venta, stock, minimo),
                )
    _sync_categorias_desde_productos()


# ---------------------------------------------------------------------------
# CATEGORÍAS
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def get_categorias():
    """Devuelve todas las categorías registradas, ordenadas alfabéticamente."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT nombre FROM categorias
            UNION
            SELECT ? WHERE EXISTS (SELECT 1 FROM productos WHERE categoria = ?)
            ORDER BY nombre ASC
            """, (SIN_CATEGORIA, SIN_CATEGORIA)
        ).fetchall()
        return [r["nombre"] for r in rows]


def get_categorias_con_conteo():
    """Devuelve categorías con cantidad de productos asociados."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT c.nombre,
                   COUNT(p.id) AS total_productos
            FROM categorias c
            LEFT JOIN productos p ON p.categoria = c.nombre
            GROUP BY c.nombre
            ORDER BY c.nombre ASC
        """).fetchall()
        return [dict(r) for r in rows]


def add_categoria(nombre):
    """Registra una categoría nueva si no existe ya."""
    nombre = _texto(nombre, "El nombre de la categoría")
    if nombre.casefold() == SIN_CATEGORIA.casefold():
        raise ValueError(f"'{SIN_CATEGORIA}' está reservada para productos sin categoría.")

    with get_connection() as conn:
        existe = conn.execute(
            "SELECT nombre FROM categorias WHERE LOWER(nombre) = LOWER(?)", (nombre,)
        ).fetchone()
        if existe:
            raise ValueError(f"La categoría '{nombre}' ya existe.")

        conn.execute("INSERT INTO categorias (nombre) VALUES (?)", (nombre,))
    get_categorias.clear()
    return nombre


def _ensure_categoria(nombre):
    """Garantiza que la categoría exista en el catálogo (uso interno al guardar productos)."""
    nombre = _texto(nombre, "La categoría")
    if nombre == SIN_CATEGORIA:
        return nombre
    with get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO categorias (nombre) VALUES (?)", (nombre,))
    get_categorias.clear()
    return nombre


def update_categoria(nombre_anterior, nombre_nuevo):
    """Renombra una categoría y actualiza todos los productos vinculados."""
    nombre_anterior = _texto(nombre_anterior, "La categoría actual")
    nombre_nuevo = _texto(nombre_nuevo, "El nombre nuevo")
    if nombre_anterior == SIN_CATEGORIA or nombre_nuevo == SIN_CATEGORIA:
        raise ValueError(f"'{SIN_CATEGORIA}' no puede gestionarse como una categoría normal.")
    if nombre_anterior.lower() == nombre_nuevo.lower():
        return nombre_nuevo

    with get_connection() as conn:
        actual = conn.execute(
            "SELECT nombre FROM categorias WHERE nombre = ?", (nombre_anterior,)
        ).fetchone()
        if not actual:
            raise ValueError(f"La categoría '{nombre_anterior}' no existe.")

        duplicada = conn.execute(
            "SELECT nombre FROM categorias WHERE LOWER(nombre) = LOWER(?) AND nombre <> ?",
            (nombre_nuevo, nombre_anterior),
        ).fetchone()
        if duplicada:
            raise ValueError(f"Ya existe otra categoría llamada '{nombre_nuevo}'.")

        conn.execute("UPDATE categorias SET nombre = ? WHERE nombre = ?", (nombre_nuevo, nombre_anterior))
        conn.execute(
            "UPDATE productos SET categoria = ? WHERE categoria = ?",
            (nombre_nuevo, nombre_anterior),
        )
    get_categorias.clear()
    return nombre_nuevo


def delete_categoria(nombre):
    """Elimina una categoría y conserva sus productos como 'Sin categoría'."""
    nombre = _texto(nombre, "La categoría")
    if nombre == SIN_CATEGORIA:
        raise ValueError(f"'{SIN_CATEGORIA}' no puede eliminarse.")
    with get_connection() as conn:
        if not conn.execute("SELECT 1 FROM categorias WHERE nombre = ?", (nombre,)).fetchone():
            raise ValueError("La categoría ya no existe.")
        conn.execute("UPDATE productos SET categoria = ? WHERE categoria = ?", (SIN_CATEGORIA, nombre))
        conn.execute("DELETE FROM categorias WHERE nombre = ?", (nombre,))
    get_categorias.clear()


# ---------------------------------------------------------------------------
# PROVEEDORES
# ---------------------------------------------------------------------------

def add_proveedor(nombre_empresa, vendedor="", telefono="", correo=""):
    nombre_empresa = _texto(nombre_empresa, "El nombre de la empresa")
    vendedor = _texto(vendedor, "El nombre del vendedor", requerido=False)
    telefono = _texto(telefono, "El teléfono", requerido=False, maximo=40)
    correo = _texto(correo, "El correo", requerido=False, maximo=254)
    if correo and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", correo):
        raise ValueError("El correo no tiene un formato válido.")
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO proveedores (nombre_empresa, vendedor, telefono, correo) "
            "VALUES (?, ?, ?, ?)",
            (nombre_empresa, vendedor, telefono, correo),
        )
        return cur.lastrowid


def get_proveedores():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM proveedores ORDER BY nombre_empresa ASC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_proveedor(proveedor_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM proveedores WHERE id = ?", (proveedor_id,)
        ).fetchone()
        return dict(row) if row else None


def update_proveedor(proveedor_id, nombre_empresa, vendedor="", telefono="", correo=""):
    proveedor_id = _id(proveedor_id, "El proveedor")
    nombre_empresa = _texto(nombre_empresa, "El nombre de la empresa")
    vendedor = _texto(vendedor, "El nombre del vendedor", requerido=False)
    telefono = _texto(telefono, "El teléfono", requerido=False, maximo=40)
    correo = _texto(correo, "El correo", requerido=False, maximo=254)
    if correo and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", correo):
        raise ValueError("El correo no tiene un formato válido.")
    with get_connection() as conn:
        conn.execute(
            "UPDATE proveedores SET nombre_empresa=?, vendedor=?, telefono=?, correo=? "
            "WHERE id=?",
            (nombre_empresa, vendedor, telefono, correo, proveedor_id),
        )


def delete_proveedor(proveedor_id):
    proveedor_id = _id(proveedor_id, "El proveedor")
    with get_connection() as conn:
        # Los productos asociados quedan con proveedor_id = NULL (ON DELETE SET NULL)
        conn.execute("DELETE FROM proveedores WHERE id = ?", (proveedor_id,))


def get_productos_por_proveedor(proveedor_id):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM productos WHERE proveedor_id = ? ORDER BY nombre ASC",
            (proveedor_id,),
        ).fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# PRODUCTOS
# ---------------------------------------------------------------------------

def add_producto(nombre, categoria, unidad_medida, proveedor_id,
                  precio_compra, precio_venta, stock_actual, stock_minimo):
    nombre = _texto(nombre, "El nombre del producto")
    unidad_medida = _texto(unidad_medida, "La unidad de medida", maximo=40)
    precio_compra = _numero(precio_compra, "El precio de compra")
    precio_venta = _numero(precio_venta, "El precio de venta")
    stock_actual = _numero(stock_actual, "El stock actual")
    stock_minimo = _numero(stock_minimo, "El stock mínimo")
    if proveedor_id is not None:
        proveedor_id = _id(proveedor_id, "El proveedor")
    categoria = _ensure_categoria(categoria)
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO productos
               (nombre, categoria, unidad_medida, proveedor_id, precio_compra,
                precio_venta, stock_actual, stock_minimo)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (nombre, categoria, unidad_medida, proveedor_id, precio_compra, precio_venta,
             stock_actual, stock_minimo),
        )
        producto_id = cur.lastrowid
    check_stock_notification(producto_id)
    return producto_id


def update_producto(producto_id, nombre, categoria, unidad_medida, proveedor_id,
                     precio_compra, precio_venta, stock_actual, stock_minimo):
    producto_id = _id(producto_id, "El producto")
    nombre = _texto(nombre, "El nombre del producto")
    unidad_medida = _texto(unidad_medida, "La unidad de medida", maximo=40)
    precio_compra = _numero(precio_compra, "El precio de compra")
    precio_venta = _numero(precio_venta, "El precio de venta")
    stock_actual = _numero(stock_actual, "El stock actual")
    stock_minimo = _numero(stock_minimo, "El stock mínimo")
    if proveedor_id is not None:
        proveedor_id = _id(proveedor_id, "El proveedor")
    categoria = _ensure_categoria(categoria)
    with get_connection() as conn:
        conn.execute(
            """UPDATE productos SET nombre=?, categoria=?, unidad_medida=?, proveedor_id=?,
               precio_compra=?, precio_venta=?, stock_actual=?, stock_minimo=?
               WHERE id=?""",
            (nombre, categoria, unidad_medida, proveedor_id, precio_compra,
             precio_venta, stock_actual, stock_minimo, producto_id),
        )
    check_stock_notification(producto_id)


def delete_producto(producto_id):
    producto_id = _id(producto_id, "El producto")
    with get_connection() as conn:
        conn.execute("DELETE FROM productos WHERE id = ?", (producto_id,))


def get_producto(producto_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM productos WHERE id = ?", (producto_id,)
        ).fetchone()
        return dict(row) if row else None


def get_producto_por_nombre(texto):
    """Busca un producto por nombre exacto (sin distinguir mayúsculas)."""
    texto = _texto(texto, "La búsqueda", maximo=MAX_BUSQUEDA)
    if texto.isdigit():
        raise ValueError("La búsqueda debe contener texto; no se aceptan códigos numéricos.")
    if not texto:
        return None

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT p.*, COALESCE(pr.nombre_empresa, 'Sin proveedor') AS proveedor_nombre
            FROM productos p
            LEFT JOIN proveedores pr ON p.proveedor_id = pr.id
            WHERE LOWER(p.nombre) = LOWER(?)
            """,
            (texto,),
        ).fetchone()
        return dict(row) if row else None


def incrementar_stock(producto_id, cantidad):
    """Suma cantidad al stock_actual de un producto y revisa alertas."""
    producto_id = _id(producto_id, "El producto")
    cantidad = _numero(cantidad, "La cantidad")
    if cantidad == 0:
        raise ValueError("La cantidad debe ser mayor a cero.")

    with get_connection() as conn:
        existe = conn.execute("SELECT id FROM productos WHERE id = ?", (producto_id,)).fetchone()
        if not existe:
            raise ValueError("El producto no existe.")

        conn.execute(
            "UPDATE productos SET stock_actual = stock_actual + ? WHERE id = ?",
            (cantidad, producto_id),
        )

    check_stock_notification(producto_id)


def get_productos(search="", categoria="Todas", solo_bajo_stock=False):
    """Devuelve productos con nombre de proveedor incluido, con filtros opcionales."""
    query = """
        SELECT p.*, COALESCE(pr.nombre_empresa, 'Sin proveedor') AS proveedor_nombre
        FROM productos p
        LEFT JOIN proveedores pr ON p.proveedor_id = pr.id
        WHERE 1=1
    """
    params = []
    if search:
        search = _texto(search, "La búsqueda", maximo=MAX_BUSQUEDA)
        query += " AND LOWER(p.nombre) LIKE ?"
        params.append(f"%{search.lower()}%")
    if categoria and categoria != "Todas":
        query += " AND p.categoria = ?"
        params.append(categoria)
    if solo_bajo_stock:
        query += " AND p.stock_actual <= p.stock_minimo"
    query += " ORDER BY p.nombre ASC"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# NOTIFICACIONES / ALERTAS DE STOCK BAJO
# ---------------------------------------------------------------------------

def check_stock_notification(producto_id):
    """
    Lógica de 'trigger': revisa si un producto quedó en stock_actual <= stock_minimo.
    Si es así, y no existe ya una notificación no leída para ese producto,
    inserta una nueva notificación automáticamente.
    Se debe invocar después de cualquier operación que modifique el stock.
    """
    with get_connection() as conn:
        producto = conn.execute(
            "SELECT * FROM productos WHERE id = ?", (producto_id,)
        ).fetchone()
        if not producto:
            return

        if producto["stock_actual"] <= producto["stock_minimo"]:
            existe = conn.execute(
                "SELECT id FROM notificaciones WHERE producto_id = ? AND leida = 0",
                (producto_id,),
            ).fetchone()
            if not existe:
                mensaje = (
                    f"Stock bajo: '{producto['nombre']}' tiene "
                    f"{producto['stock_actual']:g} {producto['unidad_medida']} "
                    f"(mínimo: {producto['stock_minimo']:g})."
                )
                conn.execute(
                    "INSERT INTO notificaciones (producto_id, mensaje, fecha, leida) "
                    "VALUES (?, ?, ?, 0)",
                    (producto_id, mensaje, datetime.now().isoformat(timespec="seconds")),
                )
        else:
            # El stock se recuperó: limpiar notificaciones no leídas de ese producto
            conn.execute(
                "DELETE FROM notificaciones WHERE producto_id = ? AND leida = 0",
                (producto_id,),
            )


def get_notificaciones(solo_no_leidas=True):
    with get_connection() as conn:
        if solo_no_leidas:
            rows = conn.execute(
                "SELECT * FROM notificaciones WHERE leida = 0 ORDER BY fecha DESC"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM notificaciones ORDER BY fecha DESC"
            ).fetchall()
        return [dict(r) for r in rows]


def marcar_notificacion_leida(notificacion_id):
    with get_connection() as conn:
        conn.execute(
            "UPDATE notificaciones SET leida = 1 WHERE id = ?", (notificacion_id,)
        )


def limpiar_notificaciones():
    """Elimina TODAS las notificaciones (borrado total, según lo solicitado)."""
    with get_connection() as conn:
        conn.execute("DELETE FROM notificaciones")


# ---------------------------------------------------------------------------
# VENTAS (PUNTO DE VENTA)
# ---------------------------------------------------------------------------

def confirmar_venta(carrito, monto_pagado=None, cliente_nombre=""):
    """
    Confirma una venta de forma atómica.

    carrito: lista de dicts con:
        {
            "producto_id": int,
            "nombre": str,
            "cantidad": float,
            "precio_unitario": float,   # precio de venta (puede ser editado/con descuento)
            "costo_unitario": float,    # precio de compra registrado del producto
        }

    Verifica stock disponible para TODOS los ítems antes de confirmar.
    Si algún ítem no tiene stock suficiente, lanza StockInsuficienteError
    y no se realiza ningún cambio en la base de datos.

    monto_pagado es opcional: si no se indica, se registra el total como pago exacto.
    Cuando el pago es parcial, cliente_nombre es obligatorio. Retorna el id de la venta creada.
    """
    if not isinstance(carrito, list) or not carrito:
        raise ValueError("El carrito está vacío.")
    if len(carrito) > 100:
        raise ValueError("La venta supera el máximo de 100 artículos distintos.")
    if monto_pagado is not None:
        monto_pagado = _numero(monto_pagado, "El monto abonado")
    cliente_nombre = _texto(cliente_nombre, "El nombre del cliente", requerido=False)

    items, ids = [], set()
    for item in carrito:
        if not isinstance(item, dict):
            raise ValueError("El carrito contiene un artículo inválido.")
        producto_id = _id(item.get("producto_id"), "El producto")
        if producto_id in ids:
            raise ValueError("Un producto no puede repetirse en la misma venta.")
        ids.add(producto_id)
        cantidad = _numero(item.get("cantidad"), "La cantidad")
        if cantidad == 0:
            raise ValueError("La cantidad debe ser mayor a cero.")
        items.append({
            "producto_id": producto_id,
            "cantidad": cantidad,
            "precio_unitario": _numero(item.get("precio_unitario"), "El precio unitario"),
        })

    with get_connection() as conn:
        cur = conn.cursor()

        # 1) Validar stock disponible de todos los productos antes de tocar nada
        for item in items:
            row = cur.execute(
                "SELECT stock_actual, nombre, precio_compra, categoria FROM productos WHERE id = ?",
                (item["producto_id"],),
            ).fetchone()
            if row is None:
                raise StockInsuficienteError(
                    "Uno de los productos ya no existe en el inventario."
                )
            if row["stock_actual"] < item["cantidad"]:
                raise StockInsuficienteError(
                    f"Stock insuficiente para '{row['nombre']}'. "
                    f"Disponible: {row['stock_actual']:g}, solicitado: {item['cantidad']:g}."
                )

        # 2) Calcular totales
        for item in items:
            producto = cur.execute(
                "SELECT nombre, precio_compra, categoria FROM productos WHERE id = ?",
                (item["producto_id"],),
            ).fetchone()
            item.update(
                nombre=producto["nombre"],
                costo_unitario=float(producto["precio_compra"]),
                categoria=producto["categoria"] or SIN_CATEGORIA,
            )
        total_venta = sum(i["cantidad"] * i["precio_unitario"] for i in items)
        ganancia_total = sum(i["cantidad"] * (i["precio_unitario"] - i["costo_unitario"]) for i in items)
        # El monto guardado representa lo efectivamente cobrado por esta venta, nunca el vuelto.
        monto_registrado = total_venta if monto_pagado is None else min(monto_pagado, total_venta)
        estado_pago = "Pagado" if monto_registrado >= total_venta else "Debe"
        if estado_pago == "Debe" and not cliente_nombre:
            raise ValueError("El nombre del cliente es obligatorio para registrar una deuda.")
        fecha = datetime.now().isoformat(timespec="seconds")

        # 3) Insertar venta
        cur.execute(
            """INSERT INTO ventas
               (fecha, total_venta, ganancia_total, monto_pagado, cliente_nombre, estado_pago)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (fecha, total_venta, ganancia_total, monto_registrado, cliente_nombre, estado_pago),
        )
        venta_id = cur.lastrowid

        # 4) Insertar detalle y descontar stock atómicamente
        for item in items:
            subtotal = item["cantidad"] * item["precio_unitario"]
            ganancia_subtotal = item["cantidad"] * (item["precio_unitario"] - item["costo_unitario"])
            cur.execute(
                """INSERT INTO detalle_ventas
                   (venta_id, producto_id, producto_nombre, categoria, cantidad, precio_unitario,
                    costo_unitario, subtotal, ganancia_subtotal)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (venta_id, item["producto_id"], item["nombre"], item["categoria"], item["cantidad"],
                 item["precio_unitario"], item["costo_unitario"], subtotal, ganancia_subtotal),
            )
            cur.execute(
                """UPDATE productos SET stock_actual = stock_actual - ?
                   WHERE id = ? AND stock_actual >= ?""",
                (item["cantidad"], item["producto_id"], item["cantidad"]),
            )
            if cur.rowcount != 1:
                raise StockInsuficienteError("El stock cambió mientras se procesaba la venta. Intentá nuevamente.")

        conn.commit()

    # 5) Revisar alertas de stock bajo para cada producto vendido (fuera de la transacción)
    for item in items:
        check_stock_notification(item["producto_id"])

    return venta_id


def get_ventas():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM ventas ORDER BY fecha DESC").fetchall()
        return [dict(r) for r in rows]


def get_historial_ventas(limite=100, solo_pendientes=False):
    """Devuelve ventas con sus renglones para auditoría operativa."""
    limite = _id(limite, "El límite")
    limite = min(limite, 500)
    if not isinstance(solo_pendientes, bool):
        raise ValueError("El filtro de pendientes no es válido.")
    with get_connection() as conn:
        consulta = "SELECT * FROM ventas"
        if solo_pendientes:
            consulta += " WHERE estado_pago = 'Debe'"
        ventas = conn.execute(consulta + " ORDER BY fecha DESC, id DESC LIMIT ?", (limite,)).fetchall()
        resultado = []
        for venta in ventas:
            detalle = conn.execute(
                "SELECT producto_nombre, categoria, cantidad, precio_unitario, subtotal "
                "FROM detalle_ventas WHERE venta_id = ? ORDER BY id ASC",
                (venta["id"],),
            ).fetchall()
            registro = dict(venta)
            registro["detalle"] = [dict(item) for item in detalle]
            resultado.append(registro)
        return resultado


def delete_venta(venta_id):
    """Elimina una operación del historial sin modificar el stock actual."""
    venta_id = _id(venta_id, "La venta")
    with get_connection() as conn:
        resultado = conn.execute("DELETE FROM ventas WHERE id = ?", (venta_id,))
        if resultado.rowcount != 1:
            raise ValueError("La venta ya no existe.")


def limpiar_historial_ventas():
    """Elimina ventas, detalles y reinicia sus contadores AUTOINCREMENT."""
    with get_connection() as conn:
        # Se borran explícitamente ambas tablas y sus secuencias para que la próxima venta sea #1.
        conn.execute("DELETE FROM detalle_ventas")
        conn.execute("DELETE FROM ventas")
        conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('ventas', 'detalle_ventas')")


def saldar_deuda(venta_id):
    """Marca como pagada una venta pendiente y registra el total como monto cobrado."""
    venta_id = _id(venta_id, "La venta")
    with get_connection() as conn:
        resultado = conn.execute(
            """UPDATE ventas SET monto_pagado = total_venta, estado_pago = 'Pagado'
               WHERE id = ? AND estado_pago = 'Debe'""",
            (venta_id,),
        )
        if resultado.rowcount != 1:
            raise ValueError("La deuda no existe o ya fue saldada.")


def get_detalle_venta(venta_id):
    venta_id = _id(venta_id, "La venta")
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM detalle_ventas WHERE venta_id = ?", (venta_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_todos_los_detalles():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT dv.*, v.fecha AS fecha_venta
            FROM detalle_ventas dv
            JOIN ventas v ON dv.venta_id = v.id
        """).fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# REPORTES / KPIs
# ---------------------------------------------------------------------------

def get_kpis_dashboard():
    with get_connection() as conn:
        ingresos = conn.execute(
            "SELECT COALESCE(SUM(total_venta), 0) AS v FROM ventas"
        ).fetchone()["v"]
        ganancia = conn.execute(
            "SELECT COALESCE(SUM(ganancia_total), 0) AS v FROM ventas"
        ).fetchone()["v"]
        unidades = conn.execute(
            "SELECT COALESCE(SUM(cantidad), 0) AS v FROM detalle_ventas"
        ).fetchone()["v"]
        productos = conn.execute("SELECT precio_compra, precio_venta, stock_actual FROM productos").fetchall()
        valor_costo = sum(p["precio_compra"] * p["stock_actual"] for p in productos)
        valor_venta = sum(p["precio_venta"] * p["stock_actual"] for p in productos)

        return {
            "ingresos_totales": ingresos,
            "ganancia_neta": ganancia,
            "unidades_vendidas": unidades,
            "valor_inventario_costo": valor_costo,
            "valor_inventario_venta": valor_venta,
        }


def get_ingresos_ganancias_por_fecha():
    """Agrupa ingresos y ganancias por día para el gráfico temporal."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT substr(fecha, 1, 10) AS dia,
                   SUM(total_venta) AS ingresos,
                   SUM(ganancia_total) AS ganancia
            FROM ventas
            GROUP BY dia
            ORDER BY dia ASC
        """).fetchall()
        return [dict(r) for r in rows]


def get_ventas_por_categoria():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT COALESCE(NULLIF(dv.categoria, ''), ?) AS categoria, SUM(dv.subtotal) AS total
            FROM detalle_ventas dv
            GROUP BY COALESCE(NULLIF(dv.categoria, ''), ?)
            ORDER BY total DESC
        """, (SIN_CATEGORIA, SIN_CATEGORIA)).fetchall()
        return [dict(r) for r in rows]


def _filtro_detalle_ventas(categoria=None, producto=None):
    """Construye filtros parametrizados reutilizables para reportes."""
    condiciones, parametros = [], []
    if categoria and categoria != "Todas":
        condiciones.append("COALESCE(NULLIF(dv.categoria, ''), ?) = ?")
        parametros.extend([SIN_CATEGORIA, categoria])
    if producto and producto != "Todos":
        condiciones.append("dv.producto_nombre = ?")
        parametros.append(producto)
    return (" WHERE " + " AND ".join(condiciones)) if condiciones else "", parametros


def get_categorias_vendidas():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT COALESCE(NULLIF(categoria, ''), ?) AS categoria "
            "FROM detalle_ventas ORDER BY categoria", (SIN_CATEGORIA,)
        ).fetchall()
        return [fila["categoria"] for fila in rows]


def get_productos_vendidos(categoria=None):
    filtro, parametros = _filtro_detalle_ventas(categoria=categoria)
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT dv.producto_nombre FROM detalle_ventas dv" + filtro + " ORDER BY dv.producto_nombre",
            parametros,
        ).fetchall()
        return [fila["producto_nombre"] for fila in rows]


def get_kpis_ganancias(categoria=None, producto=None):
    filtro, parametros = _filtro_detalle_ventas(categoria, producto)
    with get_connection() as conn:
        resumen = conn.execute(
            "SELECT COALESCE(SUM(dv.subtotal), 0) AS ingresos, "
            "COALESCE(SUM(dv.ganancia_subtotal), 0) AS ganancia, "
            "COALESCE(SUM(dv.costo_unitario * dv.cantidad), 0) AS cogs "
            "FROM detalle_ventas dv" + filtro,
            parametros,
        ).fetchone()
        estrella = conn.execute(
            "SELECT dv.producto_nombre, SUM(dv.cantidad) AS total_unidades FROM detalle_ventas dv" + filtro +
            " GROUP BY dv.producto_nombre ORDER BY total_unidades DESC LIMIT 1",
            parametros,
        ).fetchone()

        return {
            "ingresos_totales": resumen["ingresos"],
            "cogs": resumen["cogs"],
            "ganancia_neta": resumen["ganancia"],
            "producto_estrella": estrella["producto_nombre"] if estrella else "N/A",
            "producto_estrella_unidades": estrella["total_unidades"] if estrella else 0,
        }


def get_rendimiento_productos(categoria=None, producto=None):
    filtro, parametros = _filtro_detalle_ventas(categoria, producto)
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT dv.producto_nombre, SUM(dv.cantidad) AS unidades_vendidas, "
            "SUM(dv.subtotal) AS ingresos, SUM(dv.ganancia_subtotal) AS ganancia_total "
            "FROM detalle_ventas dv" + filtro +
            " GROUP BY dv.producto_nombre ORDER BY ganancia_total DESC",
            parametros,
        ).fetchall()
        return [dict(r) for r in rows]


def get_ganancia_por_categoria(categoria=None, producto=None):
    filtro, parametros = _filtro_detalle_ventas(categoria=categoria, producto=producto)
    with get_connection() as conn:
        # El primer parámetro del COALESCE pertenece al SELECT; el filtro es parametrizado.
        rows = conn.execute(
            "SELECT COALESCE(NULLIF(dv.categoria, ''), ?) AS categoria, SUM(dv.ganancia_subtotal) AS ganancia "
            "FROM detalle_ventas dv" + filtro +
            " GROUP BY COALESCE(NULLIF(dv.categoria, ''), ?) ORDER BY ganancia DESC",
            [SIN_CATEGORIA, *parametros, SIN_CATEGORIA],
        ).fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# BACKUP / RESTAURACIÓN
# ---------------------------------------------------------------------------

def export_backup():
    """Devuelve un string JSON con el contenido completo de todas las tablas."""
    with get_connection() as conn:
        data = {}
        for tabla in ["categorias", "proveedores", "productos", "ventas", "detalle_ventas", "notificaciones"]:
            rows = conn.execute(f"SELECT * FROM {tabla}").fetchall()
            data[tabla] = [dict(r) for r in rows]
        data["_exportado_en"] = datetime.now().isoformat(timespec="seconds")
        return json.dumps(data, ensure_ascii=False, indent=2)


def import_backup(json_str):
    """
    Restaura la base de datos completa a partir de un JSON generado por export_backup().
    ADVERTENCIA: reemplaza todos los datos actuales.
    """
    if not isinstance(json_str, str) or len(json_str.encode("utf-8")) > 10 * 1024 * 1024:
        raise ValueError("La copia de seguridad no es válida o supera el tamaño permitido.")
    try:
        data = json.loads(json_str)
    except (TypeError, json.JSONDecodeError) as error:
        raise ValueError("El archivo no contiene una copia de seguridad JSON válida.") from error
    if not isinstance(data, dict):
        raise ValueError("El formato de la copia de seguridad no es válido.")
    # Compatibilidad con copias previas al registro de pagos: eran ventas ya cobradas.
    if isinstance(data.get("ventas"), list):
        for venta in data["ventas"]:
            if isinstance(venta, dict) and "monto_pagado" not in venta:
                venta["monto_pagado"] = venta.get("total_venta", 0)
                venta["cliente_nombre"] = ""
                venta["estado_pago"] = "Pagado"
    esquema = {
        "categorias": {"nombre"},
        "proveedores": {"id", "nombre_empresa", "vendedor", "telefono", "correo"},
        "productos": {"id", "nombre", "categoria", "unidad_medida", "proveedor_id", "precio_compra", "precio_venta", "stock_actual", "stock_minimo"},
        "ventas": {"id", "fecha", "total_venta", "ganancia_total", "monto_pagado", "cliente_nombre", "estado_pago"},
        "detalle_ventas": {"id", "venta_id", "producto_id", "producto_nombre", "categoria", "cantidad", "precio_unitario", "costo_unitario", "subtotal", "ganancia_subtotal"},
        "notificaciones": {"id", "producto_id", "mensaje", "fecha", "leida"},
    }
    for tabla, columnas_permitidas in esquema.items():
        registros = data.get(tabla, [])
        if not isinstance(registros, list) or len(registros) > 100_000:
            raise ValueError(f"La tabla '{tabla}' tiene un formato o tamaño inválido.")
        for registro in registros:
            if not isinstance(registro, dict) or set(registro) != columnas_permitidas:
                raise ValueError(f"La estructura de '{tabla}' no coincide con una copia válida.")
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys = OFF")

        for tabla in ["detalle_ventas", "ventas", "notificaciones", "productos", "categorias", "proveedores"]:
            cur.execute(f"DELETE FROM {tabla}")

        for tabla in ["categorias", "proveedores", "productos", "ventas", "detalle_ventas", "notificaciones"]:
            registros = data.get(tabla, [])
            for reg in registros:
                columnas = ", ".join(reg.keys())
                placeholders = ", ".join(["?"] * len(reg))
                valores = list(reg.values())
                cur.execute(
                    f"INSERT INTO {tabla} ({columnas}) VALUES ({placeholders})", valores
                )

        cur.execute("PRAGMA foreign_keys = ON")
        conn.commit()
    _sync_categorias_desde_productos()
