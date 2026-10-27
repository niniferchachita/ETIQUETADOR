import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from barcode import EAN13
from barcode.writer import ImageWriter
import io
import math
import time

st.set_page_config(page_title="Etiquetador Master Web", page_icon="🏷️", layout="wide")

st.title("🏷️ ETIQUETADOR MASTER - Impresión A4")

# Variables y funciones de diseño
def generar_codigo_unico_ean12():
    timestamp = str(int(time.time() * 1000000))
    return "775" + timestamp[-9:]

def procesar_etiqueta_final(codigo, nombre, precio, logo_img=None, es_promo=False, porcentaje_desc=20.0, ocultar_codigo=False, tienda="MI TIENDA"):
    ANCHO_FIJO = 425
    ALTO_FIJO = 260
    etiqueta = Image.new("RGB", (ANCHO_FIJO, ALTO_FIJO), "white")
    draw = ImageDraw.Draw(etiqueta)

    try:
        fuente_tienda = ImageFont.truetype("arialbd.ttf", 16)
        fuente_producto = ImageFont.truetype("arialbd.ttf", 18)
        fuente_precio = ImageFont.truetype("arialbd.ttf", 34 if ocultar_codigo else 26)
        fuente_promo_ant = ImageFont.truetype("arial.ttf", 13)
        fuente_badge = ImageFont.truetype("arialbd.ttf", 12)
        fuente_codigo = ImageFont.truetype("arialbd.ttf", 12)
    except Exception:
        fuente_tienda = fuente_producto = fuente_precio = fuente_promo_ant = fuente_badge = fuente_codigo = ImageFont.load_default()

    y_encabezado = 4
    ancho_logo_real = 0
    tiene_logo = False

    if logo_img:
        logo_copy = logo_img.copy().convert("RGBA")
        logo_copy.thumbnail((110, 45), Image.Resampling.LANCZOS)
        ancho_logo_real = logo_copy.size[0]
        pos_y_logo = max(1, y_encabezado + (24 - logo_copy.size[1]) // 2)
        etiqueta.paste(logo_copy, (10, pos_y_logo), logo_copy)
        tiene_logo = True

    texto_tienda = (tienda or "MI TIENDA").strip().upper()
    try:
        tw_t = draw.textlength(texto_tienda, font=fuente_tienda)
    except Exception:
        tw_t = len(texto_tienda) * 8

    pos_x_tienda = (14 + ancho_logo_real) if tiene_logo else (ANCHO_FIJO - tw_t) // 2
    draw.text((pos_x_tienda, y_encabezado + 2), texto_tienda, fill="black", font=fuente_tienda)

    nombre_prod = str(nombre).upper()
    if len(nombre_prod) > 24:
        nombre_prod = nombre_prod[:21] + "..."
    try:
        tw_prod = draw.textlength(nombre_prod, font=fuente_producto)
        pos_x_prod = (ANCHO_FIJO - tw_prod) // 2
    except Exception:
        pos_x_prod = (ANCHO_FIJO - (len(nombre_prod) * 10)) // 2

    draw.text((pos_x_prod, 32), nombre_prod, fill="black", font=fuente_producto)

    y_seccion_precio = 56 if not ocultar_codigo else 90
    try:
        val_precio = float(str(precio).replace('$', '').replace(',', '.'))
    except ValueError:
        val_precio = 0.0

    if es_promo:
        val_anterior = val_precio / (1 - (porcentaje_desc / 100))
        txt_ant = f"Antes: ${val_anterior:.2f}"
        txt_badge = f"-{int(porcentaje_desc)}%"
        txt_oferta = f"OFERTA: ${val_precio:.2f}"
        try:
            tw_ant = draw.textlength(txt_ant, font=fuente_promo_ant)
            x_ant = (ANCHO_FIJO // 2) - tw_ant - 10
        except Exception:
            x_ant = 90

        draw.text((x_ant, y_seccion_precio), txt_ant, fill="black", font=fuente_promo_ant)
        draw.line((x_ant, y_seccion_precio + 7, x_ant + tw_ant, y_seccion_precio + 7), fill="black", width=2)
        x_badge = (ANCHO_FIJO // 2) + 10
        draw.rectangle((x_badge, y_seccion_precio - 2, x_badge + 46, y_seccion_precio + 14), fill="black")
        draw.text((x_badge + 4, y_seccion_precio - 1), txt_badge, fill="white", font=fuente_badge)
        texto_final = txt_oferta
        y_precio_final = y_seccion_precio + 16 if not ocultar_codigo else y_seccion_precio + 26
    else:
        texto_final = f"${val_precio:.2f}"
        y_precio_final = y_seccion_precio if not ocultar_codigo else y_seccion_precio + 8

    try:
        tw_p = draw.textlength(texto_final, font=fuente_precio)
        pos_x_precio = (ANCHO_FIJO - tw_p) // 2
    except Exception:
        pos_x_precio = 100
    draw.text((pos_x_precio, y_precio_final), texto_final, fill="black", font=fuente_precio)

    if not ocultar_codigo:
        cod_str = ''.join(filter(str.isdigit, str(codigo or '')))
        if len(cod_str) < 12:
            cod_limpio = generar_codigo_unico_ean12()
        else:
            cod_limpio = cod_str[:12]

        fp = io.BytesIO()
        ean = EAN13(cod_limpio, writer=ImageWriter())
        ean.write(fp, options={"write_text": False, "module_height": 6.5 if es_promo else 7.8, "module_width": 0.36, "quiet_zone": 0.0})
        fp.seek(0)
        img_bc = Image.open(fp)
        pos_x_bc = (ANCHO_FIJO - img_bc.size[0]) // 2
        y_bc = 118 if es_promo else 105
        etiqueta.paste(img_bc, (pos_x_bc, y_bc))

        cod_completo = ean.get_fullcode()
        try:
            tw_c = draw.textlength(cod_completo, font=fuente_codigo)
            pos_x_c = (ANCHO_FIJO - tw_c) // 2
        except Exception:
            pos_x_c = 150
        draw.text((pos_x_c, y_bc + img_bc.size[1] + 1), cod_completo, fill="black", font=fuente_codigo)

    return etiqueta

def generar_paginas_a4(etiquetas):
    ANCHO_A4, ALTO_A4 = 2480, 3508
    ANCHO_L, ALTO_L = 425, 260
    COLS, FILAS = 5, 12
    POR_HOJA = COLS * FILAS
    SP_X, SP_Y = 14, 12
    MG_X = (ANCHO_A4 - (COLS * ANCHO_L) - ((COLS - 1) * SP_X)) // 2
    MG_Y = (ALTO_A4 - (FILAS * ALTO_L) - ((FILAS - 1) * SP_Y)) // 2

    paginas = []
    total = len(etiquetas)
    num_pags = math.ceil(total / POR_HOJA)

    for p in range(num_pags):
        hoja = Image.new("RGB", (ANCHO_A4, ALTO_A4), "white")
        draw = ImageDraw.Draw(hoja)
        grupo = etiquetas[p * POR_HOJA : (p + 1) * POR_HOJA]
        for i, img in enumerate(grupo):
            c, r = i % COLS, i // COLS
            x = MG_X + c * (ANCHO_L + SP_X)
            y = MG_Y + r * (ALTO_L + SP_Y)
            hoja.paste(img.resize((ANCHO_L, ALTO_L), Image.Resampling.LANCZOS), (x, y))
            draw.rectangle([x, y, x + ANCHO_L, y + ALTO_L], outline="#dcdde1", width=1)
        paginas.append(hoja)
    return paginas

# Interfaz Web
col_izq, col_der = st.columns([1, 2])

with col_izq:
    st.subheader("⚙️ Configuración")
    tienda = st.text_input("Nombre de la Tienda", value="COMERCIAL EL COBRE")
    archivo_logo = st.file_uploader("Subir Logotipo", type=["png", "jpg", "jpeg"])
    logo_img = Image.open(archivo_logo) if archivo_logo else None

    st.markdown("---")
    modo = st.radio("Modo de trabajo", ["Etiqueta Individual", "Lote Masivo por Excel"])

    etiquetas_finales = []

    if modo == "Etiqueta Individual":
        nombre = st.text_input("Nombre / Descripción")
        precio = st.text_input("Precio ($)", value="10.00")
        codigo = st.text_input("Código de barras (Opcional, 12 dígitos)")
        copias = st.number_input("Cantidad de Copias", min_value=1, value=1, step=1)
        sin_codigo = st.checkbox("🚫 Ocultar Código de barras")
        es_promo = st.checkbox("🔥 Activar Promoción")
        descuento = st.slider("Descuento (%)", 5, 90, 20) if es_promo else 20.0

        if st.button("Generar Planilla A4"):
            if nombre and precio:
                img_etiq = procesar_etiqueta_final(codigo, nombre, precio, logo_img, es_promo, descuento, sin_codigo, tienda)
                etiquetas_finales = [img_etiq] * copias
            else:
                st.warning("Completa el nombre y el precio.")

    else:
        archivo_excel = st.file_uploader("Subir archivo Excel (.xlsx)", type=["xlsx"])
        if archivo_excel and st.button("Procesar Excel"):
            df = pd.read_excel(archivo_excel)
            # Normalizar columnas
            cols = {str(c).strip().lower(): c for c in df.columns}
            col_nom = next((cols[k] for k in cols if k in ['producto', 'articulo', 'nombre']), None)
            col_pre = next((cols[k] for k in cols if k in ['precio', 'precio de venta', 'costo']), None)
            col_cod = next((cols[k] for k in cols if k in ['codigo', 'codigo de barras', 'ean']), None)
            col_cant = next((cols[k] for k in cols if k in ['cantidad', 'copias', 'cant']), None)

            if col_nom and col_pre:
                for _, fila in df.iterrows():
                    nom = fila[col_nom]
                    pre = fila[col_pre]
                    if pd.isna(nom) or pd.isna(pre):
                        continue
                    cod = fila[col_cod] if col_cod and not pd.isna(fila[col_cod]) else None
                    cant = int(fila[col_cant]) if col_cant and not pd.isna(fila[col_cant]) else 1
                    img_etiq = procesar_etiqueta_final(cod, nom, pre, logo_img=logo_img, tienda=tienda)
                    etiquetas_finales.extend([img_etiq] * cant)
            else:
                st.error("El Excel debe tener columnas 'Nombre' y 'Precio'.")

with col_der:
    st.subheader("📄 Vista Previa y Descarga de Planillas")
    if etiquetas_finales:
        hojas = generar_paginas_a4(etiquetas_finales)
        st.success(f"Se generaron {len(etiquetas_finales)} etiquetas en {len(hojas)} página(s) A4.")

        for idx, hoja in enumerate(hojas):
            st.write(f"**Página {idx + 1}**")
            st.image(hoja, use_container_width=True)
            buf = io.BytesIO()
            hoja.save(buf, format="PNG")
            st.download_button(
                label=f"⬇️ Descargar Página {idx + 1} (PNG)",
                data=buf.getvalue(),
                file_name=f"Planilla_A4_Pagina_{idx + 1}.png",
                mime="image/png"
            )