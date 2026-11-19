from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import TypedDict

from sqlalchemy import inspect, select

from app.main import Municipality, SessionLocal, State


class MunicipalitySeed(TypedDict):
    code: str
    name: str


class StateSeed(TypedDict):
    name: str
    municipalities: list[MunicipalitySeed]


CATALOG_PATH = Path(__file__).resolve().parent / "data" / "mexico_locations.json"


def load_catalog() -> list[StateSeed]:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    states = catalog.get("states")
    if not isinstance(states, list) or len(states) != 32:
        raise ValueError("El catálogo de INEGI debe contener los 32 estados.")

    validated_states: list[StateSeed] = []
    seen_state_names: set[str] = set()
    seen_codes: set[str] = set()

    for state in states:
        name = state.get("name") if isinstance(state, dict) else None
        municipalities = state.get("municipalities") if isinstance(state, dict) else None
        if not isinstance(name, str) or not name.strip() or name in seen_state_names:
            raise ValueError("El catálogo contiene un estado inválido o duplicado.")
        if not isinstance(municipalities, list) or not municipalities:
            raise ValueError(f"El estado {name} no tiene municipios.")

        validated_municipalities: list[MunicipalitySeed] = []
        for municipality in municipalities:
            code = municipality.get("code") if isinstance(municipality, dict) else None
            municipality_name = municipality.get("name") if isinstance(municipality, dict) else None
            if (
                not isinstance(code, str)
                or len(code) != 5
                or not code.isdigit()
                or code in seen_codes
                or not isinstance(municipality_name, str)
                or not municipality_name.strip()
            ):
                raise ValueError(f"El catálogo contiene un municipio inválido en {name}.")
            seen_codes.add(code)
            validated_municipalities.append(
                {"code": code, "name": municipality_name}
            )

        seen_state_names.add(name)
        validated_states.append(
            {"name": name, "municipalities": validated_municipalities}
        )

    if len(seen_codes) != 2478:
        raise ValueError(f"El catálogo debe contener 2,478 municipios; contiene {len(seen_codes)}.")

    return validated_states


def seed_mexico_locations() -> tuple[int, int, int]:
    states_seed = load_catalog()
    states_added = 0
    municipalities_added = 0
    municipalities_updated = 0

    with SessionLocal.begin() as db:
        table_columns = {
            column["name"]
            for column in inspect(db.get_bind()).get_columns("municipalities")
        }
        if "code" not in table_columns:
            raise RuntimeError(
                "Aplica primero la migración con `alembic upgrade head`."
            )

        states_by_name = {
            state.name: state
            for state in db.scalars(select(State)).all()
        }
        municipalities_by_code: dict[str, Municipality] = {}
        municipalities_by_state_name: dict[tuple[int, str], list[Municipality]] = defaultdict(list)
        for municipality in db.scalars(select(Municipality)).all():
            if municipality.code:
                municipalities_by_code[municipality.code] = municipality
            else:
                municipalities_by_state_name[
                    (municipality.state_id, municipality.name)
                ].append(municipality)

        for state_data in states_seed:
            state = states_by_name.get(state_data["name"])
            if state is None:
                state = State(name=state_data["name"])
                db.add(state)
                db.flush()
                states_by_name[state.name] = state
                states_added += 1

            for municipality_data in state_data["municipalities"]:
                municipality = municipalities_by_code.get(municipality_data["code"])
                if municipality is not None:
                    if municipality.state_id != state.id:
                        raise ValueError(
                            f"La clave INEGI {municipality_data['code']} ya pertenece a otro estado."
                        )
                    if municipality.name != municipality_data["name"]:
                        municipality.name = municipality_data["name"]
                        municipalities_updated += 1
                    continue

                legacy_matches = municipalities_by_state_name[
                    (state.id, municipality_data["name"])
                ]
                municipality = next(
                    (item for item in legacy_matches if item.code is None),
                    None,
                )
                if municipality is not None:
                    municipality.code = municipality_data["code"]
                    municipality.is_other = False
                    municipalities_by_code[municipality.code] = municipality
                    municipalities_updated += 1
                    continue

                municipality = Municipality(
                    state_id=state.id,
                    code=municipality_data["code"],
                    name=municipality_data["name"],
                    is_other=False,
                )
                db.add(municipality)
                municipalities_by_code[municipality.code] = municipality
                municipalities_by_state_name[
                    (state.id, municipality.name)
                ].append(municipality)
                municipalities_added += 1

    return states_added, municipalities_added, municipalities_updated


if __name__ == "__main__":
    added_states, added_municipalities, updated_municipalities = seed_mexico_locations()
    print(
        "Catálogo INEGI aplicado: "
        f"{added_states} estados nuevos, "
        f"{added_municipalities} municipios nuevos y "
        f"{updated_municipalities} municipios asociados a su clave oficial."
    )
