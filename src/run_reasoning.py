#!/usr/bin/env python3
from pathlib import Path
from typing import Iterable

from rdflib import Graph, Namespace, RDF, RDFS, URIRef
from rdflib.query import ResultRow


BASE_DIR = Path(__file__).resolve().parents[1]

GROUP_ONTOLOGY = BASE_DIR / "ontology" / "group-ontology.ttl"
COURSE_ONTOLOGY = BASE_DIR / "ontology" / "imports" / "course-affordance.ttl"
INFERRED_OUTPUT = BASE_DIR / "ontology" / "inferred-results.ttl"

QUERY_FILE = BASE_DIR / "queries" / "graspable_objects.rq"
RESULT_OUTPUT = BASE_DIR / "results" / "graspable_objects_output.txt"

CAP = Namespace("https://hcis.io/ontology/aicapstone/2026/")
G12 = Namespace("https://hcis.io/ontology/aicapstone/2026/group12/")


def load_graph() -> Graph:
    graph = Graph()
    graph.bind("cap", CAP)
    graph.bind("g12", G12)
    graph.bind("rdf", RDF)
    graph.bind("rdfs", RDFS)

    if not GROUP_ONTOLOGY.exists():
        raise FileNotFoundError(f"Missing required file: {GROUP_ONTOLOGY}")

    graph.parse(GROUP_ONTOLOGY, format="turtle")

    if COURSE_ONTOLOGY.exists():
        graph.parse(COURSE_ONTOLOGY, format="turtle")
    else:
        print(f"[Warning] Course ontology not found: {COURSE_ONTOLOGY}")
        print("[Warning] Continuing with group-ontology.ttl only.")

    return graph


def infer_graspable_objects(graph: Graph) -> int:
    """
    Rule:
    (?obj cap:hasAffordance cap:GraspingAffordance)
        => (?obj rdf:type cap:GraspableObject)
    """
    inferred_triples = set()

    for obj in graph.subjects(CAP.hasAffordance, CAP.GraspingAffordance):
        inferred_triples.add((obj, RDF.type, CAP.GraspableObject))

    added_count = 0
    for triple in inferred_triples:
        if triple not in graph:
            graph.add(triple)
            added_count += 1

    return added_count


def save_inferred_graph(graph: Graph) -> None:
    INFERRED_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=INFERRED_OUTPUT, format="turtle")
    print(f"[OK] Inferred graph saved to {INFERRED_OUTPUT}")


def shorten(value) -> str:
    if value is None:
        return ""

    if isinstance(value, URIRef):
        value_str = str(value)
        if value_str.startswith(str(CAP)):
            return "cap:" + value_str.replace(str(CAP), "")
        if value_str.startswith(str(G12)):
            return "g12:" + value_str.replace(str(G12), "")

    return str(value)


def format_query_results(rows: Iterable[ResultRow]) -> str:
    rows = list(rows)

    headers = ["obj", "name", "label", "role"]
    data = []

    for row in rows:
        data.append([
            shorten(getattr(row, "obj", None)),
            shorten(getattr(row, "name", None)),
            shorten(getattr(row, "label", None)),
            shorten(getattr(row, "role", None)),
        ])

    widths = []
    for i in range(len(headers)):
        max_width = len(headers[i])
        for row in data:
            max_width = max(max_width, len(row[i]))
        widths.append(max_width)

    lines = []
    lines.append(" | ".join(headers[i].ljust(widths[i]) for i in range(len(headers))))
    lines.append("-+-".join("-" * widths[i] for i in range(len(headers))))

    for row in data:
        lines.append(" | ".join(row[i].ljust(widths[i]) for i in range(len(headers))))

    if not data:
        lines.append("(no results)")

    return "\n".join(lines) + "\n"


def run_graspable_query(graph: Graph) -> str:
    if not QUERY_FILE.exists():
        raise FileNotFoundError(f"Missing query file: {QUERY_FILE}")

    query_text = QUERY_FILE.read_text(encoding="utf-8")
    results = graph.query(query_text)

    output_text = format_query_results(results)

    RESULT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    RESULT_OUTPUT.write_text(output_text, encoding="utf-8")

    print(f"[OK] Query output saved to {RESULT_OUTPUT}")
    return output_text


def main() -> None:
    print("[Step 1] Loading RDF/Turtle files...")
    graph = load_graph()
    print(f"[OK] Loaded graph with {len(graph)} triples.")

    print("[Step 2] Running lightweight graspability inference...")
    added_count = infer_graspable_objects(graph)
    print(f"[OK] Added {added_count} inferred cap:GraspableObject triple(s).")

    print("[Step 3] Saving inferred graph...")
    save_inferred_graph(graph)

    print("[Step 4] Running SPARQL query over inferred graph...")
    output_text = run_graspable_query(graph)

    print("\n=== Graspable Objects ===")
    print(output_text)


if __name__ == "__main__":
    main()
