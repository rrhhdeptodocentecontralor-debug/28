import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from io import BytesIO

# ==================== CONFIGURACIÓN ====================
st.set_page_config(layout="wide", page_title="Sistema Académico PRO", page_icon="🏛️")
st.title("🏛️ Sistema Académico Institucional PRO")

# ==================== ESTADOS ====================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'df' not in st.session_state:
    st.session_state.df = None
if 'df_procesado' not in st.session_state:
    st.session_state.df_procesado = None

# ==================== LOGIN ====================
def login_ui():
    if st.session_state.authenticated:
        with st.sidebar:
            st.success("✅ Conectado")
            if st.button("🚪 Cerrar Sesión"):
                st.session_state.authenticated = False
                st.rerun()
        return True
    with st.sidebar:
        st.markdown("### 🔐 Acceso")
        user = st.text_input("Usuario")
        pwd = st.text_input("Contraseña", type="password")
        if st.button("Ingresar"):
            if user == "admin" and pwd == "admin123":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
    return False

# ==================== CARGA DE DATOS ====================
def cargar_excel(archivo):
    """Carga archivo Excel usando openpyxl (más compatible)"""
    if archivo is not None:
        try:
            # Intentar con openpyxl primero
            return pd.read_excel(archivo, engine='openpyxl')
        except:
            try:
                # Alternativa con xlrd
                return pd.read_excel(archivo)
            except Exception as e:
                st.error(f"Error al leer el archivo: {e}")
                return None
    return None

def procesar_datos(df):
    if df is None:
        return None
    
    df = df.copy()
    
    # Mapeo automático de columnas comunes
    mapeo = {
        'Carrera/Nombre': 'Carrera',
        'Asignatura/Nombre mostrado': 'Asignatura',
        'Cursos/Alumnos activos': 'Alumnos_Activos',
        'Asignatura/Horas Docente': 'Horas_Docente',
        'Cursos/Detalles/Docentes': 'Docentes',
        'Cursos/Turno (Nombre)/Nombre mostrado': 'Turno',
        'Departamento Académico/Nombre': 'Departamento',
        'Estado': 'Estado',
        'Remanentes': 'Remanentes',
        'Aprobadas': 'Aprobadas',
        'Tomadas': 'Tomadas',
        'Cursos/Código': 'Codigo_Curso'
    }
    
    for old, new in mapeo.items():
        if old in df.columns:
            df[new] = df[old]
    
    # Limpiar
    if 'Asignatura' in df.columns:
        df = df.dropna(subset=['Asignatura'])
    
    # Convertir números
    for col in ['Alumnos_Activos', 'Horas_Docente', 'Remanentes', 'Aprobadas', 'Tomadas']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df

# ==================== FUNCIONES DE ANÁLISIS ====================
def mostrar_metricas(df):
    st.subheader("📊 Métricas Disponibles")
    
    cols = st.columns(4)
    
    # Mostrar métricas según columnas disponibles
    if 'Alumnos_Activos' in df.columns:
        cols[0].metric("👨‍🎓 Total Alumnos", f"{int(df['Alumnos_Activos'].sum()):,}")
    
    if 'Codigo_Curso' in df.columns:
        cols[1].metric("📚 Total Cursos", df['Codigo_Curso'].nunique())
    else:
        cols[1].metric("📚 Total Registros", len(df))
    
    if 'Horas_Docente' in df.columns:
        cols[2].metric("⏰ Total Horas", f"{int(df['Horas_Docente'].sum()):,}")
    
    if 'Asignatura' in df.columns:
        cols[3].metric("📖 Asignaturas", df['Asignatura'].nunique())

