"""
app.py - Punto de entrada y Dashboard principal del sistema de
Control de Inventario y Punto de Venta.
"""

import streamlit as st
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import database as db
import theme

st.set_page_config(
    page_title="Inventario La Esquinita",
    page_icon=":material/inventory_2:",
    layout="wide",
    initial_sidebar_state="expanded",
)

db.init_db()
db.seed_demo_data()
theme.init_theme_state()

if "carrito" not in st.session_state:
    st.session_state.carrito = []


def pagina_dashboard():
    """Contenido del inicio principal (números del negocio + gráficos)."""
    theme.apply_theme()

    st.markdown('<div class="section-kicker">Números del negocio</div>', unsafe_allow_html=True)
    st.title("Resumen del día")
    st.caption("Resumen del rendimiento y la operación de tu negocio")

    kpis = db.get_kpis_dashboard()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        theme.kpi_card("Ingresos totales", kpis["ingresos_totales"], accent=True)
    with col2:
        theme.kpi_card("Ganancia neta", kpis["ganancia_neta"], accent=True)
    with col3:
        theme.kpi_card("Unidades vendidas", kpis["unidades_vendidas"], es_moneda=False)
    with col4:
        valor_inv = kpis["valor_inventario_costo"]
        valor_inv_venta = kpis["valor_inventario_venta"]
        theme.kpi_card("Valor de inventario", valor_inv)
        st.caption(f"A precio de venta: {theme.formato_moneda(valor_inv_venta)}")

    with st.expander("Zona de riesgo: reiniciar estadísticas", expanded=False):
        st.warning("Se eliminarán todas las ventas y sus detalles. Los indicadores volverán a cero; el inventario actual no se modifica.")
        if not st.session_state.get("confirmar_reinicio_inicio", False):
            if st.button("Reiniciar estadísticas", key="reiniciar_estadisticas_inicio"):
                st.session_state.confirmar_reinicio_inicio = True
                st.rerun()
        else:
            confirmar, cancelar = st.columns(2)
            if confirmar.button("Sí, reiniciar estadísticas", type="primary", key="confirmar_reinicio_inicio_btn"):
                db.limpiar_historial_ventas()
                st.session_state.confirmar_reinicio_inicio = False
                st.success("Estadísticas reiniciadas.")
                st.rerun()
            if cancelar.button("Cancelar", key="cancelar_reinicio_inicio"):
                st.session_state.confirmar_reinicio_inicio = False
                st.rerun()

    st.write("")
    st.divider()

    col_izq, col_der = st.columns(2)

    with col_izq:
        st.subheader("Ingresos vs. Ganancias")
        datos_tiempo = db.get_ingresos_ganancias_por_fecha()
        if datos_tiempo:
            df = pd.DataFrame(datos_tiempo)
            colores = theme.get_colores()
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df["dia"], y=df["ingresos"], name="Ingresos",
                marker_color=colores["primario"],
            ))
            fig.add_trace(go.Scatter(
                x=df["dia"], y=df["ganancia"], name="Ganancia",
                mode="lines+markers", line=dict(color=colores["secundario"], width=3),
            ))
            fig.update_layout(
                barmode="group",
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(t=40, b=20, l=10, r=10),
                height=380,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aún no hay ventas registradas para mostrar esta comparativa.")

    with col_der:
        st.subheader("Ventas por Categoría")
        datos_cat = db.get_ventas_por_categoria()
        if datos_cat:
            df_cat = pd.DataFrame(datos_cat)
            fig2 = px.pie(
                df_cat, names="categoria", values="total", hole=0.55,
                color_discrete_sequence=[colores["primario"], colores["secundario"], colores["terciario"], "#65728c"],
            )
            fig2.update_traces(textposition="inside", textinfo="percent+label")
            fig2.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=40, b=20, l=10, r=10),
                height=380,
                showlegend=True,
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Aún no hay ventas registradas para mostrar la participación por categoría.")

    st.divider()
    productos_bajo_stock = db.get_productos(solo_bajo_stock=True)
    if productos_bajo_stock:
        st.subheader("Productos que requieren reposición")
        df_bajo = pd.DataFrame(productos_bajo_stock)[
            ["nombre", "categoria", "stock_actual", "stock_minimo", "proveedor_nombre"]
        ]
        df_bajo.columns = ["Producto", "Categoría", "Stock Actual", "Stock Mínimo", "Proveedor"]
        st.dataframe(df_bajo, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# NAVEGACIÓN LATERAL AGRUPADA (Principal / Gestión)
# ---------------------------------------------------------------------------

pg_dashboard = st.Page(pagina_dashboard, title="Inicio", icon=":material/dashboard:", default=True, url_path="dashboard")
pg_inventario = st.Page("pages/inventario.py", title="Inventario", icon=":material/inventory_2:", url_path="inventario")
pg_venta = st.Page("pages/venta_libre.py", title="Venta Libre", icon=":material/point_of_sale:", url_path="venta-libre")
pg_historial = st.Page("pages/historial_ventas.py", title="Historial de ventas", icon=":material/receipt_long:", url_path="historial-ventas")
pg_proveedores = st.Page("pages/proveedores.py", title="Proveedores", icon=":material/local_shipping:", url_path="proveedores")
pg_ganancias = st.Page("pages/ganancias.py", title="Ganancias", icon=":material/monitoring:", url_path="ganancias")

nav = st.navigation(
    {
        "PRINCIPAL": [pg_dashboard, pg_inventario, pg_venta, pg_historial],
        "GESTIÓN": [pg_proveedores, pg_ganancias],
    }
)

with st.sidebar:
    theme.apply_theme()
    st.markdown('<div class="brand-lockup"><div class="brand-name">Inventario La Esquinita</div><div class="brand-subtitle">Control simple de productos, ventas y proveedores</div></div>', unsafe_allow_html=True)
    st.divider()

    notifs = db.get_notificaciones(solo_no_leidas=True)
    if theme.notificaciones_panel(notifs):
        db.limpiar_notificaciones()
        st.success("Notificaciones limpiadas.")
        st.rerun()

    st.divider()
    theme.theme_selector_widget()

    st.divider()
    if st.button("Limpiar memoria y recargar", use_container_width=True, help="Limpia únicamente la caché temporal de Streamlit. Tus ventas e inventario no se modifican."):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.toast("Memoria limpiada y sistema optimizado")
        time.sleep(1)
        st.rerun()

    st.divider()
    with st.expander("Copia de seguridad"):
        backup_json = db.export_backup()
        st.download_button(
            "Guardar copia de seguridad",
            data=backup_json,
            file_name="copia_seguridad_inventario.json",
            mime="application/json",
            use_container_width=True,
        )
        archivo = st.file_uploader("Elegir archivo de copia", type=["json"], key="uploader_backup")
        if archivo is not None:
            if st.button("Recuperar datos", use_container_width=True):
                try:
                    db.import_backup(archivo.read().decode("utf-8"))
                    st.success("Datos recuperados correctamente.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al recuperar los datos: {e}")

nav.run()
