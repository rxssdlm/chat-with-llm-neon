"""
Matriz de permisos (RBAC) del agente CRM.

Roles soportados: "seller" | "manager" | "admin".
"""

# Umbral a partir del cual un descuento requiere aprobacion de manager/admin
DISCOUNT_APPROVAL_THRESHOLD_PCT = 20.0

# Monto a partir del cual una venta/oportunidad requiere confirmacion humana
SALE_AMOUNT_CONFIRMATION_THRESHOLD = 50_000.0

ROLES_THAT_CAN_APPROVE_DISCOUNTS = {"manager", "admin"}


def can_approve_discount(role: str, discount_pct: float) -> bool:
    if discount_pct <= DISCOUNT_APPROVAL_THRESHOLD_PCT:
        return True
    return role in ROLES_THAT_CAN_APPROVE_DISCOUNTS


def requires_confirmation_for_amount(amount: float) -> bool:
    return amount > SALE_AMOUNT_CONFIRMATION_THRESHOLD


def requires_confirmation_for_discount(discount_pct: float) -> bool:
    return discount_pct > DISCOUNT_APPROVAL_THRESHOLD_PCT
