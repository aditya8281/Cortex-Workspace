"use client";

import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { StatusDot } from "@/shared/ui/StatusDot";
import { Button } from "@/shared/ui/Button";
import type { Agent } from "../api";

interface AgentCardProps {
  agent: Agent;
  onRun: (id: number) => void;
  onClick: (id: number) => void;
}

export function AgentCard({ agent, onRun, onClick }: AgentCardProps) {
  return (
    <Card
      className="p-4 cursor-pointer"
      hover
      onClick={() => onClick(agent.id)}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2.5 min-w-0">
          <StatusDot
            color={agent.is_active ? "success" : "warning"}
            pulse={agent.is_active}
          />
          <div className="min-w-0">
            <h3 className="text-sm font-medium text-text-primary truncate">
              {agent.name}
            </h3>
            {agent.description && (
              <p className="text-xs text-text-muted truncate mt-0.5">
                {agent.description}
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <Badge variant={agent.is_active ? "success" : "default"}>
            {agent.model_id}
          </Badge>
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              onRun(agent.id);
            }}
          >
            Run
          </Button>
        </div>
      </div>
      <div className="mt-3 flex items-center gap-4 text-xs text-text-muted">
        <span>{agent.run_count} runs</span>
        {agent.tools && agent.tools.length > 0 && (
          <span>{agent.tools.length} tools</span>
        )}
      </div>
    </Card>
  );
}
