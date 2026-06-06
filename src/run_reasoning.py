from pathlib import Path
from typing import Iterable, Set, Tuple

from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef, BNode
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
    graph.bind("owl", OWL)

    if not GROUP_ONTOLOGY.exists():
        raise FileNotFoundError(f"Missing required file: {GROUP_ONTOLOGY}")

    graph.parse(GROUP_ONTOLOGY, format="turtle")

    if COURSE_ONTOLOGY.exists():
        graph.parse(COURSE_ONTOLOGY, format="turtle")
    else:
        print(f"[Warning] Course ontology not found: {COURSE_ONTOLOGY}")
        print("[Warning] Continuing with group-ontology.ttl only.")

    return graph


def add_new_triples(graph: Graph, triples: Set[Tuple]) -> int:
    added_count = 0

    for triple in triples:
        if triple not in graph:
            graph.add(triple)
            added_count += 1

    return added_count


def infer_subclass_types(graph: Graph) -> int:
    """
    RDFS subclass rule:
    If x rdf:type C and C rdfs:subClassOf D, infer x rdf:type D.
    """
    inferred = set()

    for instance, cls in graph.subject_objects(RDF.type):
        if isinstance(instance, BNode):
            continue

        for superclass in graph.objects(cls, RDFS.subClassOf):
            if isinstance(superclass, URIRef):
                inferred.add((instance, RDF.type, superclass))

    return add_new_triples(graph, inferred)


def infer_existential_restrictions(graph: Graph) -> int:
    """
    OWL restriction rule for the homework pattern:
    If C rdfs:subClassOf [
        owl:onProperty P ;
        owl:someValuesFrom V
    ],
    and x rdf:type C,
    infer x P V.
    """
    inferred = set()

    for cls, restriction in graph.subject_objects(RDFS.subClassOf):
        if not isinstance(restriction, BNode):
            continue

        properties = list(graph.objects(restriction, OWL.onProperty))
        values = list(graph.objects(restriction, OWL.someValuesFrom))

        if not properties or not values:
            continue

        for prop in properties:
            for value_cls in values:
                for instance in graph.subjects(RDF.type, cls):
                    if isinstance(instance, BNode):
                        continue
                    inferred.add((instance, prop, value_cls))

    return add_new_triples(graph, inferred)


def is_subclass_or_self(graph: Graph, cls: URIRef, target: URIRef) -> bool:
    """
    Return True if cls == target or cls is connected to target by rdfs:subClassOf*.
    """
    if cls == target:
        return True

    visited = set()
    stack = [cls]

    while stack:
        current = stack.pop()

        if current in visited:
            continue
        visited.add(current)

        for superclass in graph.objects(current, RDFS.subClassOf):
            if superclass == target:
                return True
            if isinstance(superclass, URIRef):
                stack.append(superclass)

    return False


def infer_graspable_objects(graph: Graph) -> int:
    """
    Graspability classification rule:
    If x is a cap:PhysicalObject, and x cap:hasAffordance A,
    where A is cap:GraspingAffordance or a subclass of it,
    infer x rdf:type cap:GraspableObject.
    """
    inferred = set()

    for obj in graph.subjects(RDF.type, CAP.PhysicalObject):
        for affordance in graph.objects(obj, CAP.hasAffordance):
            if isinstance(affordance, URIRef) and is_subclass_or_self(
                graph,
                affordance,
                CAP.GraspingAffordance,
            ):
                inferred.add((obj, RDF.type, CAP.GraspableObject))

    return add_new_triples(graph, inferred)


def infer_level_qualified_objects(graph: Graph) -> int:
    """
    Group-specific inference:
    If x is a cap:PhysicalObject and x g12:hasTaskLevel L,
    where L rdf:type g12:TaskLevel, infer x rdf:type g12:LevelQualifiedObject.
    """
    inferred = set()

    for obj in graph.subjects(RDF.type, CAP.PhysicalObject):
        for level in graph.objects(obj, G12.hasTaskLevel):
            if (level, RDF.type, G12.TaskLevel) in graph:
                inferred.add((obj, RDF.type, G12.LevelQualifiedObject))

    return add_new_triples(graph, inferred)


def run_inference(graph: Graph, max_iterations: int = 20) -> int:
    """
    Run inference rules until no new triples are added.
    """
    total_added = 0

    for iteration in range(1, max_iterations + 1):
        added_this_round = 0

        added_this_round += infer_subclass_types(graph)
        added_this_round += infer_existential_restrictions(graph)
        added_this_round += infer_graspable_objects(graph)
        added_this_round += infer_level_qualified_objects(graph)

        print(f"[Inference] Iteration {iteration}: added {added_this_round} triple(s).")
        total_added += added_this_round

        if added_this_round == 0:
            break
    else:
        print("[Warning] Inference stopped because max_iterations was reached.")

    return total_added


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

    headers = ["obj", "name", "objectLabel", "role"]
    data = []

    for row in rows:
        data.append([
            shorten(getattr(row, "obj", None)),
            shorten(getattr(row, "name", None)),
            shorten(getattr(row, "objectLabel", None)),
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

    print("[Step 2] Running OWL/RDFS-style lightweight inference...")
    added_count = run_inference(graph)
    print(f"[OK] Added {added_count} inferred triple(s) in total.")

    print("[Step 3] Saving inferred graph...")
    save_inferred_graph(graph)

    print("[Step 4] Running SPARQL query over inferred graph...")
    output_text = run_graspable_query(graph)

    print("\n=== Graspable Objects ===")
    print(output_text)


if __name__ == "__main__":
    main()
