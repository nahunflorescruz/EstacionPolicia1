from flask import Flask, render_template, request, jsonify
import pandas as pd
import math
import requests

app = Flask(__name__)

# Cargar estaciones
try:
    estaciones = pd.read_csv("estaciones.csv")

    estaciones["latitud"] = pd.to_numeric(
        estaciones["latitud"], errors="coerce"
    )

    estaciones["longitud"] = pd.to_numeric(
        estaciones["longitud"], errors="coerce"
    )

    estaciones = estaciones.dropna(
        subset=["latitud", "longitud"]
    )

except Exception as e:
    print("Error cargando estaciones:", e)
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
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
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

    url = (
        f"https://router.project-osrm.org/route/v1/"
        f"{perfil}/{lon1},{lat1};{lon2},{lat2}"
    )

    parametros = {
        "overview": "full",
        "geometries": "geojson"
    }

    try:
        respuesta = requests.get(
            url,
            params=parametros,
            timeout=10
        )

        datos = respuesta.json()

        if datos.get("code") != "Ok":
            return None

        ruta = datos["routes"][0]

        return {
            "distancia_km": round(
                ruta["distance"] / 1000,
                2
            ),
            "tiempo_minutos": round(
                ruta["duration"] / 60,
                1
            ),
            "geometria": ruta["geometry"]
        }

    except Exception as e:
        print("Error OSRM:", e)
        return None


@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/buscar", methods=["POST"])
def buscar():

    datos = request.get_json()

    try:
        latitud = float(datos["latitud"])
        longitud = float(datos["longitud"])
    except:
        return jsonify({
            "error": "Coordenadas inválidas"
        }), 400

    if estaciones.empty:
        return jsonify({
            "error": "No hay estaciones cargadas."
        }), 500

    # Calcular distancia en línea recta
    lista = []

    for _, estacion in estaciones.iterrows():

        d = distancia(
            latitud,
            longitud,
            estacion["latitud"],
            estacion["longitud"]
        )

        lista.append({
            "nombre": str(estacion["nombre"]),
            "ubicacion": str(estacion["ubicacion"]),
            "latitud": float(estacion["latitud"]),
            "longitud": float(estacion["longitud"]),
            "distancia": round(d, 2)
        })

    # Ordenar por distancia
    lista.sort(key=lambda x: x["distancia"])

    # Las 3 más cercanas
    tres = lista[:3]

    # Modos de transporte
    perfiles = {
        "Vehículo": "driving",
        "Bicicleta": "cycling",
        "Caminar": "foot"
    }

    for estacion in tres:

        estacion["rutas"] = {}

        for nombre, perfil in perfiles.items():

            ruta = obtener_ruta(
                latitud,
                longitud,
                estacion["latitud"],
                estacion["longitud"],
                perfil
            )

            if ruta:
                estacion["rutas"][nombre] = ruta

        # Encontrar el modo más rápido
        if estacion["rutas"]:

            modo_rapido = min(
                estacion["rutas"],
                key=lambda x:
                estacion["rutas"][x]["tiempo_minutos"]
            )

            estacion["modo_mas_rapido"] = modo_rapido

            estacion["tiempo_mas_rapido"] = (
                estacion["rutas"]
                [modo_rapido]
                ["tiempo_minutos"]
            )

        else:
            estacion["modo_mas_rapido"] = "No disponible"
            estacion["tiempo_mas_rapido"] = None

    return jsonify({
        "usuario": {
            "latitud": latitud,
            "longitud": longitud
        },
        "estaciones": tres
    })


if __name__ == '__main__':
    # Agrega use_reloader=False y debug=False
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
