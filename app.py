import os
import io
import time
import sys
import math
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from barcode import EAN13
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont, ImageTk

# === ENLACE FORZADO DE IMPRESIÓN PARA COMPATIBILIDAD 64-BIT ===
SISTEMA_IMPRESION = False
try:
    import win32print
    import win32ui
    import win32con
    import openpyxl
    import pandas as pd
    SISTEMA_IMPRESION = True
except ImportError:
    ruta_usuario_313 = os.path.expandvars(r"%LOCALAPPDATA%\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\site-packages")
    sys.path.append(ruta_usuario_313)
    pywin32_dlls = os.path.join(ruta_usuario_313, "pywin32_system32")
    if os.path.exists(pywin32_dlls):
        os.environ["PATH"] = pywin32_dlls + os.pathsep + os.environ["PATH"]
        if hasattr(os, 'add_dll_directory'):
            try: 
                os.add_dll_directory(pywin32_dlls)
            except Exception: 
                pass
    try:
        import win32print
        import win32ui
        import win32con
        import openpyxl
        import pandas as pd
        SISTEMA_IMPRESION = True
    except ImportError:
        SISTEMA_IMPRESION = False

ruta_logo_global = ""

def obtener_ruta_escritorio():
    escritorio = os.path.join(os.path.expanduser('~'), 'Desktop')
    if not os.path.exists(escritorio):
        escritorio = os.path.join(os.path.expanduser('~'), 'Escritorio')
    carpeta_etiquetas = os.path.join(escritorio, 'Mis_Etiquetas_Impresion')
    if not os.path.exists(carpeta_etiquetas):
        os.makedirs(carpeta_etiquetas)
    return carpeta_etiquetas

