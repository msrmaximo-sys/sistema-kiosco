"""
inventario.py - Gestión completa de productos: alta, edición, borrado,
búsqueda, filtros por categoría y por stock bajo.
"""

import streamlit as st
import pandas as pd
from html import escape

import database as db
import theme

theme.init_theme_state()
theme.apply_theme()

st.markdown('<div class="section-kicker">Catálogo y existencias</div>', unsafe_allow_html=True)
st.title("Gestión de Inventario")
st.caption("Administrá tus productos, precios y niveles de stock")

if "mostrar_form_nuevo" not in st.session_state:
    st.session_state.mostrar_form_nuevo = False
if "editando_producto_id" not in st.session_state:
    st.session_state.editando_producto_id = None
if "mostrar_gestion_categorias" not in st.session_state:
    st.session_state.mostrar_gestion_categorias = False

# ---------------------------------------------------------------------------
# BARRA DE FILTROS
# ---------------------------------------------------------------------------

col_b, col_c, col_f, col_cat, col_n = st.columns([2.6, 1.6, 1.4, 1.4, 1.4])
with col_b:
    busqueda = st.text_input("Buscar producto por nombre", placeholder="Ej: Aceite girasol...")
with col_c:
    categorias_existentes = ["Todas"] + db.get_categorias()
    categoria_filtro = st.selectbox("Categoría", categorias_existentes)
with col_f:
    st.write("")
    st.write("")
    solo_bajo_stock = st.toggle("Mostrar solo poco stock")
with col_cat:
    st.write("")
    st.write("")
    if st.button("Gestionar categorías", use_container_width=True):
        st.session_state.mostrar_gestion_categorias = not st.session_state.mostrar_gestion_categorias
with col_n:
    st.write("")
    st.write("")
    if st.button("Nuevo producto", use_container_width=True, type="primary"):
        st.session_state.mostrar_form_nuevo = True
        st.session_state.editando_producto_id = None

if st.session_state.mostrar_gestion_categorias:
    with st.expander("Gestión de categorías", expanded=True):
        st.caption("Al renombrar una categoría, se actualizan sus productos. Al eliminarla, los productos asociados quedan como 'Sin categoría'.")

        nueva_categoria = st.text_input("Nueva categoría", placeholder="Ej: Golosinas", key="input_nueva_categoria")
        if st.button("Agregar categoría", key="btn_add_categoria", type="primary"):
            if not nueva_categoria.strip():
                st.error("Escribí un nombre para la categoría.")
            else:
                try:
                    db.add_categoria(nueva_categoria)
                    st.success(f"Categoría '{nueva_categoria.strip()}' agregada.")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

        st.divider()
        categorias_info = db.get_categorias_con_conteo()
        if not categorias_info:
            st.info("Todavía no hay categorías registradas.")
        else:
            for cat in categorias_info:
                cc1, cc2, cc3, cc4 = st.columns([2.2, 1, 1, 1])
                nuevo_nombre = cc1.text_input(
                    f"Categoría ({cat['total_productos']} producto(s))",
                    value=cat["nombre"],
                    key=f"edit_cat_{cat['nombre']}",
                    label_visibility="collapsed",
                )
                cc2.caption(f"{cat['total_productos']} producto(s)")
                if cc3.button("Guardar", key=f"save_cat_{cat['nombre']}"):
                    if not nuevo_nombre.strip():
                        st.error("El nombre no puede quedar vacío.")
                    elif nuevo_nombre.strip() != cat["nombre"]:
                        try:
                            db.update_categoria(cat["nombre"], nuevo_nombre)
                            st.success(f"Categoría actualizada a '{nuevo_nombre.strip()}'.")
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))
                if cc4.button("Eliminar", key=f"del_cat_{cat['nombre']}"):
                    st.session_state[f"confirmar_borrado_cat_{cat['nombre']}"] = True
                if st.session_state.get(f"confirmar_borrado_cat_{cat['nombre']}", False):
                    st.warning(
                        f"¿Eliminar '{cat['nombre']}'? Sus {cat['total_productos']} producto(s) pasarán a 'Sin categoría'."
                    )
                    cy, cn = st.columns(2)
                    if cy.button("Sí, eliminar", key=f"confirm_yes_cat_{cat['nombre']}", type="primary"):
                        try:
                            db.delete_categoria(cat["nombre"])
                            st.session_state[f"confirmar_borrado_cat_{cat['nombre']}"] = False
                            st.success("Categoría eliminada y productos actualizados.")
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))
                    if cn.button("Cancelar", key=f"confirm_no_cat_{cat['nombre']}"):
                        st.session_state[f"confirmar_borrado_cat_{cat['nombre']}"] = False
                        st.rerun()

st.divider()


