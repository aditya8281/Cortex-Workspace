import { useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  type Node,
  type Edge,
  Position,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useWorkspaceIntelligence } from "@/hooks/useIntelligence";
import { useRepositoryProfiles } from "@/hooks/useIntelligence";

export function KnowledgeGraphView() {
  const { data: workspace } = useWorkspaceIntelligence();
  const { data: repos = [] } = useRepositoryProfiles();

  const { nodes, edges } = useMemo(() => {
    const nodes: Node[] = [];
    const edges: Edge[] = [];
    const centerId = "workspace";
    nodes.push({
      id: centerId,
      position: { x: 400, y: 200 },
      data: { label: workspace?.project_name ?? "Workspace" },
      style: {
        background: "#121a2b",
        border: "1px solid #5b9dff",
        color: "#e8eef8",
        borderRadius: 12,
        padding: 12,
        fontSize: 13,
      },
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
    });

    repos.forEach((repo, i) => {
      const id = `repo-${i}`;
      const angle = (i / Math.max(repos.length, 1)) * Math.PI * 2;
      nodes.push({
        id,
        position: { x: 400 + Math.cos(angle) * 220, y: 200 + Math.sin(angle) * 160 },
        data: { label: repo.name },
        style: {
          background: "#0c1220",
          border: "1px solid #1e2a42",
          color: "#e8eef8",
          borderRadius: 10,
          fontSize: 12,
        },
      });
      edges.push({ id: `e-${id}`, source: centerId, target: id, label: "contains" });
    });

    workspace?.concepts.slice(0, 12).forEach((concept, i) => {
      const id = `concept-${i}`;
      nodes.push({
        id,
        position: { x: 80 + (i % 4) * 140, y: Math.floor(i / 4) * 80 },
        data: { label: concept },
        style: {
          background: "#1a2438",
          border: "1px solid #3dd68c55",
          color: "#e8eef8",
          fontSize: 11,
          borderRadius: 8,
        },
      });
      edges.push({ id: `ec-${id}`, source: centerId, target: id, label: "concept" });
    });

    workspace?.knowledge_graph.edges.slice(0, 15).forEach((edge, i) => {
      const sid = `kg-s-${i}`;
      const tid = `kg-t-${i}`;
      if (!nodes.find((n) => n.id === sid)) {
        nodes.push({
          id: sid,
          position: { x: 700, y: 80 + i * 40 },
          data: { label: edge.source },
          style: { fontSize: 10, padding: 6, borderRadius: 6, background: "#121a2b", border: "1px solid #1e2a42", color: "#8b9cb8" },
        });
      }
      if (!nodes.find((n) => n.id === tid)) {
        nodes.push({
          id: tid,
          position: { x: 900, y: 80 + i * 40 },
          data: { label: edge.target },
          style: { fontSize: 10, padding: 6, borderRadius: 6, background: "#121a2b", border: "1px solid #1e2a42", color: "#8b9cb8" },
        });
      }
      edges.push({ id: `kg-${i}`, source: sid, target: tid, label: edge.relation });
    });

    return { nodes, edges };
  }, [workspace, repos]);

  return (
    <div className="h-[calc(100vh-3.5rem)] w-full">
      <ReactFlow nodes={nodes} edges={edges} fitView className="bg-cortex-bg">
        <Background color="#1e2a42" gap={20} />
        <Controls />
        <MiniMap nodeColor="#5b9dff" maskColor="rgb(6 10 18 / 0.8)" />
      </ReactFlow>
    </div>
  );
}