def mostrar_graficos(df):
    st.subheader("📈 Gráficos")
    
    # Detectar qué gráficos se pueden mostrar
    opciones = []
    
    if 'Carrera' in df.columns:
        opciones.append("Distribución por Carrera")
    if 'Turno' in df.columns:
        opciones.append("Distribución por Turno")
    if 'Estado' in df.columns:
        opciones.append("Estado de Cursos")
    if 'Alumnos_Activos' in df.columns:
        opciones.append("Top 10 Cursos con más Alumnos")
        opciones.append("Histograma de Alumnos")
    if 'Horas_Docente' in df.columns:
        opciones.append("Top 10 Cursos con más Horas")
    if 'Departamento' in df.columns:
        opciones.append("Horas por Departamento")
    
    if not opciones:
        st.warning("No hay suficientes datos para mostrar gráficos")
        return
    
    seleccion = st.multiselect("Selecciona gráficos:", opciones, default=opciones[:2])
    
    for opcion in seleccion:
        st.markdown(f"**{opcion}**")
        
        if opcion == "Distribución por Carrera":
            data = df['Carrera'].value_counts()
            fig = px.pie(values=data.values, names=data.index)
            st.plotly_chart(fig, use_container_width=True)
        
        elif opcion == "Distribución por Turno":
            data = df['Turno'].value_counts()
            fig = px.bar(x=data.index, y=data.values)
            st.plotly_chart(fig, use_container_width=True)
        
        elif opcion == "Estado de Cursos":
            data = df['Estado'].value_counts()
            fig = px.pie(values=data.values, names=data.index)
            st.plotly_chart(fig, use_container_width=True)
        
        elif opcion == "Top 10 Cursos con más Alumnos":
            top = df.nlargest(10, 'Alumnos_Activos')[['Asignatura', 'Alumnos_Activos']]
            fig = px.bar(top, x='Alumnos_Activos', y='Asignatura', orientation='h')
            st.plotly_chart(fig, use_container_width=True)
        
        elif opcion == "Histograma de Alumnos":
            fig = px.histogram(df, x='Alumnos_Activos', nbins=20)
            st.plotly_chart(fig, use_container_width=True)
        
        elif opcion == "Top 10 Cursos con más Horas":
            top = df.nlargest(10, 'Horas_Docente')[['Asignatura', 'Horas_Docente']]
            fig = px.bar(top, x='Horas_Docente', y='Asignatura', orientation='h')
            st.plotly_chart(fig, use_container_width=True)
        
        elif opcion == "Horas por Departamento":
            data = df.groupby('Departamento')['Horas_Docente'].sum().sort_values()
            fig = px.bar(x=data.values, y=data.index, orientation='h')
            st.plotly_chart(fig, use_container_width=True)

def mostrar_tablas(df):
    st.subheader("📋 Tablas")
    
    opciones = ["Ver todos los datos"]
    
    if 'Alumnos_Activos' in df.columns:
        opciones.append("Top 20 cursos con más alumnos")
        opciones.append("Top 20 cursos con menos alumnos")
    
    if 'Remanentes' in df.columns:
        opciones.append("Cursos con remanentes")
    
    if 'Estado' in df.columns:
        opciones.append("Cursos pendientes")
    
    seleccion = st.selectbox("Selecciona:", opciones)
    
    if seleccion == "Ver todos los datos":
        st.dataframe(df, use_container_width=True)
    
    elif seleccion == "Top 20 cursos con más alumnos":
        top = df.nlargest(20, 'Alumnos_Activos')[['Asignatura', 'Carrera', 'Alumnos_Activos']]
        st.dataframe(top, use_container_width=True)
    
    elif seleccion == "Top 20 cursos con menos alumnos":
        bottom = df.nsmallest(20, 'Alumnos_Activos')[['Asignatura', 'Carrera', 'Alumnos_Activos']]
        st.dataframe(bottom, use_container_width=True)
    
    elif seleccion == "Cursos con remanentes":
        rem = df[df['Remanentes'] > 0][['Asignatura', 'Remanentes', 'Alumnos_Activos']]
        st.dataframe(rem, use_container_width=True)
    
    elif seleccion == "Cursos pendientes":
        pend = df[df['Estado'] != 'Completada'][['Asignatura', 'Estado']]
        st.dataframe(pend, use_container_width=True)

