// ======================================================
// VARIABLES
// ======================================================

let mapa = null;

let marcadorUsuario = null;

let marcadoresEstaciones = [];


// ======================================================
// CREAR MAPA
// ======================================================

function crearMapa() {

    if (mapa !== null) {
        return;
    }

    mapa = L.map("map").setView(
        [14.0723, -87.1921],
        13
    );


    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            maxZoom: 19,

            attribution:
                "&copy; OpenStreetMap contributors"
        }
    ).addTo(mapa);
}


// Crear mapa inmediatamente
crearMapa();


// ======================================================
// USAR UBICACIÓN DEL USUARIO
// ======================================================

function usarUbicacion() {

    const estado =
        document.getElementById("estado");

    const boton =
        document.getElementById("btnUbicacion");


    estado.innerHTML =
        "⏳ Obteniendo tu ubicación...";

    boton.disabled = true;


    // Comprobar soporte

    if (!navigator.geolocation) {

        estado.innerHTML =
            "❌ Tu navegador no soporta geolocalización.";

        boton.disabled = false;

        return;
    }


    navigator.geolocation.getCurrentPosition(

        function(position) {

            // =========================================
            // UBICACIÓN OBTENIDA
            // =========================================

            const lat =
                position.coords.latitude;

            const lon =
                position.coords.longitude;


            console.log(
                "Latitud:",
                lat
            );

            console.log(
                "Longitud:",
                lon
            );


            // Poner coordenadas en inputs

            document.getElementById(
                "latitud"
            ).value = lat.toFixed(6);


            document.getElementById(
                "longitud"
            ).value = lon.toFixed(6);


            estado.innerHTML =
                "✅ Ubicación encontrada correctamente.";


            boton.disabled = false;


            // Mostrar ubicación

            mostrarUsuario(
                lat,
                lon
            );

        },

        function(error) {

            boton.disabled = false;


            console.error(
                "Error de geolocalización:",
                error
            );


            // =========================================
            // ERRORES
            // =========================================

            if (error.code === 1) {

                estado.innerHTML =
                    "❌ Permiso de ubicación rechazado. " +
                    "Debes permitir la ubicación en Chrome.";

            }

            else if (error.code === 2) {

                estado.innerHTML =
                    "❌ No se pudo determinar tu ubicación.";

            }

            else if (error.code === 3) {

                estado.innerHTML =
                    "❌ Se agotó el tiempo para obtener tu ubicación.";

            }

            else {

                estado.innerHTML =
                    "❌ Error desconocido al obtener ubicación.";

            }

        },

        {
            enableHighAccuracy: true,

            timeout: 15000,

            maximumAge: 0
        }

    );

}


// ======================================================
// MOSTRAR UBICACIÓN DEL USUARIO
// ======================================================

function mostrarUsuario(lat, lon) {

    crearMapa();


    // Si ya existe marcador
    // eliminarlo

    if (marcadorUsuario !== null) {

        mapa.removeLayer(
            marcadorUsuario
        );

    }


    // Crear marcador

    marcadorUsuario =
        L.marker(
            [lat, lon]
        )
        .addTo(mapa);


    marcadorUsuario.bindPopup(

        `
        <div style="text-align:center">

            <h3>📍 Tu ubicación</h3>

            <p>
                <b>Latitud:</b>
                ${lat.toFixed(6)}
            </p>

            <p>
                <b>Longitud:</b>
                ${lon.toFixed(6)}
            </p>

        </div>
        `

    ).openPopup();


    // Centrar mapa

    mapa.setView(
        [lat, lon],
        16
    );


    // Forzar actualización del mapa

    setTimeout(
        function() {

            mapa.invalidateSize();

        },
        200
    );
}


// ======================================================
// MOSTRAR COORDENADAS ESCRITAS MANUALMENTE
// ======================================================

function mostrarCoordenadasEnMapa() {

    const lat =
        parseFloat(
            document.getElementById(
                "latitud"
            ).value
        );


    const lon =
        parseFloat(
            document.getElementById(
                "longitud"
            ).value
        );


    if (
        isNaN(lat) ||
        isNaN(lon)
    ) {

        document.getElementById(
            "estado"
        ).innerHTML =
            "❌ Debes introducir latitud y longitud.";

        return;
    }


    if (
        lat < -90 ||
        lat > 90
    ) {

        document.getElementById(
            "estado"
        ).innerHTML =
            "❌ La latitud debe estar entre -90 y 90.";

        return;
    }


    if (
        lon < -180 ||
        lon > 180
    ) {

        document.getElementById(
            "estado"
        ).innerHTML =
            "❌ La longitud debe estar entre -180 y 180.";

        return;
    }


    document.getElementById(
        "estado"
    ).innerHTML =
        "✅ Coordenadas colocadas en el mapa.";


    mostrarUsuario(
        lat,
        lon
    );
}


// ======================================================
// BUSCAR ESTACIONES
// ======================================================

