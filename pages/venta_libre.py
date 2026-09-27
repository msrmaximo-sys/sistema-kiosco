"""
venta_libre.py - Punto de Venta (POS): búsqueda de productos, carrito
dinámico con edición de cantidad/precio, y confirmación atómica de la venta.
"""

import streamlit as st
from html import escape

import database as db
import theme
from database import StockInsuficienteError

theme.init_theme_state()
theme.apply_theme()

st.markdown('<div class="section-kicker">Punto de venta</div>', unsafe_allow_html=True)
st.title("Venta Libre")
st.caption("Buscá productos, armá el carrito y confirmá la venta")

if "pago_pos_version" not in st.session_state:
    st.session_state.pago_pos_version = 0


def limpiar_pago_pos():
    """Genera campos de pago nuevos sin escribir sobre widgets ya creados."""
    st.session_state.pago_pos_version += 1


def confirmar_venta_pos(total, monto_pagado=None, cliente_nombre=""):
    """Confirma una venta y reinicia el estado visual en la siguiente ejecución."""
    carrito_valido = [item for item in st.session_state.carrito if item["cantidad"] > 0]
    if not carrito_valido:
        st.error("El carrito no tiene ítems con cantidad válida.")
        return
    try:
        venta_id = db.confirmar_venta(carrito_valido, monto_pagado, cliente_nombre)
        st.session_state.carrito = []
        limpiar_pago_pos()
        st.session_state.pos_resultado = (
            "success",
            f"Venta #{venta_id} confirmada correctamente. Total: {theme.formato_moneda(total)}",
        )
        st.rerun()
    except StockInsuficienteError as error:
        st.error(str(error))
    except ValueError as error:
        st.error(str(error))


def agregar_producto_al_carrito(producto, cantidad=1.0):
    """Agrega o incrementa un producto en el carrito respetando el stock disponible."""
    existe = next(
        (it for it in st.session_state.carrito if it["producto_id"] == producto["id"]),
        None,
    )
    if existe:
        if existe["cantidad"] + cantidad <= producto["stock_actual"]:
            existe["cantidad"] += cantidad
            return True, None
        return False, "No hay más stock disponible de este producto."

    if cantidad <= producto["stock_actual"]:
        st.session_state.carrito.append({
            "producto_id": producto["id"],
            "nombre": producto["nombre"],
            "cantidad": float(cantidad),
            "precio_unitario": producto["precio_venta"],
            "costo_unitario": producto["precio_compra"],
            "stock_disponible": producto["stock_actual"],
        })
        return True, None

    return False, "No hay stock disponible de este producto."


def procesar_busqueda_pos():
    """Callback: modifica el campo antes de que Streamlit lo renderice."""
    busqueda = st.session_state.get("busqueda_pos", "").strip()
    st.session_state.pos_mensaje = None
    if not busqueda:
        return
    try:
        producto = db.get_producto_por_nombre(busqueda)
        if producto:
            ok, mensaje = agregar_producto_al_carrito(producto)
            st.session_state.pos_mensaje = ("success" if ok else "warning", mensaje or f"{producto['nombre']} agregado al carrito.")
            if ok:
                st.session_state.busqueda_pos = ""
    except ValueError as error:
        st.session_state.pos_mensaje = ("warning", str(error))


col_buscador, col_resumen = st.columns([1.4, 1])

# ---------------------------------------------------------------------------
# BUSCADOR Y SELECCIÓN DE PRODUCTOS
# ---------------------------------------------------------------------------

with col_buscador:
    st.subheader("Buscar productos")
    if "busqueda_pos" not in st.session_state:
        st.session_state.busqueda_pos = ""

    busqueda = st.text_input(
        "Buscar productos",
        placeholder="Escribí el nombre del producto...",
        key="busqueda_pos",
        on_change=procesar_busqueda_pos,
    )

    if mensaje := st.session_state.pop("pos_mensaje", None):
        getattr(st, mensaje[0])(mensaje[1])

    productos_encontrados = db.get_productos(search=busqueda) if busqueda else db.get_productos()

    if not productos_encontrados:
        st.info("No se encontraron productos.")
    else:
        for p in productos_encontrados[:12]:
            with st.container(border=True):
                c1, c2, c3 = st.columns([2.2, 1, 1])
                with c1:
                    st.markdown(f'<div class="product-name">{escape(p["nombre"])}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="product-meta">Categoría: {escape(p["categoria"])}<br>Disponible: {p["stock_actual"]:g} {escape(p["unidad_medida"])}</div>', unsafe_allow_html=True)
                with c2:
                    st.write(theme.formato_moneda(p["precio_venta"]))
                with c3:
                    disabled = p["stock_actual"] <= 0
                    if st.button(
                        "Agregar" if not disabled else "Sin stock",
                        key=f"add_cart_{p['id']}",
                        disabled=disabled,
                        use_container_width=True,
                    ):
                        ok, mensaje = agregar_producto_al_carrito(p)
                        if ok:
                            st.rerun()
                        else:
                            st.warning(mensaje)

