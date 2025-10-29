
import streamlit as st
import pandas as pd
import mysql.connector
from dotenv import load_dotenv
import os
import io
from datetime import date

# Cargar variables de entorno desde .env
load_dotenv()

# --- Configuración de la base de datos ---
DB_HOST = os.getenv("MYSQL_HOST")
DB_USER = os.getenv("MYSQL_USER")
DB_PASS = os.getenv("MYSQL_PASSWORD")
DB_NAME = os.getenv("MYSQL_DATABASE")
DB_PORT = os.getenv("MYSQL_PORT")

# --- Funciones de la aplicación ---

# Cache del recurso para no reconectar en cada recarga
@st.cache_resource
def get_db_connection():
    """Establece y devuelve una conexión a la base de datos."""
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            port=DB_PORT
        )
        return conn
    except mysql.connector.Error as e:
        st.error(f"Error al conectar a la base de datos: {e}")
        return None

# Cache de los datos para no volver a consultar si las fechas no cambian
@st.cache_data
def fetch_data(start_date, end_date):
    """Consulta la vista y devuelve los datos como un DataFrame de Pandas."""
    conn = get_db_connection()
    if conn:
        query = "SELECT * FROM vw_consulta_certificados WHERE fecha BETWEEN %s AND %s"
        df = pd.read_sql(query, conn, params=(start_date, end_date))
        # Asegurarse de que la columna de fecha sea del tipo correcto
        if not df.empty:
            df['fecha'] = pd.to_datetime(df['fecha']).dt.date
        return df
    return pd.DataFrame()

def to_excel(df):
    """Convierte un DataFrame a un archivo Excel en memoria."""
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='openpyxl')
    df.to_excel(writer, index=False, sheet_name='Certificados')
    writer.close()
    processed_data = output.getvalue()
    return processed_data

# --- Interfaz de Usuario de Streamlit ---

st.set_page_config(page_title="Consulta de Certificados", layout="wide")

st.title("📊 Consulta de Certificados de Retención")

# --- Filtros en la barra lateral ---
st.sidebar.header("Filtros")
start_date = st.sidebar.date_input("Fecha Desde", date(date.today().year, 1, 1))
end_date = st.sidebar.date_input("Fecha Hasta", date.today())

# Validar que la fecha de inicio no sea posterior a la de fin
if start_date > end_date:
    st.sidebar.error("Error: La fecha 'Desde' no puede ser posterior a la fecha 'Hasta'.")
else:
    # Cargar y mostrar datos
    df = fetch_data(start_date, end_date)

    if not df.empty:
        st.dataframe(df)

        # --- Botón de Descarga ---
        df_excel = to_excel(df)
        start_date_str = start_date.strftime("%d-%m-%Y")
        end_date_str = end_date.strftime("%d-%m-%Y")
        st.download_button(
            label="📥 Descargar a Excel",
            data=df_excel,
            file_name=f"certificados_{start_date_str}_a_{end_date_str}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("No se encontraron registros para el rango de fechas seleccionado.")

