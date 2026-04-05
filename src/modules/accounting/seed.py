"""Chart of accounts seed templates by business type."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.accounting.models import ChartOfAccounts


CHURCH_ACCOUNTS = [
    {"code": "1", "name": "ACTIVOS", "type": "asset", "parent": None, "is_system": True},
    {"code": "1.1", "name": "Activos Corrientes", "type": "asset", "parent": "1", "is_system": True},
    {"code": "1.1.01", "name": "Caja General", "type": "asset", "parent": "1.1", "is_system": True},
    {"code": "1.1.02", "name": "Bancos", "type": "asset", "parent": "1.1", "is_system": True},
    {"code": "1.1.03", "name": "Cuentas por Cobrar", "type": "asset", "parent": "1.1", "is_system": True},
    {"code": "2", "name": "PASIVOS", "type": "liability", "parent": None, "is_system": True},
    {"code": "2.1", "name": "Pasivos Corrientes", "type": "liability", "parent": "2", "is_system": True},
    {"code": "2.1.01", "name": "Cuentas por Pagar", "type": "liability", "parent": "2.1", "is_system": True},
    {"code": "2.1.02", "name": "Retenciones por Pagar", "type": "liability", "parent": "2.1", "is_system": True},
    {"code": "3", "name": "PATRIMONIO", "type": "equity", "parent": None, "is_system": True},
    {"code": "3.1.01", "name": "Patrimonio Neto", "type": "equity", "parent": "3", "is_system": True},
    {"code": "3.1.02", "name": "Excedente/Deficit Acumulado", "type": "equity", "parent": "3", "is_system": True},
    {"code": "4", "name": "INGRESOS", "type": "revenue", "parent": None, "is_system": True},
    {"code": "4.1", "name": "Ingresos Operacionales", "type": "revenue", "parent": "4", "is_system": True},
    {"code": "4.1.01", "name": "Diezmos", "type": "revenue", "parent": "4.1", "is_system": True},
    {"code": "4.1.02", "name": "Ofrendas", "type": "revenue", "parent": "4.1", "is_system": True},
    {"code": "4.1.03", "name": "Donaciones", "type": "revenue", "parent": "4.1", "is_system": True},
    {"code": "4.1.04", "name": "Otros Ingresos", "type": "revenue", "parent": "4.1", "is_system": True},
    {"code": "5", "name": "GASTOS", "type": "expense", "parent": None, "is_system": True},
    {"code": "5.1", "name": "Gastos Operacionales", "type": "expense", "parent": "5", "is_system": True},
    {"code": "5.1.01", "name": "Arriendo", "type": "expense", "parent": "5.1", "is_system": True},
    {"code": "5.1.02", "name": "Servicios Publicos", "type": "expense", "parent": "5.1", "is_system": True},
    {"code": "5.1.03", "name": "Salarios y Honorarios", "type": "expense", "parent": "5.1", "is_system": True},
    {"code": "5.1.04", "name": "Gastos Ministeriales", "type": "expense", "parent": "5.1", "is_system": True},
    {"code": "5.1.05", "name": "Mantenimiento", "type": "expense", "parent": "5.1", "is_system": True},
    {"code": "5.1.06", "name": "Diezmo del Diezmo", "type": "expense", "parent": "5.1", "is_system": True},
    {"code": "5.1.07", "name": "Insumos y Materiales", "type": "expense", "parent": "5.1", "is_system": True},
    {"code": "5.1.08", "name": "Seguros", "type": "expense", "parent": "5.1", "is_system": True},
    {"code": "5.1.09", "name": "Transporte", "type": "expense", "parent": "5.1", "is_system": True},
    {"code": "5.1.10", "name": "Otros Gastos", "type": "expense", "parent": "5.1", "is_system": True},
]

ACCOUNT_TEMPLATES: dict[str, list[dict]] = {
    "church": CHURCH_ACCOUNTS,
}


async def seed_chart_of_accounts(
    db: AsyncSession,
    org_id: uuid.UUID,
    template_code: str = "church",
) -> list[ChartOfAccounts]:
    """Seed chart of accounts for an organization based on a template.

    Creates accounts in order so that parents are created before children,
    resolving parent codes to database IDs.
    """
    template = ACCOUNT_TEMPLATES.get(template_code, [])
    if not template:
        return []

    code_to_id: dict[str, uuid.UUID] = {}
    created_accounts: list[ChartOfAccounts] = []

    for acct in template:
        parent_id = code_to_id.get(acct["parent"]) if acct["parent"] else None
        account = ChartOfAccounts(
            organization_id=org_id,
            code=acct["code"],
            name=acct["name"],
            type=acct["type"],
            parent_id=parent_id,
            is_system=acct.get("is_system", False),
            is_active=True,
        )
        db.add(account)
        await db.flush()
        code_to_id[acct["code"]] = account.id
        created_accounts.append(account)

    return created_accounts
