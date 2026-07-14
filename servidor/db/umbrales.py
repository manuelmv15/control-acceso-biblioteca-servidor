UMBRAL_PENDIENTE_HORAS = 300
UMBRAL_CRITICO_HORAS = 400


def calcular_estado(horas):
    if horas is None:
        return None
    if horas > UMBRAL_CRITICO_HORAS:
        return "critico"
    if horas >= UMBRAL_PENDIENTE_HORAS:
        return "pendiente"
    return "optimo"
