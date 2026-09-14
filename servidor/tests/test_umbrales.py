"""Tests de calcular_estado (db/umbrales.py): decide el estado_mantenimiento
("optimo"/"pendiente"/"critico") que ve el panel a partir de las horas de uso
acumuladas de una PC. Es una función pura de tres ramas, pero un error de
signo o de operador (`>` vs `>=`) en los límites pasa fácil desapercibido en
una revisión manual y cambia en qué momento el panel avisa que una PC
necesita mantenimiento."""

from db.umbrales import UMBRAL_CRITICO_HORAS, UMBRAL_PENDIENTE_HORAS, calcular_estado


def test_calcular_estado_none_si_no_hay_horas_reportadas():
    assert calcular_estado(None) is None


def test_calcular_estado_optimo_por_debajo_del_umbral_de_pendiente():
    assert calcular_estado(0) == "optimo"
    assert calcular_estado(UMBRAL_PENDIENTE_HORAS - 1) == "optimo"


def test_calcular_estado_pendiente_en_el_umbral_y_hasta_el_critico_inclusive():
    assert calcular_estado(UMBRAL_PENDIENTE_HORAS) == "pendiente"
    assert calcular_estado(UMBRAL_CRITICO_HORAS) == "pendiente"  # == no es ">" todavía


def test_calcular_estado_critico_por_encima_del_umbral():
    assert calcular_estado(UMBRAL_CRITICO_HORAS + 1) == "critico"
