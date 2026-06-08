"""Savvy Graph — búsqueda universal de entidades cross-módulo.

El moat: la misma persona puede ser empleado (HR), afiliado (Memorial),
suscriptor (Water), lead, etc. Esto la encuentra en TODOS los módulos a la vez,
por nombre o documento. No requiere IA — es SQL puro sobre la BD compartida.
"""

from __future__ import annotations

import unicodedata
import uuid
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def _strip_accents(s: str) -> str:
    """Normaliza para coincidir con columnas unaccent(): minúsculas sin tildes."""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


@dataclass
class GraphHit:
    module: str          # 'hr', 'memorial', 'water', ...
    entity_type: str     # 'employee', 'affiliate', 'subscriber', 'lead'
    entity_id: str
    display_name: str
    document_number: str | None
    subtitle: str | None
    route: str | None


@dataclass
class PersonNode:
    """Una persona unificada y todas sus apariciones cross-módulo."""
    display_name: str
    document_number: str | None
    hits: list[GraphHit] = field(default_factory=list)


# Cada fuente: módulo, tipo, SQL con :org y :like, y cómo armar nombre/ruta.
# Se mantiene declarativo para agregar módulos fácilmente.
_SOURCES: list[dict[str, Any]] = [
    {
        "module": "hr", "entity_type": "employee",
        "sql": """
            SELECT id::text AS id,
                   trim(coalesce(first_name,'') || ' ' || coalesce(last_name,'')) AS name,
                   document_number AS doc,
                   employee_code AS extra
            FROM hr_employees
            WHERE organization_id = :org
              AND (unaccent(lower(coalesce(first_name,'') || ' ' || coalesce(last_name,''))) LIKE :like
                   OR coalesce(document_number,'') LIKE :like_doc
                   OR unaccent(lower(coalesce(email,''))) LIKE :like
                   OR lower(coalesce(employee_code,'')) LIKE :like)
            LIMIT 8
        """,
        "subtitle": "Empleado · {extra}",
        "route": "/hr/employees/{id}",
    },
    {
        "module": "memorial", "entity_type": "affiliate",
        "sql": """
            SELECT id::text AS id,
                   trim(coalesce(titular_business_name,
                        coalesce(titular_first_name,'') || ' ' || coalesce(titular_last_name,''))) AS name,
                   titular_document_number AS doc,
                   code AS extra
            FROM memorial_exequial_contracts
            WHERE organization_id = :org
              AND (unaccent(lower(coalesce(titular_first_name,'') || ' ' || coalesce(titular_last_name,''))) LIKE :like
                   OR unaccent(lower(coalesce(titular_business_name,''))) LIKE :like
                   OR coalesce(titular_document_number,'') LIKE :like_doc
                   OR unaccent(lower(coalesce(titular_email,''))) LIKE :like
                   OR lower(coalesce(code,'')) LIKE :like)
            LIMIT 8
        """,
        "subtitle": "Afiliado exequial · {extra}",
        "route": "/memorial/contracts/{id}",
    },
    {
        "module": "memorial", "entity_type": "lead",
        "sql": """
            SELECT id::text AS id,
                   trim(coalesce(business_name,
                        coalesce(first_name,'') || ' ' || coalesce(last_name,''))) AS name,
                   document_number AS doc,
                   code AS extra
            FROM memorial_leads
            WHERE organization_id = :org
              AND (unaccent(lower(coalesce(first_name,'') || ' ' || coalesce(last_name,''))) LIKE :like
                   OR unaccent(lower(coalesce(business_name,''))) LIKE :like
                   OR coalesce(document_number,'') LIKE :like_doc)
            LIMIT 5
        """,
        "subtitle": "Prospecto (lead) · {extra}",
        "route": "/memorial/crm",
    },
    {
        "module": "water", "entity_type": "subscriber",
        "sql": """
            SELECT id::text AS id,
                   trim(coalesce(business_name,
                        coalesce(first_name,'') || ' ' || coalesce(last_name,''))) AS name,
                   document_number AS doc,
                   code AS extra
            FROM water_subscribers
            WHERE organization_id = :org
              AND (unaccent(lower(coalesce(first_name,'') || ' ' || coalesce(last_name,''))) LIKE :like
                   OR unaccent(lower(coalesce(business_name,''))) LIKE :like
                   OR coalesce(document_number,'') LIKE :like_doc
                   OR lower(coalesce(code,'')) LIKE :like)
            LIMIT 8
        """,
        "subtitle": "Suscriptor de acueducto · {extra}",
        "route": "/water/subscribers",
    },
]


async def universal_search(
    db: AsyncSession, org_id: uuid.UUID, query: str, *, limit: int = 20,
) -> list[GraphHit]:
    """Busca una entidad en todos los módulos. Tolera nombre o documento."""
    raw = (query or "").strip()
    if len(raw) < 2:
        return []
    q = _strip_accents(raw)  # sin acentos para columnas unaccent()
    params = {"org": org_id, "like": f"%{q}%", "like_doc": f"%{raw.lower()}%"}
    hits: list[GraphHit] = []
    for src in _SOURCES:
        try:
            rows = (await db.execute(text(src["sql"]), params)).mappings().all()
        except Exception:
            continue  # una tabla ausente no debe romper la búsqueda global
        for r in rows:
            name = (r.get("name") or "").strip() or "(sin nombre)"
            extra = r.get("extra") or ""
            route = src["route"].format(id=r["id"]) if src.get("route") else None
            hits.append(GraphHit(
                module=src["module"], entity_type=src["entity_type"],
                entity_id=r["id"], display_name=name,
                document_number=r.get("doc"),
                subtitle=src["subtitle"].format(extra=extra).rstrip(" ·"),
                route=route,
            ))
    return hits[:limit]


async def resolve_person(
    db: AsyncSession, org_id: uuid.UUID, query: str,
) -> list[PersonNode]:
    """Agrupa los hits por documento (o nombre) → personas unificadas (Savvy Graph)."""
    hits = await universal_search(db, org_id, query)
    by_key: dict[str, PersonNode] = {}
    for h in hits:
        key = (h.document_number or h.display_name).strip().lower()
        node = by_key.get(key)
        if node is None:
            node = PersonNode(display_name=h.display_name, document_number=h.document_number)
            by_key[key] = node
        node.hits.append(h)
    # Personas con presencia en más módulos primero (lo interesante del grafo).
    return sorted(by_key.values(), key=lambda n: len(n.hits), reverse=True)
