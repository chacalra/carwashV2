"""Helpers para resolver el tenant actual desde argumentos explicitos."""


def resolve_lavanderia_id(lavanderia_id=None, *, required=False):
    """Devuelve el tenant indicado y valida si es obligatorio."""
    if required and lavanderia_id is None:
        raise ValueError("Hace falta una lavanderia activa para ejecutar esta operacion.")
    return lavanderia_id