def mostrar_filtros(df):
    st.subheader("🔍 Filtrar Datos")
    
    df_filtrado = df.copy()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if 'Carrera' in df.columns:
            carreras = st.multiselect("Carrera:", df['Carrera'].unique())
            if carreras:
                df_filtrado = df_filtrado[df_filtrado['Carrera'].isin(carreras)]
        
        if 'Turno' in df.columns:
            turnos = st.multiselect("Turno:", df['Turno'].unique())
            if turnos:
                df_filtrado = df_filtrado[df_filtrado['Turno'].isin(turnos)]
    
    with col2:
        if 'Estado' in df.columns:
            estados = st.multiselect("Estado:", df['Estado'].unique())
            if estados:
                df_filtrado = df_filtrado[df_filtrado['Estado'].isin(estados)]
        
        if 'Alumnos_Activos' in df.columns:
            min_val = int(df['Alumnos_Activos'].min())
            max_val = int(df['Alumnos_Activos'].max())
            rango = st.slider("Alumnos:", min_val, max_val, (min_val, max_val))
            df_filtrado = df_filtrado[(df_filtrado['Alumnos_Activos'] >= rango[0]) & 
                                       (df_filtrado['Alumnos_Activos'] <= rango[1])]
    
    st.info(f"📊 Mostrando {len(df_filtrado)} de {len(df)} registros")
    
    return df_filtrado

def mostrar_recomendaciones(df):
    st.subheader("💡 Recomendaciones")
    
    recomendaciones = []
    
    if 'Alumnos_Activos' in df.columns:
        media = df['Alumnos_Activos'].mean()
        baja = len(df[df['Alumnos_Activos'] < media * 0.5])
        if baja > 0:
            recomendaciones.append(f"⚠️ {baja} cursos tienen baja matrícula (<50% del promedio)")
    
    if 'Remanentes' in df.columns:
        rem = len(df[df['Remanentes'] > 0])
        if rem > 0:
            recomendaciones.append(f"📦 {rem} cursos tienen remanentes pendientes")
    
    if 'Estado' in df.columns:
        pend = len(df[df['Estado'] != 'Completada'])
        if pend > 0:
            recomendaciones.append(f"⏳ {pend} cursos están pendientes")
    
    if recomendaciones:
        for r in recomendaciones:
            st.info(r)
    else:
        st.success("✅ No se detectaron problemas")

def mostrar_exportacion(df):
    st.subheader("📥 Exportar")
    
    if st.button("Generar Excel"):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name="Datos", index=False)
        
        st.download_button(
            label="Descargar",
            data=output.getvalue(),
            file_name="datos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ==================== INTERFAZ PRINCIPAL ====================
if not login_ui():
    st.stop()

# Cargar archivo
with st.sidebar:
    st.markdown("---")
    archivo = st.file_uploader("📂 Cargar Excel", type=["xlsx", "xls"])
    
    if archivo:
        if st.button("🔄 Cargar"):
            with st.spinner("Cargando..."):
                st.session_state.df = cargar_excel(archivo)
                if st.session_state.df is not None:
                    st.session_state.df_procesado = procesar_datos(st.session_state.df)
                    st.success("✅ Datos cargados")
                    st.rerun()
    
    if st.session_state.df is not None:
        st.success(f"{len(st.session_state.df)} registros")

# Mostrar contenido
if st.session_state.df is None:
    st.info("📂 **Carga un archivo Excel para comenzar**")
    st.markdown("""
    ### Columnas que puede reconocer:
    - `Carrera/Nombre`
    - `Asignatura/Nombre mostrado`
    - `Cursos/Alumnos activos`
    - `Asignatura/Horas Docente`
    - `Estado`
    """)
    st.stop()

df = st.session_state.df_procesado

# Menú
menu = st.sidebar.radio("📌 Selecciona:", [
    "📊 Métricas",
    "📈 Gráficos",
    "📋 Tablas",
    "🔍 Filtros",
    "💡 Recomendaciones",
    "📥 Exportar"
])

# Aplicar filtros si es necesario
if menu == "🔍 Filtros" or menu == "📥 Exportar":
    df_actual = mostrar_filtros(df)
else:
    df_actual = df

# Mostrar según selección
if menu == "📊 Métricas":
    mostrar_metricas(df_actual)
elif menu == "📈 Gráficos":
    mostrar_graficos(df_actual)
elif menu == "📋 Tablas":
    mostrar_tablas(df_actual)
elif menu == "🔍 Filtros":
    st.success("Usa los filtros de arriba")
elif menu == "💡 Recomendaciones":
    mostrar_recomendaciones(df_actual)
elif menu == "📥 Exportar":
    mostrar_exportacion(df_actual)