# ---------------------------------------------------------------------------
# FORMULARIO: NUEVO PRODUCTO / EDITAR PRODUCTO
# ---------------------------------------------------------------------------

def formulario_producto(producto_existente=None):
    """Renderiza el formulario de alta/edición de producto con cálculo de margen en vivo."""
    es_edicion = producto_existente is not None
    titulo = "Editar producto" if es_edicion else "Nuevo producto"

    with st.container(border=True):
        st.subheader(titulo)

        categorias = db.get_categorias()
        proveedores = db.get_proveedores()
        opciones_proveedor = {"Ninguno": None}
        opciones_proveedor.update({p["nombre_empresa"]: p["id"] for p in proveedores})

        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input(
                "Nombre*", value=producto_existente["nombre"] if es_edicion else "",
                key="form_nombre",
            )
            modo_categoria = st.radio(
                "Categoría*", ["Elegir existente", "Escribir nueva"],
                horizontal=True, key="form_modo_categoria",
            )
            if modo_categoria == "Elegir existente" and categorias:
                idx = categorias.index(producto_existente["categoria"]) if es_edicion and producto_existente["categoria"] in categorias else 0
                categoria = st.selectbox("Seleccionar categoría", categorias, index=idx, key="form_cat_select")
            else:
                categoria = st.text_input(
                    "Nueva categoría",
                    value=producto_existente["categoria"] if es_edicion and modo_categoria != "Elegir existente" else "",
                    key="form_cat_texto",
                )

            unidad_medida = st.text_input(
                "Unidad de medida*", value=producto_existente["unidad_medida"] if es_edicion else "unidad",
                key="form_unidad", help="Ej: unidad, kg, litro, paquete",
            )
            nombre_prov_actual = "Ninguno"
            if es_edicion and producto_existente.get("proveedor_id"):
                for nom, pid in opciones_proveedor.items():
                    if pid == producto_existente["proveedor_id"]:
                        nombre_prov_actual = nom
            proveedor_sel = st.selectbox(
                "Proveedor", list(opciones_proveedor.keys()),
                index=list(opciones_proveedor.keys()).index(nombre_prov_actual),
                key="form_proveedor",
            )

        with col2:
            precio_compra = st.number_input(
                "Precio de Compra ($)*", min_value=0.0, step=0.01, format="%.2f",
                value=float(producto_existente["precio_compra"]) if es_edicion else 0.0,
                key="form_precio_compra",
            )
            precio_venta = st.number_input(
                "Precio de Venta ($)*", min_value=0.0, step=0.01, format="%.2f",
                value=float(producto_existente["precio_venta"]) if es_edicion else 0.0,
                key="form_precio_venta",
            )
            stock_actual = st.number_input(
                "Stock Actual*", min_value=0.0, step=1.0, format="%.2f",
                value=float(producto_existente["stock_actual"]) if es_edicion else 0.0,
                key="form_stock_actual",
            )
            stock_minimo = st.number_input(
                "Stock Mínimo*", min_value=0.0, step=1.0, format="%.2f",
                value=float(producto_existente["stock_minimo"]) if es_edicion else 0.0,
                key="form_stock_minimo",
            )

        # Cálculo en vivo de margen y rentabilidad
        margen = precio_venta - precio_compra
        rentabilidad = (margen / precio_compra * 100) if precio_compra > 0 else 0.0
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric("Margen por unidad", theme.formato_moneda(margen))
        with col_m2:
            st.metric("Rentabilidad", f"{rentabilidad:.1f}%")

        st.write("")
        col_guardar, col_cancelar = st.columns(2)
        with col_guardar:
            if st.button("Guardar producto", type="primary", use_container_width=True, key="btn_guardar_producto"):
                if not nombre.strip() or not categoria.strip() or not unidad_medida.strip():
                    st.error("Por favor completá los campos obligatorios: Nombre, Categoría y Unidad de medida.")
                else:
                    proveedor_id = opciones_proveedor[proveedor_sel]
                    try:
                        if es_edicion:
                            db.update_producto(
                                producto_existente["id"], nombre, categoria, unidad_medida,
                                proveedor_id, precio_compra, precio_venta, stock_actual, stock_minimo,
                            )
                            st.success(f"Producto '{nombre}' actualizado correctamente.")
                        else:
                            db.add_producto(
                                nombre, categoria, unidad_medida, proveedor_id,
                                precio_compra, precio_venta, stock_actual, stock_minimo,
                            )
                            st.success(f"Producto '{nombre}' agregado correctamente.")
                        st.session_state.mostrar_form_nuevo = False
                        st.session_state.editando_producto_id = None
                        st.rerun()
                    except ValueError as error:
                        st.error(str(error))
        with col_cancelar:
            if st.button("Cancelar", use_container_width=True, key="btn_cancelar_producto"):
                st.session_state.mostrar_form_nuevo = False
                st.session_state.editando_producto_id = None
                st.rerun()


