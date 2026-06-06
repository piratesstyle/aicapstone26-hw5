# Homework 5 Report

## Ontology-based Semantic Grounding

### Group 12

---

# 1. Introduction

The goal of this homework is to build an ontology that enables a robot agent to semantically ground the objects observed in its environment and infer which objects are graspable.

Our final project is based on the **Toy Block Collection** task. Therefore, instead of modeling unrelated scenarios, the ontology focuses on the objects that actually appear in our project environment. In addition to the entry-level setting, we also model the advanced-level objects used in our project.

The ontology combines RDF, RDFS, and OWL constructs together with a lightweight RDFLib-based reasoning workflow to derive semantic knowledge from the modeled objects.

---

# 2. Repository Structure

The repository is organized as follows:

```text
hw5/
├── ontology/
│   ├── group-ontology.ttl
│   ├── inferred-results.ttl
│   └── imports/
│       └── course-affordance.ttl
├── queries/
│   └── graspable_objects.rq
├── results/
│   └── graspable_objects_output.txt
├── src/
│   └── run_reasoning.py
└── README.md
```

The provided `course-affordance.ttl` is reused as the shared course ontology, while all other files are implemented by our group.

---

# 3. Ontology Design

## 3.1 Namespace Policy

Two namespaces are used in this project.

| Namespace | Purpose                            |
| --------- | ---------------------------------- |
| `cap:`    | Shared course ontology vocabulary  |
| `g12:`    | Group-specific ontology extensions |

The `cap:` namespace provides common robotics concepts such as object types, affordances, and task roles. The `g12:` namespace contains the classes, properties, and individuals introduced specifically for our project.

---

## 3.2 Reused Course Ontology

The ontology reuses the following concepts from the course ontology:

### Object Types

* `cap:ToyBlock`
* `cap:Basket`
* `cap:PhysicalObject`

### Task Roles

* `cap:CollectableObject`
* `cap:ContainerTarget`

### Affordances

* `cap:GraspingAffordance`
* `cap:ContainmentAffordance`

### Properties

* `cap:hasAffordance`
* `cap:hasTaskRole`
* `cap:hasObjectLabel`
* `cap:hasPoseFrame`
* `cap:hasColor`

---

## 3.3 Group-specific Extensions

To better describe our project scenario, we introduce several new ontology entities.

### Classes

* `g12:TaskLevel`
* `g12:LevelQualifiedObject`

`TaskLevel` distinguishes whether an object belongs to the entry-level task or the advanced-level task.

`LevelQualifiedObject` is defined through an OWL equivalent-class expression:

* the object must be a `cap:PhysicalObject`
* the object must have at least one `g12:hasTaskLevel`

This definition demonstrates the use of OWL class definitions and existential restrictions.

### Object Property

* `g12:hasTaskLevel`

This property associates an object with the corresponding task level.

### Datatype Property

* `g12:hasSimulationName`

This property records the object identifier used in the simulation environment.

---

# 4. Task Object Modeling

Our ontology models the actual objects used in the project.

## Entry-level Task

### Container

* WhiteBasket

### Collectable Objects

* RedToyBlock
* GreenToyBlock
* BlueToyBlock

---

## Advanced-level Task

### Containers

* RedBasket
* GreenBasket
* BlueBasket

### Collectable Objects

* RedToyBlock
* GreenToyBlock
* BlueToyBlock

The toy blocks are shared between both task levels, while different baskets are used for different scenarios.

Each object instance contains semantic information including:

* object type
* task role
* affordance
* object label
* pose frame
* task level
* simulation identifier

This design allows the ontology to closely match the actual project environment.

---

# 5. Reasoning Workflow

The reasoning workflow is implemented using RDFLib.

Instead of manually asserting all `cap:GraspableObject` instances, the system derives new knowledge by applying several semantic inference rules.

## Rule 1: RDFS Subclass Propagation

If

```
x rdf:type C
C rdfs:subClassOf D
```

then infer

```
x rdf:type D
```

---

## Rule 2: OWL Existential Restriction Materialization

If

```
C rdfs:subClassOf [
    owl:onProperty P ;
    owl:someValuesFrom V
]
```

and

```
x rdf:type C
```

then infer

```
x P V
```

This rule supports the OWL modeling pattern used by the course ontology.

---

## Rule 3: Graspability Classification

If

* the object is a `cap:PhysicalObject`, and
* it has an affordance that is `cap:GraspingAffordance` (or one of its subclasses),

then infer

```
x rdf:type cap:GraspableObject
```

This is the main reasoning mechanism required by the homework.

---

## Rule 4: Task-level Classification

If

* the object is a `cap:PhysicalObject`, and
* it has a valid `g12:hasTaskLevel` relation,

then infer

```
x rdf:type g12:LevelQualifiedObject
```

This rule supports our group-specific ontology extension.

---

# 6. SPARQL Query Design

The repository includes the query:

```
queries/graspable_objects.rq
```

The query retrieves all inferred instances of

```
cap:GraspableObject
```

together with their labels and task roles.

The query is executed on the inferred graph rather than the raw ontology graph.

---

# 7. Inference Results

After executing the reasoning workflow, the following objects are inferred as graspable:

* RedToyBlock
* GreenToyBlock
* BlueToyBlock

These objects possess the semantic affordance required for robotic grasping and are therefore classified as `cap:GraspableObject`.

The inferred graph is exported to:

```
ontology/inferred-results.ttl
```

The query results are stored in:

```
results/graspable_objects_output.txt
```

---

# 8. Design Choices and Limitations

## Design Choices

* Focus on the actual project scenario.
* Introduce task-level semantics for entry-level and advanced-level tasks.
* Reuse the provided course ontology whenever possible.
* Implement reasoning through RDFLib with OWL/RDFS-inspired rules.

## Limitations

The current implementation is a lightweight rule engine rather than a complete OWL DL reasoner.

Although it supports the OWL patterns required for this homework, it does not implement the full OWL semantics provided by dedicated reasoners such as HermiT or Pellet.

---

# 9. Team Member Contributions

| Student ID | Name     | Contribution                                                                                                              |
| ---------- | -------- | ------------------------------------------------------------------------------------------------------------------------- |
| 112101016   | 黃昱傑 | Designed the ontology structure, namespace policy, and group-specific OWL/RDFS entities.                                  |
| 112550108   | 梁家熏 | Implemented the object instances and semantic annotations, including task roles, affordances, and task-level information. |
| 112550029   | 霍朝元 | Implemented the RDFLib reasoning workflow, inference rules, and SPARQL queries.                                           |
| 112550125   | 林程亮 | Organized the repository, verified the inference results, and completed the README and report documentation.              |
