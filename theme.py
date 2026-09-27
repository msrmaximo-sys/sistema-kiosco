"""Sistema visual reutilizable para la interfaz de Inventario Pro."""

import streamlit as st


PALETAS = {
    "Coral nocturno": {
        "primario": "#ff6b5f", "secundario": "#ff9a72", "terciario": "#b82f4b",
        "brillo": "rgba(255, 107, 95, 0.22)",
    },
    "Océano eléctrico": {
        "primario": "#4f8cff", "secundario": "#67d5ff", "terciario": "#3451c9",
        "brillo": "rgba(79, 140, 255, 0.20)",
    },
    "Bosque digital": {
        "primario": "#28c78c", "secundario": "#8be3a8", "terciario": "#087c62",
        "brillo": "rgba(40, 199, 140, 0.20)",
    },
    "Violeta aurora": {
        "primario": "#9b7bff", "secundario": "#e19bff", "terciario": "#5a45c7",
        "brillo": "rgba(155, 123, 255, 0.22)",
    },
}


def init_theme_state():
    st.session_state.modo_oscuro = True
    if "paleta" not in st.session_state:
        st.session_state.paleta = "Coral nocturno"


def get_colores():
    return PALETAS.get(st.session_state.get("paleta"), PALETAS["Coral nocturno"])