if st.session_state.mostrar_form_nuevo and st.session_state.editando_producto_id is None:
    formulario_producto()
    st.divider()

if st.session_state.editando_producto_id is not None:
    producto_a_editar = db.get_producto(st.session_state.editando_producto_id)
    if producto_a_editar:
        formulario_producto(producto_a_editar)
        st.divider()

# ---------------------------------------------------------------------------
# TABLA DE PRODUCTOS
# ---------------------------------------------------------------------------

productos = db.get_productos(search=busqueda, categoria=categoria_filtro, solo_bajo_stock=solo_bajo_stock)

if not productos:
    st.info("No se encontraron productos con los filtros aplicados.")
else:
    st.caption(f"{len(productos)} producto(s) encontrado(s)")

    header = st.columns([2, 1.15, 1.35, 1, 1, 0.8, 1, 0.9, 1.5, 1.0, 1.0])
    labels = ["Producto", "Categoría", "Proveedor", "P. Compra", "P. Venta",
              "Stock", "Margen $", "Margen %", "Ingreso Rápido", "Editar", "Borrar"]
    for c, lbl in zip(header, labels):
        c.markdown(f"**{lbl}**")

    for p in productos:
        cols = st.columns([2, 1.15, 1.35, 1, 1, 0.8, 1, 0.9, 1.5, 1.0, 1.0])
        margen = p["precio_venta"] - p["precio_compra"]
        rentabilidad = (margen / p["precio_compra"] * 100) if p["precio_compra"] > 0 else 0.0
        alerta_precio = p["precio_venta"] <= 0 or margen <= 0
        alerta_html = '<span class="alerta-precio" title="Revisar precio: margen nulo o negativo">⚠️</span> ' if alerta_precio else ""

        cols[0].markdown(
            f'<div class="table-product">{alerta_html}{escape(p["nombre"])}</div>',
            unsafe_allow_html=True,
        )
        cols[1].markdown(f'<div class="table-detail">{escape(p["categoria"])}</div>', unsafe_allow_html=True)
        cols[2].markdown(f'<div class="table-detail">{escape(p["proveedor_nombre"])}</div>', unsafe_allow_html=True)
        cols[3].write(theme.formato_moneda(p["precio_compra"]))
        cols[4].write(theme.formato_moneda(p["precio_venta"]))

        if p["stock_actual"] <= p["stock_minimo"]:
            cols[5].markdown(f'<span class="badge-alerta">{p["stock_actual"]:g}</span>', unsafe_allow_html=True)
        else:
            cols[5].markdown(f'<span class="badge-ok">{p["stock_actual"]:g}</span>', unsafe_allow_html=True)

        if alerta_precio:
            cols[6].markdown(
                f'<span class="alerta-precio">⚠️</span> {theme.formato_moneda(margen)}',
                unsafe_allow_html=True,
            )
        else:
            cols[6].write(theme.formato_moneda(margen))
        cols[7].write(f"{rentabilidad:.1f}%")

        with cols[8]:
            ing_col1, ing_col2 = st.columns([1.3, 0.7])
            cant_ingreso = ing_col1.number_input(
                "Cantidad ingreso",
                min_value=0.0,
                value=0.0,
                step=1.0,
                key=f"ingreso_{p['id']}",
                label_visibility="collapsed",
            )
            if ing_col2.button("+", key=f"ingreso_add_{p['id']}", help="Agregar stock"):
                if cant_ingreso > 0:
                    try:
                        db.incrementar_stock(p["id"], cant_ingreso)
                        st.rerun()
                    except ValueError as e:
                        st.warning(str(e))
                else:
                    st.warning("Ingresá una cantidad mayor a cero.")

        if cols[9].button("Editar", key=f"edit_{p['id']}"):
            st.session_state.editando_producto_id = p["id"]
            st.session_state.mostrar_form_nuevo = False
            st.rerun()

        if cols[10].button("Eliminar", key=f"del_{p['id']}"):
            st.session_state[f"confirmar_borrado_{p['id']}"] = True

        if st.session_state.get(f"confirmar_borrado_{p['id']}", False):
            st.warning(f"¿Confirmás borrar '{p['nombre']}'? Esta acción no se puede deshacer.")
            cb1, cb2 = st.columns(2)
            if cb1.button("Sí, borrar", key=f"confirm_yes_{p['id']}", type="primary"):
                db.delete_producto(p["id"])
                st.session_state[f"confirmar_borrado_{p['id']}"] = False
                st.success(f"Producto '{p['nombre']}' eliminado.")
                st.rerun()
            if cb2.button("Cancelar", key=f"confirm_no_{p['id']}"):
                st.session_state[f"confirmar_borrado_{p['id']}"] = False
                st.rerun()
