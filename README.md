# 🧾 Lista de Compras + Presupuesto (V1 sin uploads)

Micro‑app en Streamlit para gestionar una lista de compras por categorías y comparar el gasto **vs.** presupuesto. Sin subir archivos: todo se edita en pantalla. Permite exportar CSV y una vista de impresión limpia.

## ✨ Características
- Tabla **editable** de presupuesto por categoría.
- Lista de ítems editable (cantidad × precio unitario → total por renglón).
- Resumen por categoría con **semáforo** (configurable): verde / amarillo / rojo.
- Total general y diferencia vs. presupuesto.
- **Copiar/Pegar configuración** (JSON legible) para guardar/recuperar sin archivos.
- **Descarga** opcional de CSV (resumen e ítems).
- **Vista de impresión** minimalista (usa Ctrl+P / Cmd+P).

## 🚀 Cómo correr localmente
```bash
# 1) Clona el repo
git clone https://github.com/<tu-usuario>/lista-compras-presupuesto.git
cd lista-compras-presupuesto

# 2) Crea tu entorno e instala dependencias
pip install -r requirements.txt

# 3) Inicia la app
streamlit run app.py
