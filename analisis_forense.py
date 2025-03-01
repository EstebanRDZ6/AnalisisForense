import pyodbc
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sys

# Configuración de conexión a SQL Server
server = r'PECUPC\SQLEXPRESS'  # Ajusta según corresponda
database = 'BdForense'
conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes"

try:
    conn = pyodbc.connect(conn_str)
    print("✅ Conexión exitosa a SQL Server")
except Exception as e:
    print(f"❌ Error al conectar: {e}")
    sys.exit(1)

# Función 1: Mostrar sustancias más comunes en todas las muestras
def grafico_sustancias_comunes():
    query = """
    SELECT Sustancia, COUNT(*) AS Frecuencia
    FROM ComponentesQuimicos
    GROUP BY Sustancia
    ORDER BY Frecuencia DESC
    """
    df = pd.read_sql(query, conn)
    if df.empty:
        print("No se encontraron datos de sustancias.")
        return
    plt.figure(figsize=(10, 6))
    sns.barplot(x='Frecuencia', y='Sustancia', data=df, palette='viridis')
    plt.title("Sustancias más comunes en muestras de sangre forense")
    plt.xlabel("Número de detecciones")
    plt.ylabel("Sustancia")
    plt.tight_layout()
    plt.show()

# Función 2: Buscar y seleccionar una sustancia específica
def buscar_sustancia():
    # Se solicita un término de búsqueda al usuario
    termino = input("Ingrese parte del nombre de la sustancia a buscar: ").strip()
    query = """
    SELECT DISTINCT Sustancia
    FROM ComponentesQuimicos
    WHERE Sustancia LIKE ?
    ORDER BY Sustancia
    """
    df = pd.read_sql(query, conn, params=('%'+termino+'%',))
    if df.empty:
        print("No se encontraron sustancias con ese término.")
        return
    # Mostrar las sustancias encontradas
    print("\nSustancias encontradas:")
    for idx, row in df.iterrows():
        print(f"{idx+1}. {row['Sustancia']}")
    try:
        seleccion = int(input("Seleccione el número de la sustancia deseada: ").strip())
        if seleccion < 1 or seleccion > len(df):
            print("Selección inválida.")
            return
    except ValueError:
        print("Entrada inválida.")
        return
    sustancia = df.iloc[seleccion-1]['Sustancia']
    # Mostrar la frecuencia de detección de la sustancia seleccionada
    query_det = """
    SELECT Sustancia, COUNT(*) AS Frecuencia
    FROM ComponentesQuimicos
    WHERE Sustancia = ?
    GROUP BY Sustancia
    """
    df_det = pd.read_sql(query_det, conn, params=(sustancia,))
    if df_det.empty:
        print("No se encontraron registros para esa sustancia.")
        return
    plt.figure(figsize=(6, 4))
    sns.barplot(x='Sustancia', y='Frecuencia', data=df_det, palette='coolwarm')
    plt.title(f"Detección de la sustancia: {sustancia}")
    plt.xlabel("Sustancia")
    plt.ylabel("Frecuencia de detección")
    plt.tight_layout()
    plt.show()

# Función 3: Mostrar correlación entre sustancias y enfermedades
def grafico_correlacion_enfermedades():
    query = """
    SELECT CQ.Sustancia, ED.Enfermedad, COUNT(*) AS Frecuencia
    FROM ComponentesQuimicos CQ
    JOIN MuestrasSangre MS ON CQ.ID_Muestra = MS.ID_Muestra
    JOIN EnfermedadesDetectadas ED ON MS.ID_Muestra = ED.ID_Muestra
    GROUP BY CQ.Sustancia, ED.Enfermedad
    ORDER BY ED.Enfermedad, Frecuencia DESC
    """
    df = pd.read_sql(query, conn)
    if df.empty:
        print("No hay datos para correlacionar sustancias con enfermedades.")
        return

    # Para hacerlo más comprensible, creamos un gráfico de barras para cada enfermedad.
    enfermedades = df['Enfermedad'].unique()
    n = len(enfermedades)
    plt.figure(figsize=(10, 6))
    for i, enfermedad in enumerate(enfermedades, start=1):
        df_temp = df[df['Enfermedad'] == enfermedad]
        plt.subplot(n, 1, i)
        sns.barplot(x='Frecuencia', y='Sustancia', data=df_temp, palette='Set2')
        plt.title(f"Enfermedad: {enfermedad}")
        plt.xlabel("")
        plt.ylabel("")
    plt.tight_layout()
    plt.show()

# Función 4 (Opcional): Mostrar distribución de casos forenses por ubicación
def grafico_casos_por_ubicacion():
    query = """
    SELECT Ubicacion, COUNT(*) AS Cantidad
    FROM CasosForenses
    GROUP BY Ubicacion
    ORDER BY Cantidad DESC
    """
    df = pd.read_sql(query, conn)
    if df.empty:
        print("No se encontraron datos de casos por ubicación.")
        return
    plt.figure(figsize=(10, 5))
    sns.barplot(x='Ubicacion', y='Cantidad', data=df, palette='pastel')
    plt.title("Casos Forenses por Ubicación")
    plt.xlabel("Ubicación")
    plt.ylabel("Cantidad de casos")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

# Función 5 (Opcional): Mostrar distribución de tipos de sangre en casos forenses
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
        print("No se encontraron datos de tipos de sangre.")
        return
    plt.figure(figsize=(8, 5))
    sns.barplot(x='Tipo_Sangre', y='Casos', data=df, palette='mako')
    plt.title("Distribución de Tipos de Sangre en Casos Forenses")
    plt.xlabel("Tipo de Sangre")
    plt.ylabel("Cantidad de casos")
    plt.tight_layout()
    plt.show()

# Menú interactivo completo
def menu():
    while True:
        print("\n--- Análisis Forense Interactivo ---")
        print("1. Mostrar sustancias más comunes")
        print("2. Buscar y mostrar detección de una sustancia específica")
        print("3. Mostrar correlación entre sustancias y enfermedades")
        print("4. Mostrar distribución de casos forenses por ubicación")
        print("5. Mostrar distribución de tipos de sangre en casos forenses")
        print("6. Salir")
        opcion = input("Selecciona una opción (1-6): ").strip()
        
        if opcion == '1':
            grafico_sustancias_comunes()
        elif opcion == '2':
            buscar_sustancia()
        elif opcion == '3':
            grafico_correlacion_enfermedades()
        elif opcion == '4':
            grafico_casos_por_ubicacion()
        elif opcion == '5':
            grafico_tipos_sangre()
        elif opcion == '6':
            confirm = input("¿Está seguro que desea salir? (s/n): ").strip().lower()
            if confirm == 's':
                print("Saliendo del programa...")
                break
        else:
            print("Opción inválida. Intente nuevamente.")

if __name__ == '__main__':
    menu()