def apply_theme():
    """Aplica una UI en capas, con gradientes y transiciones suaves."""
    init_theme_state()
    colores = get_colores()
    primario, secundario, terciario, brillo = (
        colores["primario"], colores["secundario"], colores["terciario"], colores["brillo"]
    )

    fondo = "#0b0c17"
    fondo_secundario = "#111323"
    tarjeta = "rgba(24, 27, 45, 0.84)"
    tarjeta_suave = "rgba(255, 255, 255, 0.045)"
    texto = "#f8f7ff"
    texto_secundario = "#d5d3e2"
    borde = "rgba(255, 255, 255, 0.10)"
    input_bg = "rgba(9, 11, 22, 0.58)"
    sombra = "0 16px 38px rgba(0, 0, 0, 0.28)"

    css = f"""
    <style>
        :root {{ --primary: {primario}; --secondary: {secundario}; --tertiary: {terciario}; }}
        .stApp {{
            color: {texto};
            font-size: 1.1rem;
            background:
                radial-gradient(circle at 88% 3%, {brillo} 0, transparent 26rem),
                radial-gradient(circle at 7% 72%, {brillo} 0, transparent 30rem),
                linear-gradient(135deg, {fondo} 0%, {fondo_secundario} 58%, {fondo} 100%);
        }}
        [data-testid="stHeader"] {{
            height: 2.1rem !important;
            min-height: 2.1rem !important;
            max-height: 2.1rem !important;
            background: rgba(11, 12, 23, 0.96) !important;
            border-bottom: 1px solid {borde};
            z-index: 999;
        }}
        [data-testid="stHeader"] > div {{
            min-height: 2.1rem !important;
            height: 2.1rem !important;
            padding-top: 0.15rem !important;
            padding-bottom: 0.15rem !important;
        }}
        [data-testid="stToolbar"] {{
            max-height: 2rem !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
        }}
        [data-testid="stAppDeployButton"] button,
        [data-testid="stToolbar"] button {{
            min-height: 1.75rem !important;
            height: 1.75rem !important;
            padding: 0.15rem 0.55rem !important;
            font-size: 0.78rem !important;
        }}
        section.main > div.block-container {{
            padding-top: 1.15rem !important;
            padding-bottom: 3rem;
        }}
        .block-container {{ max-width: 1440px; }}
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {fondo_secundario}, {fondo}) !important;
            border-right: 1px solid {borde};
        }}
        [data-testid="stSidebar"] > div:first-child {{ padding-top: 1.35rem; }}
        [data-testid="stSidebarNav"] {{ padding-top: 0.8rem; }}
        [data-testid="stSidebarNav"] a {{
            border-radius: 10px; margin: 0.14rem 0.35rem; transition: all .2s ease;
        }}
        [data-testid="stSidebarNav"] a:hover {{ background: {tarjeta_suave}; transform: translateX(3px); }}
        [data-testid="stSidebarNav"] a[aria-current="page"] {{
            background: linear-gradient(100deg, {brillo}, transparent); border-left: 3px solid {primario};
        }}
        h1, h2, h3 {{ color: {texto} !important; letter-spacing: -0.035em; }}
        h1 {{ font-weight: 780 !important; font-size: clamp(2rem, 3vw, 2.75rem) !important; margin-bottom: 0.1rem !important; }}
        h2, h3 {{ font-weight: 720 !important; }}
        p, label, [data-testid="stCaptionContainer"] {{ color: {texto_secundario}; }}
        [data-testid="stMarkdownContainer"] p, [data-testid="stText"] {{ font-size: 1.12rem; }}
        [data-testid="stDataFrame"] {{ color: {texto} !important; font-size: 1.08rem !important; }}
        [data-testid="stDataFrame"] * {{ color: inherit; }}
        [data-testid="stVerticalBlockBorderWrapper"], [data-testid="stDataFrame"], [data-testid="stExpander"] {{
            background: {tarjeta}; border: 1px solid {borde}; border-radius: 16px; box-shadow: {sombra};
        }}
        [data-testid="stVerticalBlockBorderWrapper"] {{ transition: transform .22s ease, border-color .22s ease; }}
        [data-testid="stVerticalBlockBorderWrapper"]:hover {{ border-color: color-mix(in srgb, {primario} 40%, {borde}); }}
        .kpi-card {{
            position: relative; overflow: hidden; min-height: 128px; padding: 1.2rem 1.25rem;
            border: 1px solid {borde}; border-radius: 18px; background: {tarjeta}; box-shadow: {sombra};
            transition: transform .22s ease, box-shadow .22s ease, border-color .22s ease;
        }}
        .kpi-card::after {{
            content: ""; position: absolute; width: 150px; height: 150px; top: -88px; right: -72px;
            border-radius: 50%; background: radial-gradient(circle, {brillo}, transparent 68%); pointer-events: none;
        }}
        .kpi-card:hover {{ transform: translateY(-4px); border-color: color-mix(in srgb, {primario} 48%, {borde}); box-shadow: 0 20px 42px rgba(0,0,0,.30); }}
        .kpi-label {{ color: {texto_secundario}; font-size: .9rem; font-weight: 700; letter-spacing: .04em; text-transform: uppercase; }}
        .kpi-value {{ color: {texto}; font-size: 1.8rem; font-weight: 800; letter-spacing: -.055em; margin-top: .35rem; }}
        .kpi-accent {{ color: {primario}; }}
        .badge-alerta, .badge-ok {{ padding: .23rem .58rem; border-radius: 999px; font-size: .72rem; font-weight: 750; }}
        .badge-alerta {{ color: #ffb4ac; background: rgba(234, 80, 73, .16); border: 1px solid rgba(234, 80, 73, .3); }}
        .badge-ok {{ color: #8de8bf; background: rgba(40, 199, 140, .13); border: 1px solid rgba(40, 199, 140, .25); }}
        .notif-card {{ background: {tarjeta_suave}; border: 1px solid rgba(234,80,73,.28); border-left: 3px solid #ea5049; border-radius: 11px; padding: .7rem .8rem; margin-bottom: .55rem; color: {texto}; }}
        .brand-lockup {{ padding: .5rem .25rem 1rem; }}
        .brand-name {{ color: {texto}; font-size: 1.38rem; font-weight: 820; letter-spacing: -.055em; }}
        .brand-pro {{ color: {secundario}; font-size: .7rem; font-weight: 800; letter-spacing: .1em; margin-left: .35rem; vertical-align: middle; }}
        .brand-subtitle {{ color: {texto_secundario}; font-size: .9rem; margin-top: .1rem; }}
        .section-kicker {{ color: {primario}; font-size: .84rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; margin-bottom: .15rem; }}
        .nav-section-title {{ color: {texto_secundario}; font-size: .7rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; margin: .9rem 0 .35rem .2rem; }}
        .stButton > button {{ min-height: 2.7rem; border-radius: 10px; font-size: .94rem; font-weight: 750; border: 1px solid {borde}; transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease; }}
        .stButton > button:hover {{ transform: translateY(-2px); border-color: color-mix(in srgb, {primario} 50%, {borde}); box-shadow: 0 8px 20px {brillo}; }}
        .stButton > button[kind="primary"] {{ background: linear-gradient(115deg, {primario}, {secundario}) !important; border: none !important; color: #10111d !important; font-size: 1rem !important; font-weight: 850 !important; text-shadow: none !important; }}
        .stButton > button[kind="primary"] * {{ color: #10111d !important; font-weight: 850 !important; }}
        .stTextInput input, .stNumberInput input, [data-baseweb="select"] > div {{ background: {input_bg} !important; border-color: {borde} !important; border-radius: 10px !important; color: {texto} !important; }}
        .stTextInput input:focus, .stNumberInput input:focus {{ border-color: {primario} !important; box-shadow: 0 0 0 3px {brillo} !important; }}
        [data-testid="stDataFrame"] {{ overflow: hidden; }}
        .table-product {{ color: {texto}; font-size: 1.14rem; font-weight: 750; line-height: 1.3; }}
        .table-detail {{ color: {texto_secundario}; font-size: 1rem; line-height: 1.45; }}
        .product-name {{ color: {texto}; font-size: 1.18rem; font-weight: 780; margin-bottom: .18rem; }}
        .product-meta {{ color: {texto_secundario}; font-size: 1.04rem; line-height: 1.45; }}
        .alerta-precio {{ color: #ffb347; font-size: 1rem; margin-right: .35rem; vertical-align: middle; }}
        .vuelto-destacado {{
            color: {secundario}; font-size: 1.35rem; font-weight: 820; margin-top: .35rem;
            padding: .65rem .85rem; border-radius: 12px;
            background: rgba(255, 154, 114, 0.12); border: 1px solid rgba(255, 154, 114, 0.35);
        }}
        hr {{ border-color: {borde}; }}
        @media (prefers-reduced-motion: no-preference) {{ .kpi-card {{ animation: lift-in .38s ease both; }} @keyframes lift-in {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: translateY(0); }} }} }}
    </style>
    <script>
    (function() {{
        const traducciones = {{
            "Clear cache": "Limpiar caché",
            "Clear caches": "Limpiar caché",
            "Rerun": "Recargar app",
            "Settings": "Configuración",
            "About": "Acerca de",
            "Report a bug": "Reportar un error",
            "Get help": "Obtener ayuda",
            "Deploy": "Publicar",
            "Developer options": "Opciones de desarrollador",
            "Print": "Imprimir",
            "Record a screencast": "Grabar pantalla",
        }};
        function traducirMenu() {{
            document.querySelectorAll('[data-testid="stMainMenuPopover"] *, [data-testid="stToolbar"] *').forEach(function(el) {{
                if (el.childElementCount === 0 && el.textContent) {{
                    const texto = el.textContent.trim();
                    if (traducciones[texto]) el.textContent = traducciones[texto];
                }}
            }});
        }}
        traducirMenu();
        new MutationObserver(traducirMenu).observe(document.body, {{ childList: true, subtree: true }});
    }})();
    </script>
    """
    st.markdown(css, unsafe_allow_html=True)


