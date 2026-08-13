import math
import pandas as pd
import requests
import streamlit as st

# Título de la aplicación
st.title("Estación de Policía")

# Carga de datos y visualización inicial
try:
    df = pd.read_csv("estaciones.csv")
    st.subheader("Estaciones registradas")
    st.dataframe(df)

    # Preparar datos para los cálculos
    estaciones = df.copy()
    estaciones["latitud"] = pd.to_numeric(
        estaciones["latitud"], errors="coerce"
    )
    estaciones["longitud"] = pd.to_numeric(
        estaciones["longitud"], errors="coerce"
    )
    estaciones = estaciones.dropna(subset=["latitud", "longitud"])

except Exception as e:
    st.error(f"Error cargando estaciones: {e}")
    estaciones = pd.DataFrame(
        columns=["nombre", "ubicacion", "latitud", "longitud"]
    )


def distancia(lat1, lon1, lat2, lon2):
    """
    Distancia entre dos coordenadas utilizando Haversine.
    Resultado en kilómetros.
    """
    R = 6371

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def obtener_ruta(lat1, lon1, lat2, lon2, perfil):
    """
    Obtiene ruta utilizando OSRM.

    perfiles:
    driving  = vehículo
    cycling  = bicicleta
    foot     = caminar
    """
    url = f"https://router.project-osrm.org/route/v1/{perfil}/{lon1},{lat1};{lon2},{lat2}"

    parametros = {"overview": "full", "geometries": "geojson"}

    try:
        respuesta = requests.get(url, params=parametros, timeout=10)
        datos = respuesta.json()

        if datos.get("code") != "Ok":
            return None

        ruta = datos["routes"][0]

        return {
            "distancia_km": round(ruta["distance"] / 1000, 2),
            "tiempo_minutos": round(ruta["duration"] / 60, 1),
            "geometria": ruta["geometry"],
        }

    except Exception as e:
        st.write(f"Error OSRM ({perfil}):", e)
        return None


# Formulario de entrada para coordenadas del usuario
st.markdown("---")
st.header("Buscar Estaciones Cercanas")

col1, col2 = st.columns(2)
with col1:
    latitud_usuario = st.number_input(
        "Ingresa tu Latitud:", value=0.0, format="%.6f"
    )
with col2:
    longitud_usuario = st.number_input(
        "Ingresa tu Longitud:", value=0.0, format="%.6f"
    )

if st.button("Buscar Estaciones Cercanas", type="primary"):
    if estaciones.empty:
        st.error("No hay estaciones disponibles para realizar el cálculo.")
    elif latitud_usuario == 0.0 and longitud_usuario == 0.0:
        st.warning("Por favor ingresa coordenadas válidas.")
    else:
        with st.spinner("Calculando rutas y distancias..."):
            # Calcular distancia en línea recta
            lista = []

            for _, estacion in estaciones.iterrows():
                d = distancia(
                    latitud_usuario,
                    longitud_usuario,
                    estacion["latitud"],
                    estacion["longitud"],
                )

                lista.append(
                    {
                        "nombre": str(estacion["nombre"]),
                        "ubicacion": str(estacion["ubicacion"]),
                        "latitud": float(estacion["latitud"]),
                        "longitud": float(estacion["longitud"]),
                        "distancia": round(d, 2),
                    }
                )

            # Ordenar por distancia y tomar las 3 más cercanas
            lista.sort(key=lambda x: x["distancia"])
            tres_cercanas = lista[:3]

            # Modos de transporte
            perfiles = {
                "Vehículo": "driving",
                "Bicicleta": "cycling",
                "Caminar": "foot",
            }

            for estacion in tres_cercanas:
                estacion["rutas"] = {}

                for nombre, perfil in perfiles.items():
                    ruta = obtener_ruta(
                        latitud_usuario,
                        longitud_usuario,
                        estacion["latitud"],
                        estacion["longitud"],
                        perfil,
                    )

                    if ruta:
                        estacion["rutas"][nombre] = ruta

                # Encontrar el modo más rápido
                if estacion["rutas"]:
                    modo_rapido = min(
                        estacion["rutas"],
                        key=lambda x: estacion["rutas"][x]["tiempo_minutos"],
                    )
                    estacion["modo_mas_rapido"] = modo_rapido
                    estacion["tiempo_mas_rapido"] = estacion["rutas"][
                        modo_rapido
                    ]["tiempo_minutos"]
                else:
                    estacion["modo_mas_rapido"] = "No disponible"
                    estacion["tiempo_mas_rapido"] = None

            # Desplegar resultados en pantalla
            st.subheader("Top 3 Estaciones más Cercanas")

            for i, est in enumerate(tres_cercanas, start=1):
                with st.expander(
                    f"{i}. {est['nombre']} - ({est['distancia']} km en línea recta)",
                    expanded=(i == 1),
                ):
                    st.write(f"**Ubicación:** {est['ubicacion']}")
                    st.write(
                        f"**Modo más rápido:** {est['modo_mas_rapido']} ({est['tiempo_mas_rapido']} min)"
                    )

                    st.markdown("**Detalles por medio de transporte:**")
                    if est["rutas"]:
                        for modo, datos_ruta in est["rutas"].items():
                            st.write(
                                f"- **{modo}:** {datos_ruta['distancia_km']} km | {datos_ruta['tiempo_minutos']} min"
                            )
                    else:
                        st.info(
                            "No se pudieron obtener rutas detalladas desde OSRM."
                        )