# ---------------------------------------------------------------------------
# CARRITO DE COMPRAS
# ---------------------------------------------------------------------------

with col_resumen:
    st.subheader("Carrito")

    if resultado := st.session_state.pop("pos_resultado", None):
        getattr(st, resultado[0])(resultado[1])

    if not st.session_state.carrito:
        st.info("El carrito está vacío. Agregá productos desde la búsqueda.")
    else:
        total = 0.0
        for idx, item in enumerate(st.session_state.carrito):
            with st.container(border=True):
                st.markdown(f"**{item['nombre']}**")
                c1, c2, c3 = st.columns([1.1, 1.2, 0.5])
                with c1:
                    nueva_cant = st.number_input(
                        "Cantidad", min_value=0.0,
                        max_value=float(item["stock_disponible"]),
                        value=float(item["cantidad"]), step=1.0,
                        key=f"cant_{idx}", label_visibility="collapsed",
                    )
                    item["cantidad"] = nueva_cant
                with c2:
                    nuevo_precio = st.number_input(
                        "Precio unit.", min_value=0.0,
                        value=float(item["precio_unitario"]), step=0.01, format="%.2f",
                        key=f"precio_{idx}", label_visibility="collapsed",
                    )
                    item["precio_unitario"] = nuevo_precio
                with c3:
                    if st.button("Quitar", key=f"del_cart_{idx}"):
                        st.session_state.carrito.pop(idx)
                        st.rerun()

                subtotal = item["cantidad"] * item["precio_unitario"]
                st.caption(f"{item['cantidad']:g} x {theme.formato_moneda(item['precio_unitario'])} = **{theme.formato_moneda(subtotal)}**")
                total += subtotal

        st.divider()
        st.markdown(f"### Total a Pagar: {theme.formato_moneda(total)}")

        version_pago = st.session_state.pago_pos_version
        monto_abonado = st.number_input(
            "¿Con cuánto abona?",
            min_value=0.0,
            value=0.0,
            step=100.0,
            format="%.2f",
            key=f"monto_abonado_pos_{version_pago}",
            help="Opcional: si lo dejás en $0, se registra como pago exacto.",
        )
        pago_parcial = 0 < monto_abonado < total
        if monto_abonado >= total and monto_abonado > 0:
            vuelto = monto_abonado - total
            st.markdown(
                f'<div class="vuelto-destacado">Vuelto a entregar: {theme.formato_moneda(vuelto)}</div>',
                unsafe_allow_html=True,
            )

        if pago_parcial:
            faltante = total - monto_abonado
            st.warning(f"Monto Insuficiente. Faltan {theme.formato_moneda(faltante)} para cubrir el total.")
            cliente_nombre = st.text_input(
                "Nombre del cliente*",
                key=f"cliente_pago_parcial_{version_pago}",
                placeholder="Ej: Marta García",
            )
            col_deuda, col_pagado = st.columns(2)
            if col_deuda.button("Registrar pago parcial", type="primary", use_container_width=True):
                confirmar_venta_pos(total, monto_abonado, cliente_nombre)
            if col_pagado.button("Asumir pago total", use_container_width=True):
                confirmar_venta_pos(total, total)
        else:
            col_confirmar = st.container()
            with col_confirmar:
                if st.button("Confirmar venta", type="primary", use_container_width=True):
                    # $0 es deliberadamente pago exacto; un importe mayor se registra hasta el total.
                    confirmar_venta_pos(total, monto_abonado if monto_abonado > 0 else None)
        col_vaciar, col_cancelar = st.columns(2)
        with col_vaciar:
            if st.button("Vaciar carrito", use_container_width=True):
                st.session_state.carrito = []
                limpiar_pago_pos()
                st.rerun()
        with col_cancelar:
            if st.button("Cancelar", use_container_width=True):
                st.session_state.carrito = []
                limpiar_pago_pos()
                st.rerun()
