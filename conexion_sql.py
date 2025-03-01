import pyodbc

# Configuración de la conexión
server = 'PECUPC\SQLEXPRESS'  # Cambia esto por tu servidor
database = 'BdForense'  # Nombre de tu base de datos
username = 'sa'  # Si usas autenticación de usuario
password = '123456'  # Tu contraseña, si usas autenticación de usuario

try:

    # Si usas usuario/contraseña, usa esta línea en su lugar:
    conn = pyodbc.connect(f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}")

    print("✅ Conexión exitosa a SQL Server")
except Exception as e:
    print(f"❌ Error al conectar: {e}")
