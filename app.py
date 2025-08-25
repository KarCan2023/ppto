import json
import io
from typing import List, Dict

import pandas as pd
import streamlit as st

# -------------------------
# Configuración base
# -------------------------
st.set_page_config(page_title="Lista + Presupuesto", layout="wide")

# Estilos simples (tarjetas + vista de impresión)
PRIMARY = "#0ea5e9"  # azul
COLOR_VERDE = "#16a34a"
COLOR_AMARILLO = "#ca8a04"
COLOR_ROJO = "#dc2626"
COLOR_GRIS = "#6b7280"

st.markdown(
    f"""
    <style>
    /* Tarjetas por categoría */
    .card {{
        border-left: 8px solid {PRIMARY};
        padding: 0.9rem 1rem; margin-bottom: 0.8rem;
        border-radius: 0.75rem; background: #ffffff10; backdrop-filter: blur(2px);
        box-shadow: 0 1px 2px rgb(0 0 0 / 10%);
    }}
    .card h4 {{ margin: 0 0 .25rem 0; font-size: 1.0rem; }}
    .muted {{ color: #6b7280; font-size: 0.85rem; }}
    .pill {{
        display:inline-block; padding: .15rem .5rem; border-radius: 999px; font-size: .75rem; color: white; margin-left:.5rem;
    }}
    .verde {{ background: {COLOR_VERDE}; }}
    .amarillo {{ background: {COLOR_AMARILLO}; }}
    .rojo {{ background: {COLOR_ROJO}; }}
    .gris {{ background: {COLOR_GRIS}; }}

    /* Vista de impresión */
    @media print {{
        header, footer, [data-testid="stSidebar"], button, .stToolbar, .stDeployButton {{ display: none !important; }}
        .main .block-container {{ padding-top: 0 !important; }}
        .card {{ page-break-inside: avoid; }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------
# Helpers
# -------------------------

def init_state():
    if "moneda" not in st.session_state:
        st.session_state.moneda = "COP"
    if "umbral_verde" not in st.session_state:
        st.session_state.umbral_verde = 0.8
    if "umbral_amarillo" not in st.session_state:
        st.session_state.umbral_amarillo = 1.0
    if "df_presupuesto" not in st.session_state:
        st.session_state.df_presupuesto = pd.DataFrame(
            {{
                "categoria": ["Abarrotes", "Aseo", "Hogar"],
                "presupuesto": [300000.0, 80000.0, 120000.0],
            }}
        )
    if "df_items" not in st.session_state:
        st.session_state.df_items = pd.DataFrame(
            {{
                "categoria": ["Abarrotes", "Abarrotes"],
                "item": ["Arroz 5kg", "Leche 1L"],
                "cantidad": [2, 12],
                "precio_unitario": [19000.0, 3800.0],
                "nota": ["Marca habitual", "Entera"],
                "tienda": ["Tienda A", "Mayorista"],
            }}
        )


def fmt_money(v: float, moneda: str) -> str:
    try:
        return f"{moneda} {v:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    except Exception:
        return f"{moneda} {v}"


def coerce_numeric(df: pd.DataFrame, cols: List[str]):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)


def ensure_str(df: pd.DataFrame, cols: List[str]):
    for c in cols:
        if c in df.columns:
            df[c] = df[c].astype(str).fillna("")


def semaforo(gastado: float, presupuesto: float, umbral_verde: float, umbral_amarillo: float) -> str:
    if presupuesto <= 0:
        return "gris" if gastado == 0 else "rojo"
    ratio = gastado / presupuesto
    if ratio <= umbral_verde:
        return "verde"
    elif ratio <= umbral_amarillo:
        return "amarillo"
    else:
        return "rojo"


def serialize_config() -> str:
    payload = {{
        "moneda": st.session_state.moneda,
        "umbrales": {{
            "verde": st.session_state.umbral_verde,
            "amarillo": st.session_state.umbral_amarillo,
        }},
        "presupuesto": st.session_state.df_presupuesto.fillna(0).to_dict(orient="records"),
        "items": st.session_state.df_items.fillna(0).to_dict(orient="records"),
    }}
    return json.dumps(payload, ensure_ascii=False, indent=2)


def deserialize_config(text: str) -> str:
    try:
        data = json.loads(text)
        st.session_state.moneda = data.get("moneda", st.session_state.moneda)
        um = data.get("umbrales", {{}})
        st.session_state.umbral_verde = float(um.get("verde", st.session_state.umbral_verde))
        st.session_state.umbral_amarillo = float(um.get("amarillo", st.session_state.umbral_amarillo))
        pres = pd.DataFrame(data.get("presupuesto", []))
        items = pd.DataFrame(data.get("items", []))
        expected_pres_cols = ["categoria", "presupuesto"]
        expected_item_cols = ["categoria", "item", "cantidad", "precio_unitario", "nota", "tienda"]
        # Completar columnas faltantes
        for c in expected_pres_cols:
            if c not in pres.columns:
                pres[c] = 0 if c == "presupuesto" else ""
        for c in expected_item_cols:
            if c not in items.columns:
                items[c] = 0 if c in ("cantidad", "precio_unitario") else ""
        st.session_state.df_presupuesto = pres[expected_pres_cols]
        st.session_state.df_items = items[expected_item_cols]
        return "Configuración cargada"
    except Exception as e:
        return f"Error al cargar configuración: {e}"


# -------------------------
# App
# -------------------------
init_state()

st.title("🧾 Lista de Compras + Presupuesto")
st.caption("V1 sin uploads: todo se edita dentro del sitio · Exporta/Imprime cuando quieras")

# --- Sidebar: Configuración ---
with st.sidebar:
    st.header("⚙️ Configuración")
    st.session_state.moneda = st.selectbox("Moneda", ["COP", "MXN", "USD"], index=["COP", "MXN", "USD"].index(st.session_state.moneda))
    st.write("Semáforo (relación gastado/presupuesto)")
    st.session_state.umbral_verde = st.number_input("Hasta verde", min_value=0.0, max_value=1.0, value=float(st.session_state.umbral_verde), step=0.05, help="Ej: 0.80 = 80%")
    st.session_state.umbral_amarillo = st.number_input("Hasta amarillo", min_value=float(st.session_state.umbral_verde), max_value=2.0, value=float(st.session_state.umbral_amarillo), step=0.05, help="Rojo por encima de este valor")

    st.divider()
    st.subheader("Presupuesto por categoría")
    pres_cfg = st.data_editor(
        st.session_state.df_presupuesto,
        num_rows="dynamic",
        use_container_width=True,
        column_config={{
            "categoria": st.column_config.TextColumn("Categoría", required=True),
            "presupuesto": st.column_config.NumberColumn(
                "Presupuesto", min_value=0.0, step=1000.0, format="%0.2f"
            ),
        }},
        key="editor_presupuesto",
    )
    st.session_state.df_presupuesto = pres_cfg

    st.caption("Tip: deja presupuesto en 0 si aún no lo defines")

    st.divider()
    st.subheader("Guardar / Cargar (copiar & pegar)")
    config_text = serialize_config()
    st.code(config_text, language="json")
    pasted = st.text_area("Pegar configuración aquí para cargarla", height=120)
    if st.button("Cargar configuración pegada"):
        msg = deserialize_config(pasted)
        st.success(msg) if msg.startswith("Configuración") else st.error(msg)


# --- Main: Ítems y Resumen ---
col1, col2 = st.columns([0.62, 0.38])
with col1:
    st.subheader("🛒 Ítems de la lista (editable)")

    categorias = st.session_state.df_presupuesto["categoria"].dropna().astype(str).tolist()
    if not categorias:
        categorias = ["Sin categoría"]

    items_cfg = st.data_editor(
        st.session_state.df_items,
        num_rows="dynamic",
        use_container_width=True,
        column_config={{
            "categoria": st.column_config.SelectboxColumn("Categoría", options=categorias),
            "item": st.column_config.TextColumn("Ítem", required=True),
            "cantidad": st.column_config.NumberColumn("Cantidad", min_value=0.0, step=1.0),
            "precio_unitario": st.column_config.NumberColumn("Precio unitario", min_value=0.0, step=100.0, format="%0.2f"),
            "nota": st.column_config.TextColumn("Nota"),
            "tienda": st.column_config.TextColumn("Tienda"),
        }},
        key="editor_items",
    )

    # Sanitizar y guardar
    ensure_str(items_cfg, ["categoria", "item", "nota", "tienda"])  
    coerce_numeric(items_cfg, ["cantidad", "precio_unitario"])  
    items_cfg["total"] = (items_cfg["cantidad"] * items_cfg["precio_unitario"]).fillna(0.0)
    st.session_state.df_items = items_cfg

    st.caption("El total por renglón se calcula automáticamente (cantidad × precio unitario)")

with col2:
    st.subheader("📊 Resumen por categoría")

    # Preparar data de resumen
    pres = st.session_state.df_presupuesto.copy()
    coerce_numeric(pres, ["presupuesto"])  
    pres["categoria"] = pres["categoria"].astype(str)

    items = st.session_state.df_items.copy()
    if "total" not in items.columns:
        items["total"] = items.get("cantidad", 0) * items.get("precio_unitario", 0)
    items["categoria"] = items["categoria"].astype(str)

    gastado = items.groupby("categoria")["total"].sum().reset_index().rename(columns={{"total": "gastado"}})

    resumen = pres.merge(gastado, on="categoria", how="outer").fillna({{"presupuesto": 0.0, "gastado": 0.0}})
    resumen["diferencia"] = resumen["presupuesto"] - resumen["gastado"]
    resumen["estado"] = resumen.apply(
        lambda r: semaforo(r["gastado"], r["presupuesto"], st.session_state.umbral_verde, st.session_state.umbral_amarillo), axis=1
    )
    resumen = resumen.sort_values("categoria").reset_index(drop=True)

    # Totales generales
    total_presupuesto = float(resumen["presupuesto"].sum())
    total_gastado = float(resumen["gastado"].sum())
    total_dif = total_presupuesto - total_gastado

    st.metric(
        label="Total gastado",
        value=fmt_money(total_gastado, st.session_state.moneda),
        delta=f"vs presupuesto {fmt_money(total_presupuesto, st.session_state.moneda)}",
    )

    # Tarjetas por categoría
    for _, row in resumen.iterrows():
        estado = row["estado"]
        color_class = {{
            "verde": "verde",
            "amarillo": "amarillo",
            "rojo": "rojo",
            "gris": "gris",
        }}.get(estado, "gris")
        st.markdown(
            f"""
            <div class="card" style="border-left-color: {COLOR_VERDE if estado=='verde' else COLOR_AMARILLO if estado=='amarillo' else COLOR_ROJO if estado=='rojo' else COLOR_GRIS};">
                <h4>{row['categoria']} <span class="pill {color_class}">{estado.upper()}</span></h4>
                <div class="muted">Gastado: <b>{fmt_money(float(row['gastado']), st.session_state.moneda)}</b></div>
                <div class="muted">Presupuesto: <b>{fmt_money(float(row['presupuesto']), st.session_state.moneda)}</b></div>
                <div class="muted">Diferencia: <b>{fmt_money(float(row['diferencia']), st.session_state.moneda)}</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()
    st.subheader("📥 Descargas (opcional)")

    # Exportar CSVs
    resumen_export = resumen[["categoria", "presupuesto", "gastado", "diferencia", "estado"]].copy()
    lista_export = items[["categoria", "item", "cantidad", "precio_unitario", "total", "nota", "tienda"]].copy()

    buf_resumen = io.StringIO(); resumen_export.to_csv(buf_resumen, index=False)
    buf_lista = io.StringIO(); lista_export.to_csv(buf_lista, index=False)

    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "Descargar resumen_categorias.csv",
            data=buf_resumen.getvalue().encode("utf-8"),
            file_name="resumen_categorias.csv",
            mime="text/csv",
        )
    with c2:
        st.download_button(
            "Descargar lista_detallada.csv",
            data=buf_lista.getvalue().encode("utf-8"),
            file_name="lista_detallada.csv",
            mime="text/csv",
        )

st.divider()
st.subheader("🖨️ Vista de impresión")
st.write("Activa la vista minimalista y usa **Ctrl+P** (o Comando+P en Mac) para imprimir/guardar PDF.")

# Bloque simple para minimizar elementos en pantalla durante la impresión
imprimir = st.toggle("Vista minimalista para imprimir", value=False)
if imprimir:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"], .stDownloadButton, .stTextArea, .stNumberInput, .stSelectbox, .stDataFrame, .stDataEditorRowAdd, .st-emotion-cache-ue6h4q, .stButton {display: none !important;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.info("Listo para imprimir: usa Ctrl+P / Cmd+P. (Para volver, desactiva el toggle)")