async function buscarEstaciones() {

    const estado =
        document.getElementById(
            "estado"
        );


    const lat =
        parseFloat(
            document.getElementById(
                "latitud"
            ).value
        );


    const lon =
        parseFloat(
            document.getElementById(
                "longitud"
            ).value
        );


    // Validar

    if (
        isNaN(lat) ||
        isNaN(lon)
    ) {

        estado.innerHTML =
            "❌ Primero coloca tu ubicación.";

        return;
    }


    estado.innerHTML =
        "⏳ Buscando las 3 estaciones más cercanas...";


    // Mostrar usuario

    mostrarUsuario(
        lat,
        lon
    );


    try {

        const respuesta =
            await fetch(
                "/buscar",
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body: JSON.stringify({

                        latitud: lat,

                        longitud: lon

                    })

                }
            );


        const datos =
            await respuesta.json();


        if (!respuesta.ok) {

            throw new Error(
                datos.error ||
                "Error en el servidor."
            );

        }


        estado.innerHTML =
            "✅ Se encontraron las estaciones.";


        mostrarEstaciones(
            datos.estaciones
        );


    }

    catch (error) {

        console.error(error);


        estado.innerHTML =
            "❌ " + error.message;

    }

}


// ======================================================
// MOSTRAR ESTACIONES
// ======================================================

function mostrarEstaciones(estaciones) {

    const resultados =
        document.getElementById(
            "resultados"
        );


    resultados.innerHTML = "";


    // Borrar marcadores anteriores

    marcadoresEstaciones.forEach(
        function(marcador) {

            mapa.removeLayer(
                marcador
            );

        }
    );


    marcadoresEstaciones = [];


    // ==========================================
    // RECORRER ESTACIONES
    // ==========================================

    estaciones.forEach(
        function(estacion, indice) {


            // Crear marcador

            const marcador =
                L.marker(
                    [
                        estacion.latitud,
                        estacion.longitud
                    ]
                )
                .addTo(mapa);


            marcador.bindPopup(

                `
                <h3>
                    🚔 ${estacion.nombre}
                </h3>

                <p>
                    📍 ${estacion.ubicacion}
                </p>

                <p>
                    📏 ${estacion.distancia} km
                </p>
                `

            );


            marcadoresEstaciones.push(
                marcador
            );


            // ==========================================
            // TARJETA
            // ==========================================

            let html = `

                <div class="estacion">

                    <h2>
                        ${indice + 1}.
                        🚔 ${estacion.nombre}
                    </h2>

                    <p>
                        <b>📍 Ubicación:</b>
                        ${estacion.ubicacion}
                    </p>

                    <p>
                        <b>📏 Distancia:</b>
                        ${estacion.distancia}
                        km
                    </p>

            `;


            // ==========================================
            // MODO MÁS RÁPIDO
            // ==========================================

            if (
                estacion.modo_mas_rapido
            ) {

                html += `

                    <div class="rapido">

                        ⚡ MODO MÁS RÁPIDO

                        <br><br>

                        ${obtenerIcono(
                            estacion.modo_mas_rapido
                        )}

                        ${estacion.modo_mas_rapido}

                        <br>

                        ⏱️
                        ${estacion.tiempo_mas_rapido}
                        minutos

                    </div>

                `;

            }


            // ==========================================
            // TRANSPORTE
            // ==========================================

            html += `

                <h3>
                    🚗🚲🚶 Tiempo por transporte
                </h3>

            `;


            for (
                const modo in estacion.rutas
            ) {

                const ruta =
                    estacion.rutas[modo];


                html += `

                    <div class="ruta">

                        <strong>
                            ${obtenerIcono(modo)}
                            ${modo}
                        </strong>

                        <br>

                        📏 Distancia:
                        ${ruta.distancia_km}
                        km

                        <br>

                        ⏱️ Tiempo:
                        ${ruta.tiempo_minutos}
                        minutos

                    </div>

                `;

            }


            html += `

                </div>

            `;


            resultados.innerHTML += html;

        }
    );


    // ==========================================
    // CENTRAR MAPA
    // ==========================================

    if (
        estaciones.length > 0
    ) {

        const puntos = [];


        if (marcadorUsuario) {

            puntos.push(
                marcadorUsuario.getLatLng()
            );

        }


        marcadoresEstaciones.forEach(
            function(marcador) {

                puntos.push(
                    marcador.getLatLng()
                );

            }
        );


        if (puntos.length > 0) {

            mapa.fitBounds(
                L.latLngBounds(puntos),
                {
                    padding: [50, 50]
                }
            );

        }

    }

}


// ======================================================
// ICONOS
// ======================================================

function obtenerIcono(modo) {

    if (
        modo === "Vehículo"
    ) {

        return "🚗";

    }


    if (
        modo === "Bicicleta"
    ) {

        return "🚲";

    }


    if (
        modo === "Caminar"
    ) {

        return "🚶";

    }


    return "📍";

}