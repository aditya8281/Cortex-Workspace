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
import { useWorkspaceIntelligence, useRepositoryProfiles } from "@/hooks/useIntelligence";

export function KnowledgeGraphView() {
  const { data: workspace } = useWorkspaceIntelligence();
  const { data: repos = [] } = useRepositoryProfiles();

  const { nodes, edges } = useMemo(() => {
    const nodes: Node[] = [];
    const edges: Edge[] = [];
    
    // Define layout center coordinate
    const centerX = 500;
    const centerY = 350;

    // 1. Center Workspace Node
    const workspaceId = "workspace";
    nodes.push({
      id: workspaceId,
      position: { x: centerX, y: centerY },
      data: { label: workspace?.project_name ?? "Workspace" },
      style: {
        background: "#121a2b",
        border: "2px solid #5b9dff",
        color: "#e8eef8",
        borderRadius: "12px",
        padding: "14px 18px",
        fontSize: "14px",
        fontWeight: "bold",
        boxShadow: "0 0 20px rgba(91, 157, 255, 0.25)",
      },
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
    });

    // 2. Repositories (Circle 1 - Inner - Radius 180)
    repos.forEach((repo, i) => {
      const id = `repo-${repo.name}`;
      const angle = (i / Math.max(repos.length, 1)) * Math.PI * 2;
      nodes.push({
        id,
        position: {
          x: centerX + Math.cos(angle) * 180,
          y: centerY + Math.sin(angle) * 180,
        },
        data: { label: repo.name },
        style: {
          background: "#0c1220",
          border: "1px solid #1e2a42",
          color: "#e8eef8",
          borderRadius: "8px",
          padding: "8px 12px",
          fontSize: "12px",
          boxShadow: "0 4px 6px rgba(0, 0, 0, 0.15)",
        },
      });
      edges.push({
        id: `e-repo-${repo.name}`,
        source: workspaceId,
        target: id,
        label: "contains",
        style: { stroke: "#64748b" },
      });
    });

    // 3. Architectural Concepts (Circle 2 - Middle - Radius 320)
    const concepts = workspace?.concepts ?? [];
    concepts.forEach((concept, i) => {
      const id = `concept-${concept}`;
      // Offset starting angle to interleave with repositories
      const angle = (i / Math.max(concepts.length, 1)) * Math.PI * 2 + Math.PI / 4;
      nodes.push({
        id,
        position: {
          x: centerX + Math.cos(angle) * 320,
          y: centerY + Math.sin(angle) * 320,
        },
        data: { label: concept },
        style: {
          background: "#11221b",
          border: "1px solid #10b981",
          color: "#a7f3d0",
          borderRadius: "8px",
          padding: "8px 12px",
          fontSize: "11px",
          boxShadow: "0 4px 8px rgba(16, 185, 129, 0.1)",
        },
      });
      edges.push({
        id: `e-concept-${concept}`,
        source: workspaceId,
        target: id,
        label: "concept",
        style: { stroke: "#10b981", strokeDasharray: "5 5" },
      });
    });

    // 4. Knowledge Graph Codebase Relationships (Circle 3 - Outer - Radius 480)
    const kgEdges = workspace?.knowledge_graph?.edges ?? [];
    
    // Collect all unique entity labels from the edges to construct nodes
    const kgEntities = new Set<string>();
    kgEdges.forEach((edge) => {
      kgEntities.add(edge.source);
      kgEntities.add(edge.target);
    });

    const kgEntitiesArray = Array.from(kgEntities);
    kgEntitiesArray.forEach((entity, i) => {
      const id = `kg-${entity}`;
      const angle = (i / Math.max(kgEntitiesArray.length, 1)) * Math.PI * 2 - Math.PI / 8;
      
      // Differentiate file vs symbol styling
      const isFile = entity.includes("/") || entity.endsWith(".py") || entity.endsWith(".ts") || entity.endsWith(".tsx");
      const bg = isFile ? "#1e1b4b" : "#172554";
      const border = isFile ? "#4f46e5" : "#2563eb";
      const color = isFile ? "#cbd5e1" : "#93c5fd";

      nodes.push({
        id,
        position: {
          x: centerX + Math.cos(angle) * 480,
          y: centerY + Math.sin(angle) * 480,
        },
        data: { label: entity },
        style: {
          background: bg,
          border: `1px solid ${border}`,
          color: color,
          borderRadius: "6px",
          padding: "6px 10px",
          fontSize: "10px",
          boxShadow: "0 2px 4px rgba(0, 0, 0, 0.2)",
        },
      });
    });

    // Map the actual relationships to ReactFlow edges
    kgEdges.forEach((edge, i) => {
      edges.push({
        id: `e-kg-${i}-${edge.source}-${edge.target}`,
        source: `kg-${edge.source}`,
        target: `kg-${edge.target}`,
        label: edge.relation,
        animated: true,
        style: { stroke: "#3b82f6" },
      });
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