def theme_selector_widget():
    init_theme_state()
    st.markdown('<div class="nav-section-title">Apariencia</div>', unsafe_allow_html=True)
    paleta = st.selectbox(
        "Tema de color",
        list(PALETAS.keys()),
        index=list(PALETAS.keys()).index(st.session_state.paleta),
        key="select_paleta",
    )
    if paleta != st.session_state.paleta:
        st.session_state.paleta = paleta
        st.rerun()

    with st.expander("Menú superior (⋮) — guía rápida", expanded=False):
        st.markdown(
            """
**Limpiar caché:** borra datos temporales de la app y la recarga desde cero.
Usalo si ves pantallas desactualizadas o comportamientos raros después de cambios.

**Recargar app:** vuelve a ejecutar la aplicación sin borrar tus datos de ventas e inventario.

**Publicar (Deploy):** opción avanzada de Streamlit para subir la app a internet. No es necesaria para el uso diario del kiosco.
            """
        )


def formato_moneda(valor):
    try:
        valor = float(valor)
    except (TypeError, ValueError):
        valor = 0.0
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"$ {texto}"


def kpi_card(label, valor, es_moneda=True, accent=False):
    valor_fmt = formato_moneda(valor) if es_moneda else f"{valor:,.0f}".replace(",", ".")
    clase_valor = "kpi-value kpi-accent" if accent else "kpi-value"
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">{label}</div><div class="{clase_valor}">{valor_fmt}</div></div>', unsafe_allow_html=True)


def notificaciones_panel(notificaciones, on_clear_callback_key="btn_limpiar_notifs"):
    cantidad = len(notificaciones)
    titulo = f"Alertas de inventario ({cantidad})" if cantidad else "Alertas de inventario"
    limpiar = False
    with st.expander(titulo, expanded=False):
        if not cantidad:
            st.caption("No hay alertas de stock pendientes.")
        else:
            for n in notificaciones:
                st.markdown(f'<div class="notif-card">{n["mensaje"]}<br><span style="opacity:.62;font-size:.75rem;">{n["fecha"]}</span></div>', unsafe_allow_html=True)
            limpiar = st.button("Limpiar alertas", key=on_clear_callback_key, use_container_width=True)
    return limpiar
