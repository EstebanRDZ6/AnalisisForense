import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import pyodbc
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
import webbrowser
import sys
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

# Configuración de conexión a SQL Server
server = r'PECUPC\SQLEXPRESS'  # Ajusta según corresponda
database = 'BdForense'
conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes"

try:
    conn = pyodbc.connect(conn_str)
except Exception as e:
    messagebox.showerror("Error de Conexión", f"No se pudo conectar a SQL Server:\n{e}")
    sys.exit(1)

# Diccionario para renombrar medicamentos
rename_map = {
    "Medicamento X": "Paracetamol",
    "Medicamento Y": "Ibuprofeno"
}

#####################################
# Funciones de visualización gráfica
#####################################

def clear_frame(frame):
    for widget in frame.winfo_children():
        widget.destroy()

def mostrar_grafico(fig, frame):
    clear_frame(frame)
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    widget = canvas.get_tk_widget()
    widget.pack(fill=tk.BOTH, expand=True)
    toolbar = NavigationToolbar2Tk(canvas, frame)
    toolbar.update()
    canvas._tkcanvas.pack(fill=tk.BOTH, expand=True)

#####################################
# Función 1: Sustancias más comunes
#####################################

def grafico_sustancias_comunes():
    query = """
    SELECT Sustancia, COUNT(*) AS Frecuencia
    FROM ComponentesQuimicos
    GROUP BY Sustancia
    ORDER BY Frecuencia DESC
    """
    df = pd.read_sql(query, conn)
    if df.empty:
        messagebox.showinfo("Información", "No se encontraron datos de sustancias.")
        return

    # Reemplazar nombres según el diccionario
    df['Sustancia'] = df['Sustancia'].replace(rename_map)
    
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(x='Frecuencia', y='Sustancia', data=df, palette='viridis', ax=ax)
    ax.set_title("Sustancias más comunes en muestras de sangre forense")
    ax.set_xlabel("Número de detecciones")
    ax.set_ylabel("Sustancia")
    plt.tight_layout()
    mostrar_grafico(fig, grafico_frame)

##############################################
# Función 2: Buscar sustancia y mostrar detección
##############################################

def buscar_sustancia():
    termino = simpledialog.askstring("Buscar Sustancia", "Ingrese parte del nombre de la sustancia:")
    if not termino:
        return

    query = """
    SELECT DISTINCT Sustancia
    FROM ComponentesQuimicos
    WHERE Sustancia LIKE ?
    ORDER BY Sustancia
    """
    df = pd.read_sql(query, conn, params=('%' + termino + '%',))
    if df.empty:
        messagebox.showinfo("Información", "No se encontraron sustancias con ese término.")
        return

    # Aplicar renombramiento a las opciones
    opciones = df['Sustancia'].replace(rename_map).tolist()
    lista_str = "\n".join([f"{i+1}. {s}" for i, s in enumerate(opciones)])
    seleccion = simpledialog.askstring(
        "Seleccionar Sustancia",
        f"Se encontraron las siguientes sustancias:\n{lista_str}\n\nIngrese el número de la sustancia a mostrar:"
    )
    try:
        num = int(seleccion)
        if num < 1 or num > len(opciones):
            raise ValueError
    except (ValueError, TypeError):
        messagebox.showerror("Error", "Entrada inválida.")
        return

    sustancia = opciones[num - 1]

    query_det = """
    SELECT Sustancia, COUNT(*) AS Frecuencia
    FROM ComponentesQuimicos
    WHERE (CASE WHEN Sustancia = 'Medicamento X' THEN 'Paracetamol'
                WHEN Sustancia = 'Medicamento Y' THEN 'Ibuprofeno'
                ELSE Sustancia END) = ?
    GROUP BY Sustancia
    """
    df_det = pd.read_sql(query_det, conn, params=(sustancia,))
    if df_det.empty:
        messagebox.showinfo("Información", "No se encontraron registros para esa sustancia.")
        return

    # Reemplazo en el resultado
    df_det['Sustancia'] = df_det['Sustancia'].replace(rename_map)
    
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.barplot(x='Sustancia', y='Frecuencia', data=df_det, palette='coolwarm', ax=ax)
    ax.set_title(f"Detección de la sustancia: {sustancia}")
    ax.set_xlabel("Sustancia")
    ax.set_ylabel("Frecuencia")
    plt.tight_layout()
    mostrar_grafico(fig, grafico_frame)

#####################################
# Función 3: Correlación sustancias - enfermedades (Heatmap)
#####################################

