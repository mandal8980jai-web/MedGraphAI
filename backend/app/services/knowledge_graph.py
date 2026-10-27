import networkx as nx
from typing import List, Dict, Any
from app.services.interaction_engine import (
    load_medicine_catalog,
    resolve_medicine_details,
    _extract_medicine_field
)


def build_knowledge_graph(medicines: List[Any], interactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build a NetworkX graph containing:
      - medicine nodes
      - ingredient nodes
      - 'contains' edges (medicine -> ingredient)
      - 'interacts' edges (medicine <-> medicine) with severity and notes
    Returns a dictionary with plain 'nodes' and 'edges' lists for the frontend.
    """
    G = nx.Graph()

    catalog = load_medicine_catalog()
    catalog_map = {m["id"]: m for m in catalog if "id" in m}

    # 1. Add medicine nodes & ingredient nodes & contains edges
    med_col = 0
    ing_col = 0
    ing_positions = {}

    for idx, med in enumerate(medicines):
        resolved = resolve_medicine_details(med, catalog_map)
        med_id = resolved["id"]
        med_label = resolved["name_text"] or _extract_medicine_field(med, "name_text", f"Medicine {idx+1}")
        is_known = resolved["found_in_list"]
        strength = _extract_medicine_field(med, "strength")
        dose = _extract_medicine_field(med, "dose")
        match_status = _extract_medicine_field(med, "match_status", "matched" if is_known else "not_found")

        # Position medicine in top tier
        x_pos = med_col * 280 + 60
        y_pos = 60
        med_col += 1

        G.add_node(
            med_id,
            label=med_label,
            type="medicine",
            is_known=is_known,
            strength=strength,
            dose=dose,
            match_status=match_status,
            x=x_pos,
            y=y_pos
        )

        # Add contains edges for each active ingredient
        for ing in resolved["ingredients"]:
            ing_id = ing.lower()
            if not G.has_node(ing_id):
                ing_x = ing_col * 240 + 100
                ing_y = 280
                ing_positions[ing_id] = (ing_x, ing_y)
                ing_col += 1

                G.add_node(
                    ing_id,
                    label=ing_id.title(),
                    type="ingredient",
                    is_known=True,
                    x=ing_positions[ing_id][0],
                    y=ing_positions[ing_id][1]
                )

            G.add_edge(
                med_id,
                ing_id,
                type="contains"
            )

    # 2. Add configured interaction edges with severity between interacting medicines
    for inter in interactions:
        pair = inter.get("medicines", [])
        if len(pair) == 2:
            m1, m2 = str(pair[0]), str(pair[1])
            if G.has_node(m1) and G.has_node(m2):
                G.add_edge(
                    m1,
                    m2,
                    type="interacts",
                    severity=inter.get("severity", "moderate"),
                    rule_id=inter.get("rule_id", ""),
                    note=inter.get("note", ""),
                    source_label=inter.get("source_label", "Sample demo rule, verify with a pharmacist")
                )

    # 3. Format as clean lists for frontend consumption
    nodes = []
    for node_id, data in G.nodes(data=True):
        nodes.append({
            "id": str(node_id),
            "label": data.get("label", str(node_id)),
            "type": data.get("type", "medicine"),
            "is_known": data.get("is_known", True),
            "strength": data.get("strength"),
            "dose": data.get("dose"),
            "match_status": data.get("match_status", "matched"),
            "position": {
                "x": data.get("x", 0),
                "y": data.get("y", 0)
            }
        })

    edges = []
    for u, v, data in G.edges(data=True):
        edge_id = f"{u}-{v}-{data.get('type', 'link')}"
        edges.append({
            "id": edge_id,
            "from": str(u),
            "to": str(v),
            "source": str(u),
            "target": str(v),
            "type": data.get("type", "contains"),
            "severity": data.get("severity"),
            "rule_id": data.get("rule_id"),
            "note": data.get("note"),
            "source_label": data.get("source_label")
        })

    return {
        "nodes": nodes,
        "edges": edges
    }
