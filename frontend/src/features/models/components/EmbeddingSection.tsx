"use client";

import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { Button } from "@/shared/ui/Button";
import type { FamilySummary } from "@/features/developer/api";

interface EmbeddingSectionProps {
  families: FamilySummary[];
  onDownload?: (modelId: string) => void;
  onViewDetail?: (family: string) => void;
}

export function EmbeddingSection({ families, onDownload, onViewDetail }: EmbeddingSectionProps) {
  if (families.length === 0) return null;

  return (
    <div>
      <h3 className="text-sm font-semibold text-text-primary mb-3">
        Embedding Models
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {families.map((fam) => (
          <Card key={fam.family} className="p-4">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-medium text-text-primary">
                {fam.display_name}
              </h4>
              <Badge variant="default">
                {fam.model_count} variant{fam.model_count !== 1 ? "s" : ""}
              </Badge>
            </div>

            <div className="space-y-1 text-xs text-text-secondary mb-3">
              {fam.embedding_dim && (
                <p>{fam.embedding_dim} dimensions</p>
              )}
              <p>
                Context:{" "}
                {fam.context_range[0] >= 1000
                  ? `${Math.round(fam.context_range[0] / 1000)}K`
                  : fam.context_range[0]}
              </p>
              {fam.license && <p>{fam.license}</p>}
            </div>

            <div className="flex items-center gap-2">
              {fam.default_variant.downloaded ? (
                <Badge variant="success">Installed</Badge>
              ) : (
                onDownload && (
                  <Button
                    size="sm"
                    onClick={() => onDownload(fam.default_variant.model_id)}
                  >
                    Download
                  </Button>
                )
              )}
              {onViewDetail && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => onViewDetail(fam.family)}
                >
                  View Details
                </Button>
              )}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
