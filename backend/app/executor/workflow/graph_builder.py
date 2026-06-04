from __future__ import annotations

from collections import defaultdict, deque

from backend.app.executor.tool_registry import ToolRegistry
from backend.app.executor.workflow.models import WorkflowGraph, WorkflowNode, WorkflowPlan


class WorkflowGraphBuilder:
    """
    Convert a structured workflow plan into a validated DAG.
    """

    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def build(self, plan: WorkflowPlan) -> WorkflowGraph:
        nodes: list[WorkflowNode] = []
        edges: list[tuple[str, str]] = []
        step_id_to_node_id: dict[int, str] = {}

        for step in plan.steps:
            resolved_tool = self.registry.resolve_name(step.tool)
            if not self.registry.get(resolved_tool):
                raise ValueError(f"Tool '{step.tool}' is not available in the registry.")

            node_id = f"step_{step.id}"
            step_id_to_node_id[step.id] = node_id
            nodes.append(
                WorkflowNode(
                    id=node_id,
                    step_id=step.id,
                    tool=resolved_tool,
                    args=dict(step.args),
                    depends_on=[],
                    fallback_tools=[self.registry.resolve_name(tool) for tool in step.fallback_tools],
                    critical=step.critical,
                    description=step.description,
                )
            )

        for node in nodes:
            plan_step = next(step for step in plan.steps if step.id == node.step_id)
            node.depends_on = [step_id_to_node_id[dep] for dep in plan_step.depends_on]
            for dep in node.depends_on:
                edges.append((dep, node.id))

        self._validate(nodes)
        layers = self._topological_layers(nodes)
        return WorkflowGraph(nodes=nodes, edges=edges, layers=layers, plan=plan)

    def _validate(self, nodes: list[WorkflowNode]) -> None:
        node_ids = {node.id for node in nodes}

        for node in nodes:
            if node.id in node.depends_on:
                raise ValueError(f"Self dependency detected for node '{node.id}'.")
            for dep in node.depends_on:
                if dep not in node_ids:
                    raise ValueError(f"Invalid dependency '{dep}' for node '{node.id}'.")

        visited: set[str] = set()
        stack: set[str] = set()
        adjacency = defaultdict(list)
        for node in nodes:
            for dep in node.depends_on:
                adjacency[dep].append(node.id)

        def dfs(node_id: str):
            if node_id in stack:
                raise ValueError(f"Cycle detected at '{node_id}'.")
            if node_id in visited:
                return
            visited.add(node_id)
            stack.add(node_id)
            for child in adjacency.get(node_id, []):
                dfs(child)
            stack.remove(node_id)

        for node in nodes:
            dfs(node.id)

    def _topological_layers(self, nodes: list[WorkflowNode]) -> list[list[str]]:
        indegree = {node.id: len(node.depends_on) for node in nodes}
        adjacency = defaultdict(list)
        for node in nodes:
            for dep in node.depends_on:
                adjacency[dep].append(node.id)

        queue = deque(sorted([node_id for node_id, count in indegree.items() if count == 0]))
        layers: list[list[str]] = []
        visited = set()

        while queue:
            current_layer: list[str] = []
            for _ in range(len(queue)):
                node_id = queue.popleft()
                if node_id in visited:
                    continue
                visited.add(node_id)
                current_layer.append(node_id)

            if not current_layer:
                break

            layers.append(current_layer)

            next_nodes: list[str] = []
            for node_id in current_layer:
                for child in adjacency.get(node_id, []):
                    indegree[child] -= 1
                    if indegree[child] == 0:
                        next_nodes.append(child)

            for child in sorted(next_nodes):
                queue.append(child)

        if len(visited) != len(nodes):
            remaining = [node.id for node in nodes if node.id not in visited]
            raise ValueError(f"Unable to resolve topological order for nodes: {remaining}")

        return layers
