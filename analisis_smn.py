from datetime import datetime
import json
import sys
import os

# Mapea nombres de mes en español (como vienen en el archivo del SMN) a su número
MESES_ESP = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, 
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11,
    "diciembre": 12
    }


def guardar_json(observaciones: dict, ruta_salida: str) -> None:
    """Guarda el diccionario de observaciones en un archivo JSON."""
    # default=str convierte los objetos datetime a texto
    with open(ruta_salida, "w", encoding="utf-8") as archivo:
        json.dump(observaciones, archivo, ensure_ascii=False, indent=2, default=str)


def separar_viento(campo_viento: str) -> tuple:
    # Separa "Norte  5" en ("Norte", 5.0); si es "Calma", velocidad = 0
    partes = campo_viento.split()
    if len(partes) == 1:
        direccion = partes[0]
        velocidad = 0
    else:
        direccion = partes[0]
        velocidad = float(partes[1])

    return direccion, velocidad


def leer_observaciones(ruta: str) -> dict:
    # Lee el .txt del SMN y arma {ciudad: {datos}}; devuelve también la lista de líneas mal formadas
    observaciones = {}
    lineas_invalidas = []

    try:
        codificacion = 'utf-8'
        try:
            with open(ruta, 'r', encoding='utf-8') as archivo_prueba:
                archivo_prueba.read()
        except UnicodeDecodeError:
            codificacion = 'latin-1'

        with open(ruta, 'r', encoding=codificacion) as archivo:
            for linea in archivo:
                campos = linea.strip().split(";")

                # Descarta líneas que no tengan los 10 campos esperados
                if len(campos) != 10:
                    lineas_invalidas.append(len(campos))
                    continue

                ciudad = campos[0].strip()
                direccion_viento, velocidad_viento = separar_viento(campos[8])

                # Arma un datetime real a partir de fecha + hora en texto
                try:
                    dia, mes_texto, año = campos[1].split("-")
                    hora, minuto = campos[2].split(":")
                    fecha_y_hora = datetime(int(año), MESES_ESP[mes_texto], int(dia), int(hora), int(minuto))
                except (ValueError, KeyError):
                    fecha_y_hora = None

                # Sensación térmica: puede venir como "No se calcula" u otro texto no numérico
                try:
                    sensacion_termica = float(campos[6])
                except ValueError:
                    sensacion_termica = None

                # Presión: se le saca un sufijo raro (ej. "999 /") antes de convertir
                try:
                    presion = float(campos[9].strip().split()[0])
                except ValueError:
                    presion = None

                try:
                    temperatura = float(campos[5])
                except ValueError:
                    temperatura = None

                datos_ciudad = {
                    "fecha": campos[1],
                    "hora": campos[2],
                    "condicion": campos[3],
                    "visibilidad": campos[4],
                    "temperatura": temperatura,
                    "sensacion_termica": sensacion_termica,
                    "humedad": campos[7].strip(),
                    "direccion_viento": direccion_viento,
                    "velocidad_viento": velocidad_viento,
                    "presion": presion,
                    "fecha_y_hora": fecha_y_hora
                }

                observaciones[ciudad] = datos_ciudad

    except FileNotFoundError:
        # No corta el programa: avisa y devuelve lo que haya (vacío en este caso)
        print(f"Error: no se encontró el archivo '{ruta}'")
        return observaciones, lineas_invalidas

    return observaciones, lineas_invalidas


def horarios_reportados(observaciones: dict) -> list:
    """Devuelve una lista de los horarios a los que las estaciones reportaron
    la observación, en formato 'HH:MM', sin repetir y ordenados de menor a mayor."""
    horarios = set()
    for datos in observaciones.values():
        if datos["fecha_y_hora"] is not None:
            horarios.add(datos["fecha_y_hora"].strftime("%H:%M"))

    return sorted(horarios)


def cantidad_ciudades(observaciones: dict) -> int:
    # Cantidad de claves (ciudades) en el diccionario
    return len(observaciones)


def cant_ciudades_comp(observaciones: dict) -> int:
    # Cuenta ciudades donde ningún campo es None (sin datos faltantes)
    completas = 0
    for datos in observaciones.values():
        falta = any(valor is None for valor in datos.values())
        if not falta:
            completas += 1
    return completas


def top_n_ciudades(observaciones: dict, campo: str, n: int, descendente: bool = True) -> list:
    # Función genérica de ranking: sirve para temperatura o viento según el "campo" que se le pase
    pares = []
    for ciudad, datos in observaciones.items():
        if datos[campo] is not None:
            pares.append((datos[campo], ciudad))  # (valor, ciudad): así el sort ordena por valor primero

    pares.sort(reverse=descendente)  # reverse=True → mayor a menor

    top = pares[:n]  # se queda con los primeros n ya ordenados

    ciudades = []
    for valor, ciudad in top:
        ciudades.append(ciudad)  # descarta el valor, se queda solo con el nombre

    return ciudades


def faltantes_por_campo(observaciones: dict) -> dict:
    # Por cada campo (fecha, temperatura, etc.), cuenta y lista en qué ciudades falta ese dato
    if not observaciones:
        return {}

    primera_ciudad = next(iter(observaciones.values()))  # toma cualquier ciudad para saber los nombres de campo
    campos = list(primera_ciudad.keys())

    resultado = {}
    for campo in campos:
        ciudades_con_faltante = []
        for ciudad, datos in observaciones.items():
            if datos[campo] is None:
                ciudades_con_faltante.append(ciudad)
        resultado[campo] = {
            "cantidad": len(ciudades_con_faltante),
            "ciudades": ciudades_con_faltante
        }
    return resultado