def obtener_impresoras():
    if not SISTEMA_IMPRESION:
        return ["Impresión deshabilitada (Usa Python 3.13 de 64 bits)"]
    try:
        impresoras = [imp[2] for imp in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
        return impresoras if impresoras else ["No se detectaron impresoras físicas"]
    except Exception:
        return ["Error al listar el hardware de impresión"]

def mandar_a_imprimir_directo(ruta_imagen, nombre_impresora, copias=1):
    if not SISTEMA_IMPRESION or "deshabilitada" in nombre_impresora or "No se detectaron" in nombre_impresora:
        return False
    try:
        for _ in range(copias):
            hDC = win32ui.CreateDC()
            hDC.CreatePrinterDC(nombre_impresora)
            hDC.StartDoc(os.path.basename(ruta_imagen))
            hDC.StartPage()
            anchura_printable = hDC.GetDeviceCaps(win32con.HORZRES)
            altura_printable = hDC.GetDeviceCaps(win32con.VERTRES)
            win32image = Image.open(ruta_imagen).convert("RGB")
            from PIL import ImageWin
            dibujo_pantalla = ImageWin.Dib(win32image)
            dibujo_pantalla.draw(hDC.GetHandleOutput(), (0, 0, anchura_printable, altura_printable))
            hDC.EndPage()
            hDC.EndDoc()
            del hDC
        return True
    except Exception as e:
        print(f"Error de hardware en la impresora: {e}")
        return False

def generar_codigo_unico_ean12():
    timestamp = str(int(time.time() * 1000000))
    codigo_12_digitos = "775" + timestamp[-9:]
    return codigo_12_digitos

def seleccionar_logo():
    global ruta_logo_global
    archivo = filedialog.askopenfilename(
        title="Selecciona el logo de la empresa",
        filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp")]
    )
    if archivo:
        ruta_logo_global = archivo
        nombre_archivo = os.path.basename(archivo)
        lbl_status_logo.config(text=f" Logo cargado: {nombre_archivo}", foreground="#27ae60")
    else:
        ruta_logo_global = ""
        lbl_status_logo.config(text="⚠️ Sin logo (Se usará solo texto)", foreground="#7f8c8d")

def procesar_etiqueta_final(codigo, nombre, precio, es_promo_override=None, descuento_override=None, ocultar_codigo_override=None):
    ocultar_codigo = var_sin_codigo.get() if ocultar_codigo_override is None else ocultar_codigo_override
    es_promo = var_es_promo.get() if es_promo_override is None else es_promo_override

    ANCHO_FIJO = 425
    ALTO_FIJO = 260
    etiqueta_final = Image.new("RGB", (ANCHO_FIJO, ALTO_FIJO), "white")
    draw = ImageDraw.Draw(etiqueta_final)
    
    windir = os.environ.get('SystemRoot', 'C:\\Windows')
    ruta_fuentes = os.path.join(windir, 'Fonts')
    
    try:
        fuente_tienda = ImageFont.truetype(os.path.join(ruta_fuentes, "arialbd.ttf"), 16) 
        fuente_producto = ImageFont.truetype(os.path.join(ruta_fuentes, "arialbd.ttf"), 18) 
        fuente_precio = ImageFont.truetype(os.path.join(ruta_fuentes, "arialbd.ttf"), 34 if ocultar_codigo else 26) 
        fuente_promo_ant = ImageFont.truetype(os.path.join(ruta_fuentes, "arial.ttf"), 13)
        fuente_badge = ImageFont.truetype(os.path.join(ruta_fuentes, "arialbd.ttf"), 12)
        fuente_codigo = ImageFont.truetype(os.path.join(ruta_fuentes, "arialbd.ttf"), 12)
    except Exception:
        fuente_tienda = ImageFont.load_default()
        fuente_producto = ImageFont.load_default()
        fuente_precio = ImageFont.load_default()
        fuente_promo_ant = ImageFont.load_default()
        fuente_badge = ImageFont.load_default()
        fuente_codigo = ImageFont.load_default()

    y_encabezado = 4
    tiene_logo = False
    ancho_logo_real = 0
    
    if ruta_logo_global and os.path.exists(ruta_logo_global):
        try:
            img_logo = Image.open(ruta_logo_global).convert("RGBA")
            img_logo.thumbnail((110, 45), Image.Resampling.LANCZOS)
            ancho_logo_real = img_logo.size[0]
            pos_y_logo = y_encabezado + (24 - img_logo.size[1]) // 2
            etiqueta_final.paste(img_logo, (10, pos_y_logo if pos_y_logo > 1 else 1), img_logo)
            tiene_logo = True
        except Exception as e:
            print(f"Error al cargar el logo: {e}")

    texto_tienda = entry_tienda.get().strip().upper()
    if not texto_tienda: 
        texto_tienda = "MI TIENDA"

    try:
        tw_t = draw.textlength(texto_tienda, font=fuente_tienda)
    except Exception:
        tw_t = len(texto_tienda) * 8

    if tiene_logo:
        pos_x_tienda = 14 + ancho_logo_real
        if pos_x_tienda + tw_t > ANCHO_FIJO - 8:
            texto_tienda = texto_tienda[:10] + "..."
    else:
        pos_x_tienda = (ANCHO_FIJO - tw_t) // 2

    draw.text((pos_x_tienda, y_encabezado + 2), texto_tienda, fill="black", font=fuente_tienda) 

    y_producto = 32
    if len(nombre) > 24: 
        nombre = nombre[:21] + "..."
    texto_producto = str(nombre).upper()
    
    try:
        tw_prod = draw.textlength(texto_producto, font=fuente_producto)
        pos_x_prod = (ANCHO_FIJO - tw_prod) // 2
    except Exception:
        pos_x_prod = (ANCHO_FIJO - (len(texto_producto) * 10)) // 2
    
    draw.text((pos_x_prod, y_producto), texto_producto, fill="black", font=fuente_producto) 
    
    y_seccion_precio = 56 if not ocultar_codigo else 90
    try:
        val_precio_actual = float(precio)
    except ValueError:
        val_precio_actual = 0.0

    if es_promo:
        porcentaje_desc = descuento_override if descuento_override is not None else 20.0
        if descuento_override is None:
            try:
                porcentaje_desc = float(entry_descuento.get().strip().replace('%', ''))
                if porcentaje_desc <= 0 or porcentaje_desc >= 100: 
                    porcentaje_desc = 20.0
            except ValueError:
                porcentaje_desc = 20.0
        
        val_precio_anterior = val_precio_actual / (1 - (porcentaje_desc / 100))
        texto_ant_str = f"Antes: ${val_precio_anterior:.2f}"
        texto_badge_str = f"-{int(porcentaje_desc)}%"
        texto_precio_oferta = f"OFERTA: ${val_precio_actual:.2f}"

        try:
            tw_ant = draw.textlength(texto_ant_str, font=fuente_promo_ant)
            x_ant = (ANCHO_FIJO // 2) - tw_ant - 10
        except Exception:
            x_ant = 90
        
        draw.text((x_ant, y_seccion_precio), texto_ant_str, fill="black", font=fuente_promo_ant)
        draw.line((x_ant, y_seccion_precio + 7, x_ant + tw_ant, y_seccion_precio + 7), fill="black", width=2)

        x_badge = (ANCHO_FIJO // 2) + 10
        draw.rectangle((x_badge, y_seccion_precio - 2, x_badge + 46, y_seccion_precio + 14), fill="black")
        draw.text((x_badge + 4, y_seccion_precio - 1), texto_badge_str, fill="white", font=fuente_badge)

        texto_final_render = texto_precio_oferta
        y_precio_final = y_seccion_precio + 16 if not ocultar_codigo else y_seccion_precio + 26
    else:
        texto_final_render = f"${precio}"
        y_precio_final = y_seccion_precio if not ocultar_codigo else y_seccion_precio + 8

    try:
        tw_p = draw.textlength(texto_final_render, font=fuente_precio)
        pos_x_precio = (ANCHO_FIJO - tw_p) // 2
    except Exception:
        pos_x_precio = (ANCHO_FIJO - (len(texto_final_render) * 13) // 2)

    draw.text((pos_x_precio, y_precio_final), texto_final_render, fill="black", font=fuente_precio)

    if not ocultar_codigo:
        if codigo is None or codigo == "" or pd.isna(codigo):
            codigo_limpio = generar_codigo_unico_ean12()
        else:
            codigo_str = str(codigo).split('.')[0].strip()
            codigo_limpio = ''.join(filter(str.isdigit, codigo_str))
            if len(codigo_limpio) < 12: 
                codigo_limpio = codigo_limpio.zfill(12)
            elif len(codigo_limpio) > 12: 
                codigo_limpio = codigo_limpio[:12]

        writer_options = {
            "write_text": False, 
            "module_height": 6.5 if es_promo else 7.8, 
            "module_width": 0.36, 
            "quiet_zone": 0.0      
        }
        
        fp = io.BytesIO()
        ean = EAN13(codigo_limpio, writer=ImageWriter())
        ean.write(fp, options=writer_options)
        
        codigo_barras_final = ean.get_fullcode()
        fp.seek(0) 
        img_barcode = Image.open(fp)
        
        pos_x_barcode = (ANCHO_FIJO - img_barcode.size[0]) // 2
        y_barcode_pos = 118 if es_promo else 105
        etiqueta_final.paste(img_barcode, (pos_x_barcode, y_barcode_pos))

        texto_codigo = str(codigo_barras_final)
        try:
            tw_cod = draw.textlength(texto_codigo, font=fuente_codigo)
            pos_x_codigo = (ANCHO_FIJO - tw_cod) // 2
        except Exception:
            pos_x_codigo = (ANCHO_FIJO - (len(texto_codigo) * 6)) // 2
        
        y_texto_codigo = y_barcode_pos + img_barcode.size[1] + 1
        draw.text((pos_x_codigo, y_texto_codigo), texto_codigo, fill="black", font=fuente_codigo)
        img_barcode.close()
        fp.close()

    return etiqueta_final

def generar_paginas_a4(lista_imagenes_etiquetas):
    ANCHO_A4 = 2480  
    ALTO_A4 = 3508   
    ANCHO_LABEL = 425
    ALTO_LABEL = 260
    COLUMNAS = 5
    FILAS = 12
    ETIQUETAS_POR_PAGINA = COLUMNAS * FILAS

    SPACING_X = 14
    SPACING_Y = 12
    
    MARGIN_X = (ANCHO_A4 - (COLUMNAS * ANCHO_LABEL) - ((COLUMNAS - 1) * SPACING_X)) // 2
    MARGIN_Y = (ALTO_A4 - (FILAS * ALTO_LABEL) - ((FILAS - 1) * SPACING_Y)) // 2

    paginas = []
    total_etiquetas = len(lista_imagenes_etiquetas)
    num_paginas = math.ceil(total_etiquetas / ETIQUETAS_POR_PAGINA)

    for p in range(num_paginas):
        hoja_a4 = Image.new("RGB", (ANCHO_A4, ALTO_A4), "white")
        draw = ImageDraw.Draw(hoja_a4)
        etiquetas_subconjunto = lista_imagenes_etiquetas[p * ETIQUETAS_POR_PAGINA : (p + 1) * ETIQUETAS_POR_PAGINA]

        for i, img_etiq in enumerate(etiquetas_subconjunto):
            col = i % COLUMNAS
            row = i // COLUMNAS
            pos_x = MARGIN_X + col * (ANCHO_LABEL + SPACING_X)
            pos_y = MARGIN_Y + row * (ALTO_LABEL + SPACING_Y)

            img_resized = img_etiq.resize((ANCHO_LABEL, ALTO_LABEL), Image.Resampling.LANCZOS)
            hoja_a4.paste(img_resized, (pos_x, pos_y))
            draw.rectangle([pos_x, pos_y, pos_x + ANCHO_LABEL, pos_y + ALTO_LABEL], outline="#dcdde1", width=1)

        paginas.append(hoja_a4)

    return paginas

def generar_masivo_excel():
    archivo_ruta_raw = filedialog.askopenfilename(title="Selecciona tu archivo de Excel", filetypes=[("Archivos de Excel", "*.xlsx")])
    if not archivo_ruta_raw: 
        return
        
    archivo_ruta = os.path.abspath(archivo_ruta_raw)
    try:
        with open(archivo_ruta, 'rb') as f:
            contenido_binario = io.BytesIO(f.read())
            df = pd.read_excel(contenido_binario, engine='openpyxl')
        
        if df.empty:
            messagebox.showerror("Error", "El archivo de Excel seleccionado está vacío.")
            return

        columnas_originales = df.columns.tolist()
        columnas_limpias = [
            str(c).strip().lower().replace('ó', 'o').replace('é', 'e').replace('á', 'a').replace('í', 'i') 
            for c in columnas_originales
        ]
        
        mapeo = {}
        for col_orig, col_limpia in zip(columnas_originales, columnas_limpias):
            if col_limpia in ['codigo de barras', 'cod', 'codigo', 'ean']: 
                mapeo['codigo'] = col_orig
            elif col_limpia in ['producto', 'articulo', 'nombre', 'detalles', 'descripcion']: 
                mapeo['nombre'] = col_orig
            elif col_limpia in ['costo', 'precio de venta', 'precio', 'p. venta']: 
                mapeo['precio'] = col_orig
            elif col_limpia in ['cantidad', 'copias', 'cant', 'stock']: 
                mapeo['cantidad'] = col_orig
            elif col_limpia in ['descuento', 'desc', 'promo', 'porcentaje']: 
                mapeo['descuento'] = col_orig
            elif col_limpia in ['sin codigo', 'ocultar codigo', 'sin_codigo', 'no_codigo']: 
                mapeo['sin_codigo'] = col_orig

        if 'nombre' not in mapeo or 'precio' not in mapeo:
            messagebox.showerror("Error de Columnas", "El archivo debe contener al menos las columnas:\n'Nombre' y 'Precio'.")
            return

        coleccion_etiquetas = []

        for index, fila in df.iterrows():
            nombre_raw = fila.get(mapeo['nombre'])
            precio_raw = fila.get(mapeo['precio'])
            if pd.isna(nombre_raw) or pd.isna(precio_raw): 
                continue
            
            nombre = str(nombre_raw).strip()
            codigo = None
            if 'codigo' in mapeo:
                cod_val = fila.get(mapeo['codigo'])
                if not pd.isna(cod_val) and str(cod_val).strip() != "":
                    codigo = str(cod_val).strip()

            ocultar_cod = False
            if 'sin_codigo' in mapeo:
                val_sin_cod = str(fila.get(mapeo['sin_codigo'])).strip().lower()
                ocultar_cod = val_sin_cod in ['si', 's', 'true', '1', 'yes']
            elif codigo is None:
                ocultar_cod = True

            es_promo_fila = False
            desc_fila = None
            if 'descuento' in mapeo:
                val_desc = fila.get(mapeo['descuento'])
                if not pd.isna(val_desc):
                    try:
                        desc_limpio = float(str(val_desc).replace('%', '').replace(',', '.').strip())
                        if desc_limpio > 0:
                            es_promo_fila = True
                            desc_fila = desc_limpio
                    except ValueError:
                        pass

            cant_copias = 1
            if 'cantidad' in mapeo:
                try:
                    cant_val = int(fila.get(mapeo['cantidad']))
                    if cant_val > 0: 
                        cant_copias = cant_val
                except (ValueError, TypeError):
                    cant_copias = 1

            try:
                precio_limpio = str(precio_raw).replace('$', '').replace(',', '.').strip()
                precio = f"{float(precio_limpio):.2f}"
            except ValueError:
                precio = str(precio_raw).strip()

            if nombre and precio:
                img_etiq = procesar_etiqueta_final(
                    codigo=codigo, 
                    nombre=nombre, 
                    precio=precio,
                    es_promo_override=es_promo_fila,
                    descuento_override=desc_fila,
                    ocultar_codigo_override=ocultar_cod
                )
                for _ in range(cant_copias):
                    coleccion_etiquetas.append(img_etiq)

        if not coleccion_etiquetas:
            messagebox.showwarning("Atención", "No se encontraron filas válidas para procesar.")
            return

        hojas_a4 = generar_paginas_a4(coleccion_etiquetas)
        carpeta_destino = obtener_ruta_escritorio()
        impresora_destino = combo_impresoras.get()
        
        archivos_guardados = []
        for idx, hoja in enumerate(hojas_a4):
            ruta_a4 = os.path.join(carpeta_destino, f"Planilla_A4_Pagina_{idx + 1}_{int(time.time())}.png")
            hoja.save(ruta_a4, "PNG")
            archivos_guardados.append(ruta_a4)

            if SISTEMA_IMPRESION and "deshabilitada" not in impresora_destino and "No se detectaron" not in impresora_destino:
                mandar_a_imprimir_directo(ruta_a4, impresora_destino, copias=1)

        messagebox.showinfo("Proceso Completado 🚀", f"Se procesaron {len(coleccion_etiquetas)} etiquetas en total.\nSe generaron {len(hojas_a4)} página(s) A4 en:\n'Mis_Etiquetas_Impresion'.")
    except Exception as e:
        messagebox.showerror("Error al procesar", f"No se pudo procesar el archivo Excel:\n{str(e)}")

def limpiar_formulario():
    entry_nombre.delete(0, tk.END)
    entry_precio.delete(0, tk.END)
    entry_codigo.delete(0, tk.END)
    entry_copias.delete(0, tk.END)
    entry_copias.insert(0, "1")
    if var_es_promo.get():
        entry_descuento.delete(0, tk.END)
        entry_descuento.insert(0, "20")
    entry_nombre.focus()

def ejecutar_accion_individual(solo_guardar=False):
    nombre = entry_nombre.get().strip()
    precio = entry_precio.get().strip()
    codigo_manual = entry_codigo.get().strip()
    
    if not nombre or not precio:
        messagebox.showerror("Campos Incompletos", "Por favor, ingresa el Nombre y el Precio del producto.")
        return

    if not var_sin_codigo.get() and codigo_manual and len(''.join(filter(str.isdigit, codigo_manual))) not in [12, 13]:
        messagebox.showwarning("Código Inválido", "El código manual debe contener exactamente 12 o 13 dígitos numéricos.")
        return

    try:
        cant_copias = int(entry_copias.get().strip())
        if cant_copias < 1: 
            cant_copias = 1
    except ValueError:
        cant_copias = 1

    try:
        try:
            precio_limpio = precio.replace('$', '').replace(',', '.').strip()
            precio_formateado = f"{float(precio_limpio):.2f}"
        except ValueError:
            precio_formateado = precio

        img_etiqueta = procesar_etiqueta_final(codigo_manual if codigo_manual else None, nombre, precio_formateado)
        lista_repetida = [img_etiqueta] * cant_copias
        hojas_a4 = generar_paginas_a4(lista_repetida)
        
        carpeta_destino = obtener_ruta_escritorio()
        impresora_destino = combo_impresoras.get()
        impreso_ok = False

        for idx, hoja in enumerate(hojas_a4):
            ruta_a4 = os.path.join(carpeta_destino, f"Etiqueta_A4_Pagina_{idx+1}_{int(time.time())}.png")
            hoja.save(ruta_a4, "PNG")

            if not solo_guardar and SISTEMA_IMPRESION and "deshabilitada" not in impresora_destino and "No se detectaron" not in impresora_destino:
                impreso_ok = mandar_a_imprimir_directo(ruta_a4, impresora_destino, 1)

        if solo_guardar:
            messagebox.showinfo("💾 Guardado", f"Etiquetas organizadas en {len(hojas_a4)} página(s) A4 en 'Mis_Etiquetas_Impresion'.")
            limpiar_formulario()
            return

        if impreso_ok:
            messagebox.showinfo("🖨️ Impresión Exitosa", f"Enviadas {len(hojas_a4)} página(s) A4 a la impresora {impresora_destino}.")
            limpiar_formulario()
        else:
            messagebox.showinfo("💾 Archivo Guardado", f"Página(s) A4 guardadas en el Escritorio en 'Mis_Etiquetas_Impresion'.")
    except Exception as e:
        messagebox.showerror("Error General", f"No se pudo procesar la solicitud:\n{str(e)}")

# =============================================================================
# --- MOTOR DE TEMAS DINÁMICOS (OSCURO / CLARO) ---
# =============================================================================
TEMAS = {
    "claro": {
        "bg_root": "#f4f6f9",
        "fg_main": "#2c3e50",
        "fg_title": "#1a252f",
        "fg_subtitle": "#495057",
        "bg_entry": "#ffffff",
        "fg_entry": "#2c3e50",
        "bg_entry_disabled": "#e9ecef",
        "fg_entry_disabled": "#7f8c8d",
        "border_entry": "#ced4da",
        "bg_sep": "#dee2e6",
        "bg_btn_secondary": "#e9ecef",
        "fg_btn_secondary": "#d35400",
        "bg_btn_gray": "#6c757d",
        "fg_btn_gray": "#ffffff",
        "bg_btn_print": "#2980b9",
        "fg_btn_print": "#ffffff",
        "bg_btn_excel": "#27ae60",
        "fg_btn_excel": "#ffffff",
        "btn_theme_bg": "#ffffff",
        "btn_theme_fg": "#2c3e50",
        "btn_theme_text": "🌙 Modo Oscuro"
    },
    "oscuro": {
        "bg_root": "#1a252f",
        "fg_main": "#ecf0f1",
        "fg_title": "#f1c40f",
        "fg_subtitle": "#bdc3c7",
        "bg_entry": "#2c3e50",
        "fg_entry": "#ffffff",
        "bg_entry_disabled": "#1a252f",
        "fg_entry_disabled": "#7f8c8d",
        "border_entry": "#34495e",
        "bg_sep": "#2c3e50",
        "bg_btn_secondary": "#34495e",
        "fg_btn_secondary": "#f39c12",
        "bg_btn_gray": "#34495e",
        "fg_btn_gray": "#eeeeee",
        "bg_btn_print": "#2c3e50",
        "fg_btn_print": "#f1c40f",
        "bg_btn_excel": "#2c3e50",
        "fg_btn_excel": "#2ecc71",
        "btn_theme_bg": "#2c3e50",
        "btn_theme_fg": "#ffffff",
        "btn_theme_text": "☀️ Modo Claro"
    }
}

tema_actual = "claro"

def aplicar_tema(nombre_tema):
    c = TEMAS[nombre_tema]
    root.configure(bg=c["bg_root"])
    
    style.configure('.', background=c["bg_root"], foreground=c["fg_main"])
    style.configure('TLabel', background=c["bg_root"], foreground=c["fg_main"])
    style.configure('TCombobox', 
                    fieldbackground=c["bg_entry"], 
                    background=c["bg_entry"], 
                    foreground=c["fg_entry"], 
                    arrowcolor=c["fg_entry"])
    style.map('TCombobox', 
              fieldbackground=[('readonly', c["bg_entry"])], 
              foreground=[('readonly', c["fg_entry"])])

    lbl_main_title.config(bg=c["bg_root"], fg=c["fg_title"])
    btn_cambiar_tema.config(bg=c["btn_theme_bg"], fg=c["btn_theme_fg"], text=c["btn_theme_text"])
    
    for lbl in [lbl_desc_cod, lbl_desc_nom, lbl_desc_p1, lbl_desc_p2, lbl_desc_p3]:
        lbl.config(foreground=c["fg_subtitle"])

    for linea in lineas_separador:
        linea.config(bg=c["bg_sep"])

    for entry in [entry_tienda, entry_codigo, entry_nombre, entry_precio, entry_copias]:
        entry.config(bg=c["bg_entry"], fg=c["fg_entry"], insertbackground=c["fg_entry"])

    if var_es_promo.get():
        entry_descuento.config(bg=c["bg_entry"], fg=c["fg_entry"], insertbackground=c["fg_entry"])
    else:
        entry_descuento.config(bg=c["bg_entry_disabled"], fg=c["fg_entry_disabled"])

    chk_sin_codigo.config(bg=c["bg_root"], activebackground=c["bg_root"], selectcolor=c["bg_entry"])
    chk_es_promo.config(bg=c["bg_root"], activebackground=c["bg_root"], selectcolor=c["bg_entry"])

    btn_logo.config(bg=c["bg_btn_secondary"], fg=c["fg_btn_secondary"])
    btn_guardar_solo.config(bg=c["bg_btn_gray"], fg=c["fg_btn_gray"])
    btn_imprimir.config(bg=c["bg_btn_print"], fg=c["fg_btn_print"])
    btn_masivo.config(bg=c["bg_btn_excel"], fg=c["fg_btn_excel"])

def toggle_tema():
    global tema_actual
    tema_actual = "oscuro" if tema_actual == "claro" else "claro"
    aplicar_tema(tema_actual)

# Sincronización con el toggle de promoción según el tema activo
def toggle_promocion():
    c = TEMAS[tema_actual]
    if var_es_promo.get():
        entry_descuento.config(state="normal", bg=c["bg_entry"], fg=c["fg_entry"])
        entry_descuento.focus()
    else:
        entry_descuento.delete(0, tk.END)
        entry_descuento.config(state="disabled", bg=c["bg_entry_disabled"], fg=c["fg_entry_disabled"])

# =============================================================================
# --- CONSTRUCCIÓN DE LA INTERFAZ GRÁFICA ---
# =============================================================================
root = tk.Tk()
root.title("🏷️ ETIQUETADOR MASTER 36x22 - Impresión A4")
root.geometry("540x880") 

style = ttk.Style()
style.theme_use('clam')

main_frame = ttk.Frame(root, padding=25)
main_frame.pack(fill="both", expand=True)

lineas_separador = []

def crear_separador(pad_y=10):
    sep = ttk.Frame(main_frame, height=1)
    sep.pack(fill="x", pady=pad_y)
    linea = tk.Frame(sep, height=1)
    linea.pack(fill="x")
    lineas_separador.append(linea)

# BARRA SUPERIOR: TÍTULO Y BOTÓN DE MODO CLARO/OSCURO
fila_superior = ttk.Frame(main_frame)
fila_superior.pack(fill="x", pady=(0, 10))

lbl_main_title = tk.Label(fila_superior, text="🏷️ ETIQUETADOR MASTER", font=("Segoe UI", 15, "bold"))
lbl_main_title.pack(side="left", anchor="w")

btn_cambiar_tema = tk.Button(fila_superior, text="🌙 Modo Oscuro", command=toggle_tema, font=("Segoe UI", 8, "bold"), bd=1, relief="solid", cursor="hand2")
btn_cambiar_tema.pack(side="right", ipady=2, ipadx=8)

# SECCIÓN 1: HARDWARE
lbl_sec1 = ttk.Label(main_frame, text="⚙️ HARDWARE DE IMPRESIÓN", font=("Segoe UI", 9, "bold"), foreground="#2980b9")
lbl_sec1.pack(anchor="w", pady=(0, 5))
combo_impresoras = ttk.Combobox(main_frame, values=obtener_impresoras(), font=("Segoe UI", 10), state="readonly")
combo_impresoras.pack(fill="x", pady=2, ipady=4)
combo_impresoras.current(0)

crear_separador()

# SECCIÓN 2: EMPRESA
lbl_sec2 = ttk.Label(main_frame, text="💼 CORPORATIVO / ENCABEZADO", font=("Segoe UI", 9, "bold"), foreground="#d35400")
lbl_sec2.pack(anchor="w", pady=(0, 5))

entry_tienda = tk.Entry(main_frame, font=("Segoe UI", 11), bd=1, relief="solid")
entry_tienda.pack(fill="x", pady=2, ipady=4)
entry_tienda.insert(0, "COMERCIAL EL COBRE")

btn_logo = tk.Button(main_frame, text="🖼️ Cargar Logotipo Corporativo", command=seleccionar_logo, font=("Segoe UI", 9, "bold"), bd=1, relief="solid", cursor="hand2")
btn_logo.pack(fill="x", pady=5, ipady=4)

lbl_status_logo = ttk.Label(main_frame, text="⚠️ Sin logo (Se usará solo texto)", font=("Segoe UI", 9, "italic"), foreground="#7f8c8d")
lbl_status_logo.pack(anchor="w", pady=2)

crear_separador()

# SECCIÓN 3: PANEL DE CONTROL DE ARTÍCULO
lbl_sec3 = ttk.Label(main_frame, text="📝 REGISTRO DE ARTÍCULO INDIVIDUAL", font=("Segoe UI", 9, "bold"), foreground="#2980b9")
lbl_sec3.pack(anchor="w", pady=(0, 5))

fila_checks = ttk.Frame(main_frame)
fila_checks.pack(fill="x", pady=4)

var_sin_codigo = tk.BooleanVar(value=False)
chk_sin_codigo = tk.Checkbutton(fila_checks, text="🚫 Ocultar Código", variable=var_sin_codigo, fg="#c0392b", font=("Segoe UI", 9, "bold"), cursor="hand2")
chk_sin_codigo.pack(side="left", padx=(0, 15))

var_es_promo = tk.BooleanVar(value=False)
chk_es_promo = tk.Checkbutton(fila_checks, text="🔥 ACTIVAR PROMOCIÓN", variable=var_es_promo, command=toggle_promocion, fg="#27ae60", font=("Segoe UI", 9, "bold"), cursor="hand2")
chk_es_promo.pack(side="left")

lbl_desc_cod = ttk.Label(main_frame, text="Código de Barras Manual (Opcional):", font=("Segoe UI", 9))
lbl_desc_cod.pack(anchor="w")
entry_codigo = tk.Entry(main_frame, font=("Segoe UI", 11), bd=1, relief="solid")
entry_codigo.pack(fill="x", pady=2, ipady=4)

lbl_desc_nom = ttk.Label(main_frame, text="Nombre / Descripción del Producto:", font=("Segoe UI", 9))
lbl_desc_nom.pack(anchor="w")
entry_nombre = tk.Entry(main_frame, font=("Segoe UI", 11), bd=1, relief="solid")
entry_nombre.pack(fill="x", pady=2, ipady=4)

fila_precios = ttk.Frame(main_frame)
fila_precios.pack(fill="x", pady=6)

col_1 = ttk.Frame(fila_precios)
col_1.pack(side="left", fill="x", expand=True, padx=(0, 5))
lbl_desc_p1 = ttk.Label(col_1, text="Precio actual ($):", font=("Segoe UI", 9))
lbl_desc_p1.pack(anchor="w")
entry_precio = tk.Entry(col_1, font=("Segoe UI", 11), bd=1, relief="solid")
entry_precio.pack(fill="x", pady=2, ipady=4)

col_2 = ttk.Frame(fila_precios)
col_2.pack(side="left", fill="x", expand=True, padx=5)
lbl_desc_p2 = ttk.Label(col_2, text="Descuento (%):", font=("Segoe UI", 9))
lbl_desc_p2.pack(anchor="w")
entry_descuento = tk.Entry(col_2, font=("Segoe UI", 11), bd=1, relief="solid", state="disabled")
entry_descuento.pack(fill="x", pady=2, ipady=4)

col_3 = ttk.Frame(fila_precios)
col_3.pack(side="right", fill="x", expand=True, padx=(5, 0))
lbl_desc_p3 = ttk.Label(col_3, text="Nº Copias:", font=("Segoe UI", 9))
lbl_desc_p3.pack(anchor="w")
entry_copias = tk.Entry(col_3, font=("Segoe UI", 11), bd=1, relief="solid")
entry_copias.pack(fill="x", pady=2, ipady=4)
entry_copias.insert(0, "1")

fila_botones = ttk.Frame(main_frame)
fila_botones.pack(fill="x", pady=10)

btn_guardar_solo = tk.Button(fila_botones, text="💾 SÓLO GUARDAR PLANILLA", command=lambda: ejecutar_accion_individual(solo_guardar=True), font=("Segoe UI", 10, "bold"), bd=0, cursor="hand2")
btn_guardar_solo.pack(side="left", fill="x", expand=True, padx=(0, 4), ipady=8)

btn_imprimir = tk.Button(fila_botones, text="🖨️ IMPRIMIR HOJA A4", command=lambda: ejecutar_accion_individual(solo_guardar=False), font=("Segoe UI", 10, "bold"), bd=0, cursor="hand2")
btn_imprimir.pack(side="right", fill="x", expand=True, padx=(4, 0), ipady=8)

crear_separador()

# SECCIÓN 4: EXCEL MASIVO EN PLANILLAS A4
lbl_sec4 = ttk.Label(main_frame, text="📊 PROCESAMIENTO LOTE EXCEL (36x22 mm)", font=("Segoe UI", 9, "bold"), foreground="#27ae60")
lbl_sec4.pack(anchor="w", pady=(0, 5))

btn_masivo = tk.Button(main_frame, text="🚀 PROCESAR EXCEL A PLANILLAS A4", command=generar_masivo_excel, font=("Segoe UI", 11, "bold"), bd=0, cursor="hand2")
btn_masivo.pack(fill="x", pady=5, ipady=12)

# Inicializar tema claro
aplicar_tema("claro")

root.mainloop()