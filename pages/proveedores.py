"""
proveedores.py - Gestión de proveedores: alta, edición, borrado y
vista en tarjetas con los productos asignados a cada uno.
"""

import streamlit as st
from html import escape

import database as db
import theme

theme.init_theme_state()
theme.apply_theme()

st.markdown('<div class="section-kicker">Red de abastecimiento</div>', unsafe_allow_html=True)
st.title("Gestión de Proveedores")
st.caption("Administrá tus proveedores y visualizá los productos que te ofrecen")

if "mostrar_form_proveedor" not in st.session_state:
    st.session_state.mostrar_form_proveedor = False
if "editando_proveedor_id" not in st.session_state:
    st.session_state.editando_proveedor_id = None

col_titulo, col_boton = st.columns([4, 1])
with col_boton:
    if st.button("Nuevo proveedor", use_container_width=True, type="primary"):
        st.session_state.mostrar_form_proveedor = True
        st.session_state.editando_proveedor_id = None

st.divider()


def formulario_proveedor(proveedor_existente=None):
    es_edicion = proveedor_existente is not None
    titulo = "Editar proveedor" if es_edicion else "Nuevo proveedor"

    with st.container(border=True):
        st.subheader(titulo)
        col1, col2 = st.columns(2)
        with col1:
            nombre_empresa = st.text_input(
                "Nombre de la empresa*",
                value=proveedor_existente["nombre_empresa"] if es_edicion else "",
                key="form_nombre_empresa",
            )
            vendedor = st.text_input(
                "Nombre del vendedor",
                value=proveedor_existente["vendedor"] if es_edicion else "",
                key="form_vendedor", placeholder="Ej: Carlos",
            )
        with col2:
            telefono = st.text_input(
                "Teléfono",
                value=proveedor_existente["telefono"] if es_edicion else "",
                key="form_telefono",
            )
            correo = st.text_input(
                "Correo",
                value=proveedor_existente["correo"] if es_edicion else "",
                key="form_correo",
            )

        st.write("")
        col_g, col_c = st.columns(2)
        with col_g:
            if st.button("Guardar proveedor", type="primary", use_container_width=True, key="btn_guardar_proveedor"):
                if not nombre_empresa.strip():
                    st.error("El nombre de la empresa es obligatorio.")
                else:
                    try:
                        if es_edicion:
                            db.update_proveedor(proveedor_existente["id"], nombre_empresa, vendedor, telefono, correo)
                            st.success(f"Proveedor '{nombre_empresa}' actualizado.")
                        else:
                            db.add_proveedor(nombre_empresa, vendedor, telefono, correo)
                            st.success(f"Proveedor '{nombre_empresa}' agregado.")
                        st.session_state.mostrar_form_proveedor = False
                        st.session_state.editando_proveedor_id = None
                        st.rerun()
                    except ValueError as error:
                        st.error(str(error))
        with col_c:
            if st.button("Cancelar", use_container_width=True, key="btn_cancelar_proveedor"):
                st.session_state.mostrar_form_proveedor = False
                st.session_state.editando_proveedor_id = None
                st.rerun()


if st.session_state.mostrar_form_proveedor and st.session_state.editando_proveedor_id is None:
    formulario_proveedor()
    st.divider()

if st.session_state.editando_proveedor_id is not None:
    prov = db.get_proveedor(st.session_state.editando_proveedor_id)
    if prov:
        formulario_proveedor(prov)
        st.divider()

# ---------------------------------------------------------------------------
# VISTA EN TARJETAS
# ---------------------------------------------------------------------------

proveedores = db.get_proveedores()

if not proveedores:
    st.info("Todavía no registraste proveedores. Usá el botón 'Nuevo Proveedor' para empezar.")
else:
    columnas_por_fila = 2
    filas = [proveedores[i:i + columnas_por_fila] for i in range(0, len(proveedores), columnas_por_fila)]

    for fila in filas:
        cols = st.columns(columnas_por_fila)
        for col, prov in zip(cols, fila):
            with col:
                with st.container(border=True):
                    st.markdown(f"### {escape(prov['nombre_empresa'])}")
                    if prov["vendedor"]:
                        st.write(f"Vendedor: {prov['vendedor']}")
                    if prov["telefono"]:
                        st.write(f"Teléfono: {prov['telefono']}")
                    if prov["correo"]:
                        st.write(f"Correo: {prov['correo']}")

                    productos_prov = db.get_productos_por_proveedor(prov["id"])
                    st.markdown(f"**Productos asignados ({len(productos_prov)})**")
                    if productos_prov:
                        for p in productos_prov:
                            requiere_reposicion = p["stock_actual"] <= p["stock_minimo"]
                            badge_clase = "badge-alerta" if requiere_reposicion else "badge-ok"
                            st.markdown(
                                f"- {escape(p['nombre'])} — "
                                f'<span class="{badge_clase}">{p["stock_actual"]:g} {escape(p["unidad_medida"])}</span>',
                                unsafe_allow_html=True,
                            )
                    else:
                        st.caption("Sin productos asignados todavía.")

                    st.write("")
                    ce, cb = st.columns(2)
                    if ce.button("Editar", key=f"edit_prov_{prov['id']}", use_container_width=True):
                        st.session_state.editando_proveedor_id = prov["id"]
                        st.session_state.mostrar_form_proveedor = False
                        st.rerun()
                    if cb.button("Borrar", key=f"del_prov_{prov['id']}", use_container_width=True):
                        st.session_state[f"confirmar_borrado_prov_{prov['id']}"] = True

                    if st.session_state.get(f"confirmar_borrado_prov_{prov['id']}", False):
                        st.warning("¿Confirmás borrar este proveedor? Sus productos quedarán sin proveedor asignado.")
                        cy, cn = st.columns(2)
                        if cy.button("Sí, borrar", key=f"confirm_yes_prov_{prov['id']}", type="primary"):
                            db.delete_proveedor(prov["id"])
                            st.session_state[f"confirmar_borrado_prov_{prov['id']}"] = False
                            st.success("Proveedor eliminado.")
                            st.rerun()
                        if cn.button("Cancelar", key=f"confirm_no_prov_{prov['id']}"):
                            st.session_state[f"confirmar_borrado_prov_{prov['id']}"] = False
                            st.rerun()
