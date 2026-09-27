"""Historial auditable de las operaciones de venta registradas."""

import streamlit as st
from html import escape

import database as db
import theme

theme.init_theme_state()
theme.apply_theme()

st.markdown('<div class="section-kicker">Auditoría de operaciones</div>', unsafe_allow_html=True)
st.title("Historial de ventas")
st.caption("Cada operación confirmada conserva fecha, importe y productos vendidos.")

solo_pendientes = st.toggle("Solo ventas pendientes de pago", key="filtro_deudas_historial")
ventas = db.get_historial_ventas(solo_pendientes=solo_pendientes)
if not ventas:
    st.info("No hay deudas pendientes." if solo_pendientes else "Todavía no hay ventas registradas.")
else:
    with st.expander("Zona de riesgo: vaciar historial", expanded=False):
        st.warning("Esta acción elimina todas las ventas y reinicia las estadísticas. No modifica el stock actual y no se puede deshacer.")
        if not st.session_state.get("confirmar_vaciar_historial", False):
            if st.button("Vaciar historial completo", type="secondary", key="vaciar_historial"):
                st.session_state.confirmar_vaciar_historial = True
                st.rerun()
        else:
            st.error("Confirmá el borrado definitivo del historial de ventas.")
            confirmar, cancelar = st.columns(2)
            if confirmar.button("Sí, vaciar historial", type="primary", key="confirmar_vaciar_historial_btn"):
                db.limpiar_historial_ventas()
                st.session_state.confirmar_vaciar_historial = False
                st.success("Historial y estadísticas reiniciados.")
                st.rerun()
            if cancelar.button("Cancelar", key="cancelar_vaciar_historial"):
                st.session_state.confirmar_vaciar_historial = False
                st.rerun()

    st.caption(f"Mostrando las últimas {len(ventas)} operación(es).")
    for venta in ventas:
        fecha = escape(venta["fecha"].replace("T", " "))
        with st.expander(
            f"Venta #{venta['id']} · {fecha} · {theme.formato_moneda(venta['total_venta'])}",
            expanded=False,
        ):
            st.caption(f"Ganancia registrada: {theme.formato_moneda(venta['ganancia_total'])}")
            estado = venta.get("estado_pago", "Pagado")
            abonado = venta.get("monto_pagado", venta["total_venta"])
            if estado == "Debe":
                st.warning(
                    f"Debe {theme.formato_moneda(venta['total_venta'] - abonado)} · "
                    f"Cliente: {venta.get('cliente_nombre') or 'Sin nombre'}"
                )
                if st.button("Saldar deuda", type="primary", key=f"saldar_deuda_{venta['id']}"):
                    try:
                        db.saldar_deuda(venta["id"])
                        st.success("Deuda marcada como pagada.")
                        st.rerun()
                    except ValueError as error:
                        st.error(str(error))
            else:
                st.caption(f"Pago registrado: {theme.formato_moneda(abonado)} · Pagado")
            for item in venta["detalle"]:
                nombre = escape(item["producto_nombre"])
                categoria = escape(item.get("categoria") or db.SIN_CATEGORIA)
                st.markdown(
                    f"**{nombre}** · {categoria}  \n"
                    f"{item['cantidad']:g} × {theme.formato_moneda(item['precio_unitario'])} = "
                    f"**{theme.formato_moneda(item['subtotal'])}**"
                )
            estado_confirmacion = f"confirmar_borrado_venta_{venta['id']}"
            if not st.session_state.get(estado_confirmacion, False):
                if st.button("Eliminar esta venta", key=f"borrar_venta_{venta['id']}"):
                    st.session_state[estado_confirmacion] = True
                    st.rerun()
            else:
                st.warning("Esta operación se eliminará del historial y de las estadísticas; el stock no se modifica.")
                confirmar, cancelar = st.columns(2)
                if confirmar.button("Sí, eliminar venta", type="primary", key=f"confirmar_borrar_venta_{venta['id']}"):
                    try:
                        db.delete_venta(venta["id"])
                        st.session_state[estado_confirmacion] = False
                        st.success("Venta eliminada del historial.")
                        st.rerun()
                    except ValueError as error:
                        st.error(str(error))
                if cancelar.button("Cancelar", key=f"cancelar_borrar_venta_{venta['id']}"):
                    st.session_state[estado_confirmacion] = False
                    st.rerun()
