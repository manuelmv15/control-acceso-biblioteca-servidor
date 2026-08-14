UMBRAL_PENDIENTE_HORAS = 300
UMBRAL_CRITICO_HORAS = 400

# El cliente reporta su estado (sesion_activa + heartbeat) cada
# SYNC_INTERVAL segundos (30s por defecto) vía POST /estado, sin importar
# si hay sesión activa o no. Si no llega señal en esta ventana, asumimos
# que la PC está apagada/desconectada en vez de simplemente "libre".
UMBRAL_DISPONIBLE_MINUTOS = 2


def calcular_estado(horas):
    if horas is None:
        return None
    if horas > UMBRAL_CRITICO_HORAS:
        return "critico"
    if horas >= UMBRAL_PENDIENTE_HORAS:
        return "pendiente"
    return "optimo"