def mostrar_resumen(observaciones: dict, lineas_invalidas: list) -> None:
    # Junta todas las funciones anteriores y las imprime de forma legible
    print('=' * 40)
    print('RESUMEN DE OBSERVACIONES SMN')
    print('=' * 40)

    print(f"Ciudades leídas: {cantidad_ciudades(observaciones)}")
    print(f"Ciudades con datos completos: {cant_ciudades_comp(observaciones)}")   

    print(f"Líneas inválidas: {len(lineas_invalidas)}")
    if lineas_invalidas:
        print(f"  (cantidad de campos encontrados en cada una: {lineas_invalidas})")

    print(f"Horarios reportados: {horarios_reportados(observaciones)}")

    print("Datos faltantes por campo:")
    faltantes = faltantes_por_campo(observaciones)
    for campo, info in faltantes.items():
        print(f"  {campo}: {info['cantidad']} faltantes")

    # Extremos individuales, usando top_n_ciudades con n=1
    print("Extremos:")
    print(f"  Ciudad más cálida: {top_n_ciudades(observaciones, 'temperatura', 1)}")
    print(f"  Ciudad más fría: {top_n_ciudades(observaciones, 'temperatura', 1, descendente=False)}")
    print(f"  Ciudad con más viento: {top_n_ciudades(observaciones, 'velocidad_viento', 1)}")
    print(f"  Ciudad con menos viento: {top_n_ciudades(observaciones, 'velocidad_viento', 1, descendente=False)}")

    # Rankings de las 5 ciudades más destacadas en cada categoría
    print("Top 5 rankings:")
    print(f"  Más cálidas: {top_n_ciudades(observaciones, 'temperatura', 5)}")
    print(f"  Más frías: {top_n_ciudades(observaciones, 'temperatura', 5, descendente=False)}")
    print(f"  Más viento: {top_n_ciudades(observaciones, 'velocidad_viento', 5)}")
    print(f"  Menos viento: {top_n_ciudades(observaciones, 'velocidad_viento', 5, descendente=False)}")


def contar_ciudades_informadas(observaciones: dict) -> int:
    # Cuenta las ciudades que tienen temperatura (dato válido)
    informadas = 0
    for datos in observaciones.values():
        if datos.get("temperatura") is not None:
            informadas += 1
    return informadas


def contar_archivos(carpeta: str, extension: str) -> int:
    # Cuenta los archivos de la carpeta que terminan con la extensión dada
    cantidad = 0
    try:
        for nombre in os.listdir(carpeta):
            if nombre.endswith(extension):
                cantidad += 1
    except FileNotFoundError:
        pass  # si la carpeta no existe, hay 0 archivos
    return cantidad


def convertir_txt_a_json(ruta: str, nombre_sin_ext: str) -> None:
    # Lee un .txt del SMN, lo guarda como .json en obs_json/ e informa los conteos
    print("archivo del SMN, convirtiendo a json...")

    print("leyendo observaciones...")
    resultado, lineas_invalidas = leer_observaciones(ruta)

    # Si no se leyó ninguna observación (archivo inexistente o vacío), no seguimos
    if not resultado:
        print("no se pudo leer ninguna observación, no se genera el json.")
        return
    print("lectura completada.")

    print("pasando las fechas a formato ISO 8601...")
    for datos in resultado.values():
        if datos["fecha_y_hora"] is not None:
            # timespec='minutes' hace que no se muestren los segundos
            datos["fecha_y_hora"] = datos["fecha_y_hora"].isoformat(timespec='minutes')
    print("fechas convertidas.")

    if not os.path.exists("obs_json"):
        print("el directorio obs_json no existe, creándolo...")
        os.mkdir("obs_json")
        print("directorio creado.")

    ruta_salida = f"obs_json/{nombre_sin_ext}.json"
    print(f"guardando {ruta_salida}...")
    guardar_json(resultado, ruta_salida)
    print("archivo guardado.")

    print(f"Ciudades que contiene el archivo: {len(resultado)}")
    print(f"Ciudades informadas: {contar_ciudades_informadas(resultado)}")


def informar_json(ruta: str) -> None:
    # Lee un .json (siempre utf-8) e informa la cantidad de ciudades
    try:
        with open(ruta, 'r', encoding='utf-8') as archivo:
            datos_json = json.load(archivo)
    except FileNotFoundError:
        print(f"Error: no se encontró el archivo '{ruta}'")
        return
    except ValueError:
        print(f"Error: '{ruta}' no es un json válido.")
        return

    print(f"Ciudades que contiene el archivo JSON: {len(datos_json)}")
    print(f"Ciudades informadas: {contar_ciudades_informadas(datos_json)}")


def main() -> None:
    if len(sys.argv) > 2:
        print("Aviso: Se pasó más de un parámetro. Finalizando la ejecución.")
        return

    if len(sys.argv) == 1:
        print("Aviso: no se proporcionó ningún archivo por parámetro.")
        print(f"Archivos .txt en 'datos/': {contar_archivos('datos', '.txt')}")
        print(f"Archivos .json en 'obs_json/': {contar_archivos('obs_json', '.json')}")
        return

    # Si llega hasta acá, hay exactamente 1 parámetro
    ruta = sys.argv[1]

    nombre_archivo = ruta.split('/')[-1]
    partes_nombre = nombre_archivo.rsplit('.', 1)
    nombre_sin_ext = partes_nombre[0]

    if len(partes_nombre) > 1:
        extension = '.' + partes_nombre[1]
    else:
        extension = ''

    if extension.lower() == '.txt':
        convertir_txt_a_json(ruta, nombre_sin_ext)
    elif extension.lower() == '.json':
        informar_json(ruta)
    else:
        print(f"Error: Extensión '{extension}' no soportada.")


if __name__ == "__main__":
    main()