def grafico_correlacion_enfermedades():
    query = """
    SELECT 
        (CASE 
            WHEN CQ.Sustancia = 'Medicamento X' THEN 'Paracetamol'
            WHEN CQ.Sustancia = 'Medicamento Y' THEN 'Ibuprofeno'
            ELSE CQ.Sustancia 
         END) AS Sustancia,
         ED.Enfermedad,
         COUNT(*) AS Frecuencia
    FROM ComponentesQuimicos CQ
    JOIN MuestrasSangre MS ON CQ.ID_Muestra = MS.ID_Muestra
    JOIN EnfermedadesDetectadas ED ON MS.ID_Muestra = ED.ID_Muestra
    GROUP BY 
        (CASE 
            WHEN CQ.Sustancia = 'Medicamento X' THEN 'Paracetamol'
            WHEN CQ.Sustancia = 'Medicamento Y' THEN 'Ibuprofeno'
            ELSE CQ.Sustancia 
         END),
         ED.Enfermedad
    ORDER BY ED.Enfermedad, Frecuencia DESC
    """
    df = pd.read_sql(query, conn)
    if df.empty:
        messagebox.showinfo("Información", "No hay datos para correlacionar sustancias con enfermedades.")
        return

    pivot_df = df.pivot_table(index='Sustancia', columns='Enfermedad', values='Frecuencia', fill_value=0)
    pivot_df = pivot_df.astype(int)
    
    fig, ax = plt.subplots(figsize=(12, 8))
    heatmap = sns.heatmap(pivot_df, annot=True, fmt="d", cmap="YlGnBu", ax=ax)
    ax.set_title("Correlación entre Sustancias y Enfermedades", fontsize=14)
    ax.set_xlabel("Enfermedad", fontsize=12)
    ax.set_ylabel("Sustancia", fontsize=12)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right", fontsize=10)
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=10)
    plt.tight_layout()
    mostrar_grafico(fig, grafico_frame)

#####################################
# Función 4: Casos por ubicación - Mapa
#####################################

location_coords = {
    "Buenos Aires": (-34.6037, -58.3816),
    "Ciudad de México": (19.4326, -99.1332),
    "Madrid": (40.4168, -3.7038),
    "Bogotá": (4.7110, -74.0721),
    "Lima": (-12.0464, -77.0428),
    "Santiago": (-33.4489, -70.6693),
    "Montevideo": (-34.9011, -56.1645),
    "Caracas": (10.4806, -66.9036)
}

def mapa_casos_por_ubicacion():
    query = """
    SELECT Ubicacion, COUNT(*) AS Cantidad
    FROM CasosForenses
    GROUP BY Ubicacion
    ORDER BY Cantidad DESC
    """
    df = pd.read_sql(query, conn)
    if df.empty:
        messagebox.showinfo("Información", "No se encontraron datos de casos por ubicación.")
        return
    
    m = folium.Map(location=[10, -60], zoom_start=3)
    
    for idx, row in df.iterrows():
        loc = row['Ubicacion']
        cantidad = row['Cantidad']
        coords = location_coords.get(loc, None)
        if coords:
            folium.Marker(location=coords,
                          popup=f"{loc}: {cantidad} casos",
                          tooltip=loc).add_to(m)
        else:
            folium.Marker(location=[0,0],
                          popup=f"{loc}: {cantidad} casos (sin coordenadas)",
                          tooltip=loc).add_to(m)
    
    map_filename = "casos_por_ubicacion.html"
    m.save(map_filename)
    webbrowser.open(map_filename)

#####################################
# Función 5: Distribución de tipos de sangre en casos
#####################################

def grafico_tipos_sangre():
    query = """
    SELECT P.Tipo_Sangre, COUNT(CF.ID_Caso) AS Casos
    FROM Pacientes P
    JOIN CasosForenses CF ON P.ID_Paciente = CF.ID_Paciente
    GROUP BY P.Tipo_Sangre
    ORDER BY Casos DESC
    """
    df = pd.read_sql(query, conn)
    if df.empty:
        messagebox.showinfo("Información", "No se encontraron datos de tipos de sangre.")
        return
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.barplot(x='Tipo_Sangre', y='Casos', data=df, palette='mako', ax=ax)
    ax.set_title("Distribución de Tipos de Sangre en Casos Forenses")
    ax.set_xlabel("Tipo de Sangre")
    ax.set_ylabel("Cantidad de casos")
    plt.tight_layout()
    mostrar_grafico(fig, grafico_frame)

#####################################
# Función 6: Seleccionar Paciente (nuevo)
#####################################

