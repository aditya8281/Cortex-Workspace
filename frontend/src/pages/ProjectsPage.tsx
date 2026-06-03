import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";

export function ProjectsPage() {
  const navigate = useNavigate();
  return (
    <div className="flex h-full items-center justify-center p-8">
      <Card className="max-w-md text-center">
        <CardContent className="space-y-4 p-8">
          <h2 className="text-lg font-semibold">Projects</h2>
          <p className="text-sm text-cortex-muted">
            Project workspaces group repositories and memory. Cortex will auto-organize discovered git roots into projects during sync.
          </p>
          <Button onClick={() => navigate("/repositories")}>Browse repositories</Button>
        </CardContent>
      </Card>
    </div>
  );
}
