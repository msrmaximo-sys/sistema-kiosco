"""Reportes filtrables y reinicio protegido de estadísticas de ventas."""

import streamlit as st
import pandas as pd
import plotly.express as px
from html import escape

import database as db
import theme

theme.init_theme_state()
theme.apply_theme()

st.markdown('<div class="section-kicker">Análisis financiero</div>', unsafe_allow_html=True)
st.title("Ganancias y Reportes")
st.caption("Filtrá resultados por categoría o producto para analizar cada línea de venta.")

categorias = ["Todas"] + db.get_categorias_vendidas()
col_categoria, col_producto = st.columns(2)
with col_categoria:
    categoria = st.selectbox("Categoría", categorias, key="filtro_ganancias_categoria")
with col_producto:
    productos = ["Todos"] + db.get_productos_vendidos(categoria)
    producto = st.selectbox("Producto", productos, key="filtro_ganancias_producto")

kpis = db.get_kpis_ganancias(categoria, producto)
col1, col2, col3, col4 = st.columns(4)
with col1:
    theme.kpi_card("Ingresos", kpis["ingresos_totales"], accent=True)
with col2:
    theme.kpi_card("Costo de mercadería", kpis["cogs"])
with col3:
    theme.kpi_card("Ganancia neta", kpis["ganancia_neta"], accent=True)
with col4:
    destacado = escape(kpis["producto_estrella"])
    st.markdown(
        f'<div class="kpi-card"><div class="kpi-label">Producto destacado</div>'
        f'<div class="kpi-value" style="font-size:1.15rem;">{destacado}</div>'
        f'<div style="font-size:0.78rem;opacity:0.65;margin-top:2px;">'
        f'{kpis["producto_estrella_unidades"]:g} unidades vendidas</div></div>',
        unsafe_allow_html=True,
    )

st.write("")
st.divider()
with st.expander("Zona de riesgo: reiniciar estadísticas", expanded=False):
    st.warning("El reinicio elimina todas las ventas y sus detalles, por lo que las estadísticas quedarán en cero. El stock actual no se modifica.")
    if not st.session_state.get("confirmar_reinicio_ganancias", False):
        if st.button("Reiniciar estadísticas", key="reiniciar_estadisticas_ganancias"):
            st.session_state.confirmar_reinicio_ganancias = True
            st.rerun()
    else:
        confirmar, cancelar = st.columns(2)
        if confirmar.button("Sí, reiniciar estadísticas", type="primary", key="confirmar_reinicio_ganancias_btn"):
            db.limpiar_historial_ventas()
            st.session_state.confirmar_reinicio_ganancias = False
            st.success("Estadísticas reiniciadas.")
            st.rerun()
        if cancelar.button("Cancelar", key="cancelar_reinicio_ganancias"):
            st.session_state.confirmar_reinicio_ganancias = False
            st.rerun()

st.divider()
rendimiento = db.get_rendimiento_productos(categoria, producto)
ganancia_cat = db.get_ganancia_por_categoria(categoria, producto)

izq, der = st.columns([1.35, 1])
with izq:
    st.subheader("Ganancia por producto")
    if rendimiento:
        df = pd.DataFrame(rendimiento)
        df["margen_%"] = df.apply(
            lambda fila: (fila["ganancia_total"] / (fila["ingresos"] - fila["ganancia_total"]) * 100)
            if (fila["ingresos"] - fila["ganancia_total"]) > 0 else 0,
            axis=1,
        )
        fig_producto = px.bar(
            df, x="producto_nombre", y="ganancia_total", color="ganancia_total",
            color_continuous_scale="Tealgrn", labels={"producto_nombre": "Producto", "ganancia_total": "Ganancia ($)"},
        )
        fig_producto.update_layout(height=360, margin=dict(t=20, b=80, l=10, r=10), coloraxis_showscale=False)
        st.plotly_chart(fig_producto, use_container_width=True)
        tabla = df[["producto_nombre", "unidades_vendidas", "ingresos", "ganancia_total", "margen_%"]].copy()
        tabla["ingresos"] = tabla["ingresos"].map(theme.formato_moneda)
        tabla["ganancia_total"] = tabla["ganancia_total"].map(theme.formato_moneda)
        tabla["margen_%"] = tabla["margen_%"].map(lambda valor: f"{valor:.1f}%")
        tabla.columns = ["Producto", "Unidades", "Ingresos", "Ganancia", "Margen %"]
        st.dataframe(tabla, use_container_width=True, hide_index=True)
    else:
        st.info("No hay ventas que coincidan con los filtros.")

with der:
    st.subheader("Ganancia por categoría")
    if ganancia_cat:
        df_cat = pd.DataFrame(ganancia_cat)
        fig_categoria = px.bar(
            df_cat, x="categoria", y="ganancia", color="categoria",
            labels={"categoria": "Categoría", "ganancia": "Ganancia ($)"},
        )
        fig_categoria.update_layout(showlegend=False, height=360, margin=dict(t=20, b=60, l=10, r=10))
        st.plotly_chart(fig_categoria, use_container_width=True)
        resumen = df_cat.copy()
        resumen["ganancia"] = resumen["ganancia"].map(theme.formato_moneda)
        resumen.columns = ["Categoría", "Ganancia"]
        st.dataframe(resumen, use_container_width=True, hide_index=True)
    else:
        st.info("No hay datos de categorías para el filtro elegido.")