def seleccionar_paciente():
    query = "SELECT ID_Paciente, Nombre FROM Pacientes ORDER BY Nombre"
    df = pd.read_sql(query, conn)
    if df.empty:
        messagebox.showinfo("Información", "No hay pacientes registrados.")
        return None

    top = tk.Toplevel(root)
    top.title("Seleccionar Paciente")
    top.geometry("400x300")

    frame = ttk.Frame(top)
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL)
    lb = tk.Listbox(frame, selectmode=tk.SINGLE, yscrollcommand=scrollbar.set, font=("Arial", 10))
    scrollbar.config(command=lb.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    for index, row in df.iterrows():
        lb.insert(tk.END, f"{row['ID_Paciente']}. {row['Nombre']}")

    selected_id = [None]

    def seleccionar():
        selection = lb.curselection()
        if selection:
            item = lb.get(selection[0])
            try:
                selected_id[0] = int(item.split('.')[0])
            except Exception as e:
                selected_id[0] = None
        top.destroy()

    btn = ttk.Button(top, text="Seleccionar", command=seleccionar)
    btn.pack(pady=5)

    top.wait_window()
    return selected_id[0]

#####################################
# Función 7: Reporte Detallado de Paciente (actualizado)
#####################################

def reporte_paciente():
    id_paciente = seleccionar_paciente()
    if id_paciente is None:
        return

    query_paciente = """
    SELECT *
    FROM Pacientes
    WHERE ID_Paciente = ?
    """
    paciente = pd.read_sql(query_paciente, conn, params=(id_paciente,))
    if paciente.empty:
        messagebox.showinfo("Información", "Paciente no encontrado.")
        return

    query_casos = """
    SELECT *
    FROM CasosForenses
    WHERE ID_Paciente = ?
    """
    casos = pd.read_sql(query_casos, conn, params=(id_paciente,))

    query_sustancias = """
    SELECT CQ.Sustancia, CQ.Concentracion, CQ.Tipo_Analisis, MS.Fecha_Analisis
    FROM ComponentesQuimicos CQ
    JOIN MuestrasSangre MS ON CQ.ID_Muestra = MS.ID_Muestra
    JOIN CasosForenses CF ON MS.ID_Caso = CF.ID_Caso
    WHERE CF.ID_Paciente = ?
    """
    sustancias = pd.read_sql(query_sustancias, conn, params=(id_paciente,))

    query_enfermedades = """
    SELECT ED.Enfermedad, MS.Fecha_Analisis
    FROM EnfermedadesDetectadas ED
    JOIN MuestrasSangre MS ON ED.ID_Muestra = MS.ID_Muestra
    JOIN CasosForenses CF ON MS.ID_Caso = CF.ID_Caso
    WHERE CF.ID_Paciente = ?
    """
    enfermedades = pd.read_sql(query_enfermedades, conn, params=(id_paciente,))

    reporte_win = tk.Toplevel(root)
    reporte_win.title("Reporte Detallado de Paciente")
    reporte_win.geometry("800x600")

    txt = tk.Text(reporte_win, wrap=tk.WORD, font=("Consolas", 10))
    txt.pack(fill=tk.BOTH, expand=True)

    reporte_text = f"--- Datos del Paciente ---\n{paciente.to_string(index=False)}\n\n"
    reporte_text += "--- Casos Forenses ---\n" + (casos.to_string(index=False) if not casos.empty else "No hay casos registrados") + "\n\n"
    reporte_text += "--- Sustancias Detectadas ---\n" + (sustancias.to_string(index=False) if not sustancias.empty else "No hay datos de sustancias") + "\n\n"
    reporte_text += "--- Enfermedades Detectadas ---\n" + (enfermedades.to_string(index=False) if not enfermedades.empty else "No hay datos de enfermedades") + "\n\n"
    
    txt.insert(tk.END, reporte_text)
    txt.config(state=tk.DISABLED)

#####################################
# Función 8: Salir
#####################################

def salir():
    if messagebox.askyesno("Confirmar salida", "¿Está seguro que desea salir?"):
        root.destroy()

#####################################
# Menú principal en la interfaz gráfica
#####################################

root = tk.Tk()
root.title("Análisis Forense Interactivo")
root.geometry("1200x700")

menu_frame = ttk.Frame(root, padding=10)
menu_frame.pack(side=tk.LEFT, fill=tk.Y)

grafico_frame = ttk.Frame(root, padding=10)
grafico_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

titulo = ttk.Label(menu_frame, text="Menú de Análisis", font=("Arial", 16))
titulo.pack(pady=10)

btn1 = ttk.Button(menu_frame, text="1. Sustancias más comunes", command=grafico_sustancias_comunes)
btn1.pack(fill=tk.X, pady=5)

btn2 = ttk.Button(menu_frame, text="2. Buscar sustancia", command=buscar_sustancia)
btn2.pack(fill=tk.X, pady=5)

btn3 = ttk.Button(menu_frame, text="3. Correlación sustancias - enfermedades", command=grafico_correlacion_enfermedades)
btn3.pack(fill=tk.X, pady=5)

btn4 = ttk.Button(menu_frame, text="4. Casos por ubicación (Mapa)", command=mapa_casos_por_ubicacion)
btn4.pack(fill=tk.X, pady=5)

btn5 = ttk.Button(menu_frame, text="5. Tipos de sangre en casos", command=grafico_tipos_sangre)
btn5.pack(fill=tk.X, pady=5)

btn6 = ttk.Button(menu_frame, text="6. Reporte de Paciente", command=reporte_paciente)
btn6.pack(fill=tk.X, pady=5)

btn7 = ttk.Button(menu_frame, text="7. Salir", command=salir)
btn7.pack(fill=tk.X, pady=20)

root.mainloop()
