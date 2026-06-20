# Phase 10: Production Hardening

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Production-ready reliability, security, performance, and packaging. Test coverage, security hardening, performance optimization, Docker packaging, CI/CD.

**Architecture:** Comprehensive test suite covering all API endpoints, security header hardening, database connection pooling, response compression, optimized multi-stage Docker builds, and full CI/CD pipeline with integration tests.

**Tech Stack:** Python 3.12+, pytest, Next.js 15, Docker, GitHub Actions, Vitest

---

## Task 1: Backend Integration Tests

**Files:**
- Create: `tests/test_api_agents.py`
- Create: `tests/test_api_search.py`
- Create: `tests/test_api_conversations.py`
- Create: `tests/test_api_models.py`

All tests use the existing `conftest.py` fixtures: in-memory SQLite engine, `_db_session` autouse rollback, `mock_auth` for authenticated endpoints, `client` fixture, and `_mock_external_services` autouse mock.

### Step 1: Agent API tests

Create `tests/test_api_agents.py`:

```python
"""Integration tests for Agent CRUD, runs, steps, and feedback endpoints."""

import pytest


# ── Agent CRUD ──────────────────────────────────────────────────


def test_list_agents_empty(client, mock_auth):
    """List agents when none exist returns empty list."""
    r = client.get("/api/v1/agents")
    assert r.status_code == 200
    data = r.json()
    assert "agents" in data
    assert isinstance(data["agents"], list)
    assert len(data["agents"]) == 0


def test_create_agent(client, mock_auth):
    """Create a new agent and verify returned fields."""
    r = client.post(
        "/api/v1/agents",
        json={
            "name": "test-agent",
            "system_prompt": "You are a test agent.",
            "model_id": "local",
            "description": "A test agent",
            "tools": ["search", "code"],
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "created"
    agent = data["agent"]
    assert agent["name"] == "test-agent"
    assert agent["system_prompt"] == "You are a test agent."
    assert agent["model_id"] == "local"
    assert agent["is_active"] is True
    assert agent["id"] is not None


def test_create_agent_missing_name(client, mock_auth):
    """Create agent without name fails validation."""
    r = client.post(
        "/api/v1/agents",
        json={"system_prompt": "You are a test agent."},
    )
    assert r.status_code == 422


def test_create_agent_empty_system_prompt(client, mock_auth):
    """Create agent with empty system_prompt fails validation."""
    r = client.post(
        "/api/v1/agents",
        json={"name": "bad-agent", "system_prompt": ""},
    )
    assert r.status_code == 422


def test_get_agent(client, mock_auth):
    """Create then retrieve a specific agent."""
    create_r = client.post(
        "/api/v1/agents",
        json={"name": "get-agent", "system_prompt": "prompt"},
    )
    agent_id = create_r.json()["agent"]["id"]

    r = client.get(f"/api/v1/agents/{agent_id}")
    assert r.status_code == 200
    assert r.json()["agent"]["name"] == "get-agent"


def test_get_agent_not_found(client, mock_auth):
    """Get non-existent agent returns 404."""
    r = client.get("/api/v1/agents/99999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Agent not found"


def test_update_agent(client, mock_auth):
    """Create then update an agent's name."""
    create_r = client.post(
        "/api/v1/agents",
        json={"name": "old-name", "system_prompt": "prompt"},
    )
    agent_id = create_r.json()["agent"]["id"]

    r = client.put(
        f"/api/v1/agents/{agent_id}",
        json={"name": "new-name"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "updated"

    get_r = client.get(f"/api/v1/agents/{agent_id}")
    assert get_r.json()["agent"]["name"] == "new-name"


def test_update_agent_deactivate(client, mock_auth):
    """Deactivate an agent via update."""
    create_r = client.post(
        "/api/v1/agents",
        json={"name": "deactivate-me", "system_prompt": "prompt"},
    )
    agent_id = create_r.json()["agent"]["id"]

    r = client.put(f"/api/v1/agents/{agent_id}", json={"is_active": False})
    assert r.status_code == 200

    get_r = client.get(f"/api/v1/agents/{agent_id}")
    assert get_r.json()["agent"]["is_active"] is False


def test_delete_agent(client, mock_auth):
    """Create then delete an agent."""
    create_r = client.post(
        "/api/v1/agents",
        json={"name": "delete-me", "system_prompt": "prompt"},
    )
    agent_id = create_r.json()["agent"]["id"]

    r = client.delete(f"/api/v1/agents/{agent_id}")
    assert r.status_code == 200
    assert r.json()["status"] == "deleted"

    get_r = client.get(f"/api/v1/agents/{agent_id}")
    assert get_r.status_code == 404


def test_delete_agent_not_found(client, mock_auth):
    """Delete non-existent agent returns 404."""
    r = client.delete("/api/v1/agents/99999")
    assert r.status_code == 404


def test_list_agents_after_create(client, mock_auth):
    """List agents returns created agents."""
    client.post(
        "/api/v1/agents",
        json={"name": "list-agent-1", "system_prompt": "p1"},
    )
    client.post(
        "/api/v1/agents",
        json={"name": "list-agent-2", "system_prompt": "p2"},
    )

    r = client.get("/api/v1/agents")
    assert r.status_code == 200
    agents = r.json()["agents"]
    assert len(agents) >= 2
    names = {a["name"] for a in agents}
    assert "list-agent-1" in names
    assert "list-agent-2" in names


# ── Runs ────────────────────────────────────────────────────────


def test_create_run(client, mock_auth):
    """Create an agent then trigger a run."""
    create_r = client.post(
        "/api/v1/agents",
        json={"name": "run-agent", "system_prompt": "prompt"},
    )
    agent_id = create_r.json()["agent"]["id"]

    r = client.post(
        "/api/v1/agents/runs",
        json={"agent_id": agent_id, "input": "Hello agent"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "completed"
    assert "run" in data
    assert data["run"]["input"] == "Hello agent"


def test_create_run_nonexistent_agent(client, mock_auth):
    """Run with non-existent agent_id returns 404."""
    r = client.post(
        "/api/v1/agents/runs",
        json={"agent_id": 99999, "input": "test"},
    )
    assert r.status_code == 404


def test_list_runs(client, mock_auth):
    """List runs returns runs for the authenticated user."""
    create_r = client.post(
        "/api/v1/agents",
        json={"name": "list-runs-agent", "system_prompt": "prompt"},
    )
    agent_id = create_r.json()["agent"]["id"]

    client.post(
        "/api/v1/agents/runs",
        json={"agent_id": agent_id, "input": "run 1"},
    )

    r = client.get("/api/v1/agents/runs")
    assert r.status_code == 200
    runs = r.json()["runs"]
    assert isinstance(runs, list)
    assert len(runs) >= 1


def test_get_run(client, mock_auth):
    """Create a run then retrieve it with steps."""
    create_r = client.post(
        "/api/v1/agents",
        json={"name": "get-run-agent", "system_prompt": "prompt"},
    )
    agent_id = create_r.json()["agent"]["id"]

    run_r = client.post(
        "/api/v1/agents/runs",
        json={"agent_id": agent_id, "input": "get this run"},
    )
    run_id = run_r.json()["run"]["id"]

    r = client.get(f"/api/v1/agents/runs/{run_id}")
    assert r.status_code == 200
    data = r.json()
    assert "run" in data
    assert "steps" in data
    assert data["run"]["id"] == run_id


def test_get_run_not_found(client, mock_auth):
    """Get non-existent run returns 404."""
    r = client.get("/api/v1/agents/runs/99999")
    assert r.status_code == 404


def test_get_run_steps(client, mock_auth):
    """Create a run then get its steps."""
    create_r = client.post(
        "/api/v1/agents",
        json={"name": "steps-agent", "system_prompt": "prompt"},
    )
    agent_id = create_r.json()["agent"]["id"]

    run_r = client.post(
        "/api/v1/agents/runs",
        json={"agent_id": agent_id, "input": "step test"},
    )
    run_id = run_r.json()["run"]["id"]

    r = client.get(f"/api/v1/agents/runs/{run_id}/steps")
    assert r.status_code == 200
    assert "steps" in r.json()
    assert isinstance(r.json()["steps"], list)


# ── Feedback ────────────────────────────────────────────────────


def test_add_feedback(client, mock_auth):
    """Add feedback to a completed run."""
    create_r = client.post(
        "/api/v1/agents",
        json={"name": "feedback-agent", "system_prompt": "prompt"},
    )
    agent_id = create_r.json()["agent"]["id"]

    run_r = client.post(
        "/api/v1/agents/runs",
        json={"agent_id": agent_id, "input": "feedback test"},
    )
    run_id = run_r.json()["run"]["id"]

    r = client.post(
        f"/api/v1/agents/runs/{run_id}/feedback",
        json={"rating": 5, "comment": "Great run!"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "created"
    assert data["feedback"]["rating"] == 5
    assert data["feedback"]["comment"] == "Great run!"


def test_add_feedback_invalid_rating(client, mock_auth):
    """Feedback with rating outside 1-5 returns 400."""
    create_r = client.post(
        "/api/v1/agents",
        json={"name": "bad-feedback-agent", "system_prompt": "prompt"},
    )
    agent_id = create_r.json()["agent"]["id"]

    run_r = client.post(
        "/api/v1/agents/runs",
        json={"agent_id": agent_id, "input": "bad feedback"},
    )
    run_id = run_r.json()["run"]["id"]

    r = client.post(
        f"/api/v1/agents/runs/{run_id}/feedback",
        json={"rating": 10},
    )
    assert r.status_code == 400


def test_get_feedback(client, mock_auth):
    """Get feedback for a run returns feedback list."""
    create_r = client.post(
        "/api/v1/agents",
        json={"name": "get-feedback-agent", "system_prompt": "prompt"},
    )
    agent_id = create_r.json()["agent"]["id"]

    run_r = client.post(
        "/api/v1/agents/runs",
        json={"agent_id": agent_id, "input": "get feedback"},
    )
    run_id = run_r.json()["run"]["id"]

    client.post(
        f"/api/v1/agents/runs/{run_id}/feedback",
        json={"rating": 4, "comment": "Nice"},
    )

    r = client.get(f"/api/v1/agents/runs/{run_id}/feedback")
    assert r.status_code == 200
    feedback = r.json()["feedback"]
    assert len(feedback) >= 1
    assert feedback[0]["rating"] == 4


def test_unauthenticated_agents(client):
    """Agent endpoints require authentication."""
    assert client.get("/api/v1/agents").status_code in (401, 403)
    assert client.post("/api/v1/agents", json={}).status_code in (401, 403)
```

### Step 2: Search API tests

Create `tests/test_api_search.py`:

```python
"""Integration tests for unified search endpoints (POST and GET)."""

import pytest


def test_unified_search_post(client, mock_auth):
    """POST /search with valid query returns results structure."""
    r = client.post(
        "/api/v1/search",
        json={"query": "test search", "max_results": 5},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["query"] == "test search"
    assert "total" in data
    assert "results" in data
    assert isinstance(data["results"], list)
    assert data["total"] <= 5


def test_unified_search_get(client, mock_auth):
    """GET /search with q param returns results structure."""
    r = client.get("/api/v1/search?q=test+query&max_results=3")
    assert r.status_code == 200
    data = r.json()
    assert data["query"] == "test query"
    assert isinstance(data["results"], list)
    assert data["total"] <= 3


def test_search_empty_query_post(client, mock_auth):
    """POST /search with empty query fails validation."""
    r = client.post("/api/v1/search", json={"query": ""})
    assert r.status_code == 422


def test_search_empty_query_get(client, mock_auth):
    """GET /search with empty q fails validation."""
    r = client.get("/api/v1/search?q=")
    assert r.status_code == 422


def test_search_long_query(client, mock_auth):
    """POST /search with query exceeding max length fails validation."""
    long_query = "a" * 1001
    r = client.post("/api/v1/search", json={"query": long_query})
    assert r.status_code == 422


def test_search_with_filters(client, mock_auth):
    """POST /search with repo_id, node_type, language filters."""
    r = client.post(
        "/api/v1/search",
        json={
            "query": "function test",
            "repo_id": 1,
            "node_type": "function",
            "language": "python",
            "max_results": 10,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data["results"], list)


def test_search_max_results_bounds(client, mock_auth):
    """max_results must be between 1 and 50."""
    r = client.post("/api/v1/search", json={"query": "test", "max_results": 0})
    assert r.status_code == 422

    r = client.post("/api/v1/search", json={"query": "test", "max_results": 51})
    assert r.status_code == 422

    r = client.post("/api/v1/search", json={"query": "test", "max_results": 50})
    assert r.status_code == 200


def test_unauthenticated_search(client):
    """Search requires authentication."""
    r = client.post("/api/v1/search", json={"query": "test"})
    assert r.status_code in (401, 403)

    r = client.get("/api/v1/search?q=test")
    assert r.status_code in (401, 403)
```

### Step 3: Conversations/Chat tests

Create `tests/test_api_conversations.py`:

```python
"""Integration tests for chat/conversation endpoints.

Tests the memory-based chat flow: POST /api/memory for creating entries,
GET /api/memory for listing, and conversation-related user endpoints.
"""

import pytest


def test_memory_post(client, mock_auth):
    """Post a memory entry (chat message equivalent)."""
    r = client.post(
        "/api/memory",
        json={"title": "test memory", "content": "Hello from test"},
    )
    assert r.status_code == 200


def test_memory_get_requires_auth(client):
    """GET /api/memory requires authentication."""
    r = client.get("/api/memory")
    assert r.status_code == 401


def test_memory_post_requires_auth(client):
    """POST /api/memory requires authentication."""
    r = client.post(
        "/api/memory",
        json={"title": "unauth", "content": "should fail"},
    )
    assert r.status_code == 401


def test_memory_post_empty_content(client, mock_auth):
    """Post memory with empty content fails validation."""
    r = client.post(
        "/api/memory",
        json={"title": "empty", "content": ""},
    )
    assert r.status_code in (400, 422)


def test_profile_get_and_update(client, mock_auth):
    """Get profile then update bio."""
    r = client.get("/api/v1/me/profile")
    assert r.status_code == 200
    data = r.json()
    assert "username" in data

    r2 = client.put("/api/v1/me/profile", json={"bio": "test bio"})
    assert r2.status_code == 200
    assert r2.json()["bio"] == "test bio"


def test_profile_requires_auth(client):
    """Profile endpoints require authentication."""
    assert client.get("/api/v1/me/profile").status_code in (401, 403)
    assert client.put("/api/v1/me/profile", json={"bio": "x"}).status_code in (401, 403)


def test_users_requires_admin(client, mock_auth):
    """Users list requires admin role. Regular user gets 403."""
    r = client.get("/api/v1/users")
    assert r.status_code in (401, 403)
```

### Step 4: Model/Health API tests

Create `tests/test_api_models.py`:

```python
"""Integration tests for health, system, and model-related endpoints."""

import pytest


def test_health_live(client):
    """Liveness endpoint returns 200 without auth."""
    r = client.get("/api/v1/health/live")
    assert r.status_code == 200
    assert r.json()["status"] == "alive"


def test_health_ready(client):
    """Readiness endpoint returns 200 or 503."""
    r = client.get("/api/v1/health/ready")
    assert r.status_code in (200, 503)
    data = r.json()
    assert "status" in data
    assert "database" in data


def test_health_deep(client):
    """Deep health check returns status and checks."""
    r = client.get("/api/v1/health/deep")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] in ("healthy", "degraded")
    assert "checks" in data
    assert "database" in data["checks"]


def test_root_endpoint(client):
    """Root / returns app status message."""
    r = client.get("/")
    assert r.status_code == 200
    assert "message" in r.json()


def test_security_headers_present(client):
    """All responses include security headers."""
    r = client.get("/api/v1/health/live")
    headers = r.headers
    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert headers.get("x-xss-protection") == "1; mode=block"
    assert headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert "content-security-policy" in headers
    assert "x-request-id" in headers


def test_request_id_in_response(client):
    """Every response includes x-request-id header."""
    r = client.get("/api/v1/health/live")
    assert "x-request-id" in r.headers
    assert len(r.headers["x-request-id"]) > 0


def test_security_headers_on_POST(client, mock_auth):
    """Security headers present on POST responses too."""
    r = client.post(
        "/api/v1/search",
        json={"query": "headers test"},
    )
    assert "x-content-type-options" in r.headers
    assert "x-frame-options" in r.headers
```

### Step 5: Run all backend tests

```bash
cd /home/adi/Desktop/Cortex-Workspace && uv run pytest tests/test_api_agents.py tests/test_api_search.py tests/test_api_conversations.py tests/test_api_models.py -v --tb=short
```

---

## Task 2: Frontend Component Tests

**Files:**
- Create: `frontend/__tests__/MetricRing.test.tsx`
- Create: `frontend/__tests__/Card.test.tsx`
- Create: `frontend/__tests__/TabGroup.test.tsx`

Uses existing vitest config (`frontend/vitest.config.ts`) with jsdom environment, `@testing-library/react`, and `./src/test-setup.ts` (imports `@testing-library/jest-dom`).

### Step 1: MetricRing test

Create `frontend/__tests__/MetricRing.test.tsx`:

```tsx
import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { MetricRing } from "@/shared/ui/MetricRing";

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
});

describe("MetricRing", () => {
  it("renders the label", () => {
    render(<MetricRing label="CPU" value={50} />);
    expect(screen.getByText("CPU")).toBeInTheDocument();
  });

  it("renders the value display", () => {
    render(<MetricRing label="Memory" value={75} />);
    expect(screen.getByText("75")).toBeInTheDocument();
  });

  it("renders the default unit (%)", () => {
    render(<MetricRing label="Disk" value={30} />);
    expect(screen.getByText("%")).toBeInTheDocument();
  });

  it("renders a custom unit", () => {
    render(<MetricRing label="Speed" value={100} unit="ms" />);
    expect(screen.getByText("ms")).toBeInTheDocument();
  });

  it("renders SVG circles", () => {
    const { container } = render(<MetricRing label="Test" value={50} />);
    const circles = container.querySelectorAll("circle");
    expect(circles.length).toBe(2);
  });

  it("applies custom size", () => {
    const { container } = render(
      <MetricRing label="Big" value={50} size={200} />
    );
    const svg = container.querySelector("svg");
    expect(svg).toHaveAttribute("width", "200");
    expect(svg).toHaveAttribute("height", "200");
  });

  it("applies custom className", () => {
    const { container } = render(
      <MetricRing label="Styled" value={50} className="extra-class" />
    );
    expect(container.firstChild).toHaveClass("extra-class");
  });

  it("caps value display at max", () => {
    render(<MetricRing label="Over" value={150} max={100} />);
    expect(screen.getByText("150")).toBeInTheDocument();
  });
});
```

### Step 2: Card test

Create `frontend/__tests__/Card.test.tsx`:

```tsx
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import Card from "@/shared/ui/Card";

describe("Card", () => {
  it("renders children", () => {
    render(<Card>Card content</Card>);
    expect(screen.getByText("Card content")).toBeInTheDocument();
  });

  it("renders without optional props", () => {
    const { container } = render(<Card>Basic</Card>);
    const card = container.firstChild as HTMLElement;
    expect(card).toBeInTheDocument();
    expect(card.tagName).toBe("DIV");
  });

  it("applies hover classes when hover is true", () => {
    const { container } = render(<Card hover>Hoverable</Card>);
    const card = container.firstChild as HTMLElement;
    expect(card.className).toContain("cursor-pointer");
    expect(card.className).toContain("hover:-translate-y-0.5");
  });

  it("does not apply hover classes by default", () => {
    const { container } = render(<Card>Not hoverable</Card>);
    const card = container.firstChild as HTMLElement;
    expect(card.className).not.toContain("cursor-pointer");
  });

  it("applies glass class when glass is true", () => {
    const { container } = render(<Card glass>Glass card</Card>);
    const card = container.firstChild as HTMLElement;
    expect(card.className).toContain("glass-panel");
  });

  it("applies glow class when glow is true", () => {
    const { container } = render(<Card glow>Glow card</Card>);
    const card = container.firstChild as HTMLElement;
    expect(card.className).toContain("shadow-glow");
  });

  it("applies gradient classes when gradient is true", () => {
    const { container } = render(<Card gradient>Gradient</Card>);
    const card = container.firstChild as HTMLElement;
    expect(card.className).toContain("bg-gradient-to-br");
  });

  it("applies custom className", () => {
    const { container } = render(
      <Card className="my-custom-class">Custom</Card>
    );
    const card = container.firstChild as HTMLElement;
    expect(card.className).toContain("my-custom-class");
  });

  it("forwards ref", () => {
    const ref = React.createRef<HTMLDivElement>();
    render(<Card ref={ref}>Ref test</Card>);
    expect(ref.current).toBeInstanceOf(HTMLDivElement);
  });

  it("has base styling classes", () => {
    const { container } = render(<Card>Base styles</Card>);
    const card = container.firstChild as HTMLElement;
    expect(card.className).toContain("rounded-xl");
    expect(card.className).toContain("border");
  });

  it("renders multiple children", () => {
    render(
      <Card>
        <span>First</span>
        <span>Second</span>
      </Card>
    );
    expect(screen.getByText("First")).toBeInTheDocument();
    expect(screen.getByText("Second")).toBeInTheDocument();
  });
});
```

### Step 3: TabGroup test

Create `frontend/__tests__/TabGroup.test.tsx`:

```tsx
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { TabGroup, TabPanel } from "@/shared/ui/TabGroup";

const sampleTabs = [
  { id: "tab1", label: "First Tab" },
  { id: "tab2", label: "Second Tab" },
  { id: "tab3", label: "Third Tab" },
];

describe("TabGroup", () => {
  it("renders all tab labels", () => {
    render(
      <TabGroup tabs={sampleTabs}>
        <div>Content</div>
      </TabGroup>
    );
    expect(screen.getByText("First Tab")).toBeInTheDocument();
    expect(screen.getByText("Second Tab")).toBeInTheDocument();
    expect(screen.getByText("Third Tab")).toBeInTheDocument();
  });

  it("defaults to the first tab", () => {
    render(
      <TabGroup tabs={sampleTabs}>
        <TabPanel tabId="tab1">Panel 1</TabPanel>
        <TabPanel tabId="tab2">Panel 2</TabPanel>
      </TabGroup>
    );
    expect(screen.getByText("Panel 1")).toBeInTheDocument();
    expect(screen.queryByText("Panel 2")).not.toBeInTheDocument();
  });

  it("switches tab on click", () => {
    render(
      <TabGroup tabs={sampleTabs}>
        <TabPanel tabId="tab1">Panel 1</TabPanel>
        <TabPanel tabId="tab2">Panel 2</TabPanel>
      </TabGroup>
    );

    fireEvent.click(screen.getByText("Second Tab"));
    expect(screen.queryByText("Panel 1")).not.toBeInTheDocument();
    expect(screen.getByText("Panel 2")).toBeInTheDocument();
  });

  it("calls onChange callback when tab changes", () => {
    const handleChange = vi.fn();
    render(
      <TabGroup tabs={sampleTabs} onChange={handleChange}>
        <div>Content</div>
      </TabGroup>
    );

    fireEvent.click(screen.getByText("Third Tab"));
    expect(handleChange).toHaveBeenCalledWith("tab3");
  });

  it("respects defaultTab prop", () => {
    render(
      <TabGroup tabs={sampleTabs} defaultTab="tab2">
        <TabPanel tabId="tab1">Panel 1</TabPanel>
        <TabPanel tabId="tab2">Panel 2</TabPanel>
      </TabGroup>
    );
    expect(screen.queryByText("Panel 1")).not.toBeInTheDocument();
    expect(screen.getByText("Panel 2")).toBeInTheDocument();
  });

  it("renders tab with count", () => {
    const tabsWithCount = [
      { id: "a", label: "Items", count: 5 },
      { id: "b", label: "Other" },
    ];
    render(
      <TabGroup tabs={tabsWithCount}>
        <div>Content</div>
      </TabGroup>
    );
    expect(screen.getByText("5")).toBeInTheDocument();
  });

  it("applies custom className", () => {
    const { container } = render(
      <TabGroup tabs={sampleTabs} className="custom-tabs">
        <div>Content</div>
      </TabGroup>
    );
    expect(container.firstChild).toHaveClass("custom-tabs");
  });

  it("renders TabPanel only when its tab is active", () => {
    render(
      <TabGroup tabs={sampleTabs}>
        <TabPanel tabId="tab1">Visible</TabPanel>
        <TabPanel tabId="tab3">Hidden</TabPanel>
      </TabGroup>
    );
    expect(screen.getByText("Visible")).toBeInTheDocument();
    expect(screen.queryByText("Hidden")).not.toBeInTheDocument();

    fireEvent.click(screen.getByText("Third Tab"));
    expect(screen.queryByText("Visible")).not.toBeInTheDocument();
    expect(screen.getByText("Hidden")).toBeInTheDocument();
  });
});
```

### Step 4: Run frontend tests

```bash
cd /home/adi/Desktop/Cortex-Workspace/frontend && npx vitest run __tests__/
```

---

## Task 3: Security Hardening

**Files:**
- Modify: `backend/app/core/middleware.py`
- Modify: `backend/app/core/csrf.py`
- Modify: `frontend/package.json`

### Step 1: Add request body size limit middleware

The existing `middleware.py` already has security headers (`x-content-type-options`, `x-frame-options`, `x-xss-protection`, `referrer-policy`, `content-security-policy`). Add a max request body size middleware to prevent abuse.

Add `RequestSizeLimitMiddleware` to `backend/app/core/middleware.py`:

```python
"""Request logging, security headers, and request size limiting middleware."""

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from backend.app.api.metrics import record_request
from backend.app.core.config import settings
from backend.app.core.logging import RequestIdFilter, get_logger

logger = get_logger(__name__)

# Security headers added to every response.
_CSP_DEV = (
    b"default-src 'self'; "
    b"script-src 'self'; "
    b"style-src 'self' 'unsafe-inline'; "
    b"img-src 'self' data: blob:; "
    b"font-src 'self' data:; "
    b"connect-src 'self' http://localhost:* ws://localhost:*"
)
_CSP_PROD = (
    b"default-src 'self'; "
    b"script-src 'self'; "
    b"style-src 'self' 'unsafe-inline'; "
    b"img-src 'self' data: blob:; "
    b"font-src 'self' data:; "
    b"connect-src 'self'"
)

_is_dev = settings.ENV in ("development", "test")

_SECURITY_HEADERS: list[tuple[bytes, bytes]] = [
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"x-xss-protection", b"1; mode=block"),
    (b"referrer-policy", b"strict-origin-when-cross-origin"),
    (b"content-security-policy", _CSP_DEV if _is_dev else _CSP_PROD),
    (b"permissions-policy", b"camera=(), microphone=(), geolocation=()"),
]

# Maximum request body size: 10 MB
MAX_BODY_BYTES = 10 * 1024 * 1024


class RequestLoggingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid.uuid4())
        RequestIdFilter.set(request_id)
        start = time.perf_counter()
        status_code = 500

        async def send_wrapper(message):
            nonlocal status_code

            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode("ascii")))
                headers.extend(_SECURITY_HEADERS)
                message["headers"] = headers

            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration = round((time.perf_counter() - start) * 1000, 2)
            method = scope.get("method", "UNKNOWN")
            path = scope.get("path", "/")
            record_request(status_code, duration)
            logger.info(
                "request_id=%s method=%s path=%s status=%s duration_ms=%s",
                request_id,
                method,
                path,
                status_code,
                duration,
            )


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests with bodies exceeding MAX_BODY_BYTES."""

    def __init__(self, app: ASGIApp, max_bytes: int = MAX_BODY_BYTES):
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_bytes:
            from starlette.responses import JSONResponse

            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large"},
            )
        return await call_next(request)
```

### Step 2: Update CSRF exemptions

The existing `csrf.py` already exempts `/api/v1/auth/`, `/api/v1/health/`, `/metrics`, `/ws`, `/api/v1/me/vault/`. Verify these are correct and add `/api/auth/` to cover the auth router prefix:

Modify `backend/app/core/csrf.py` — update `EXEMPT_PREFIXES`:

```python
EXEMPT_PREFIXES = ("/api/auth/", "/api/v1/auth/", "/api/v1/health/", "/metrics", "/ws", "/api/v1/me/vault/")
```

### Step 3: Wire new middleware into main.py

Add `RequestSizeLimitMiddleware` to `backend/app/main.py` after the existing middleware:

```python
from backend.app.core.middleware import RequestLoggingMiddleware, RequestSizeLimitMiddleware

# ... existing middleware setup ...

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
```

### Step 4: Remove Three.js from frontend/package.json

Three.js (`three`, `@react-three/fiber`, `@react-three/drei`, `@types/three`) is listed as a dependency but is **never imported** in any frontend source file (confirmed by grep). Remove all four packages:

In `frontend/package.json`, remove from `dependencies`:
- `"@react-three/drei": "^10.7.7"`
- `"@react-three/fiber": "^9.6.1"`
- `"three": "^0.184.0"`

Remove from `devDependencies`:
- `"@types/three": "^0.184.1"`

### Step 5: Install and verify

```bash
cd /home/adi/Desktop/Cortex-Workspace/frontend && npm install
cd /home/adi/Desktop/Cortex-Workspace && uv run ruff check backend/app/core/middleware.py backend/app/core/csrf.py
```

---

## Task 4: Performance Optimization

**Files:**
- Modify: `backend/app/core/db.py`
- Modify: `backend/app/main.py`
- Modify: `frontend/next.config.ts`

### Step 1: Add database connection pooling configuration

The existing `bootstrap.py` already configures `pool_size=5, max_overflow=10, pool_pre_ping=True`. Add configurable pooling settings via `config.py` and expose them:

Add to `backend/app/core/config.py`:

```python
    # Database pool settings
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800  # 30 minutes
```

Update `backend/app/db/bootstrap.py` `_create_engine` to use settings:

```python
def _create_engine():
    global _engine
    if _engine is not None:
        return _engine

    engine = create_engine(
        get_database_url(),
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_pre_ping=True,
    )
    _engine = engine
    return engine
```

### Step 2: Add GZip response compression

Add `GZipMiddleware` to `backend/app/main.py`:

```python
from fastapi.middleware.gzip import GZipMiddleware

# After CORSMiddleware, before RequestLoggingMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### Step 3: Optimize frontend bundle with dynamic imports

Modify `frontend/next.config.ts` to enable bundle splitting and tree shaking:

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  experimental: {
    optimizePackageImports: ["lucide-react", "framer-motion"],
  },
  compiler: {
    removeConsole: process.env.NODE_ENV === "production" ? { exclude: ["error", "warn"] } : false,
  },
};

export default nextConfig;
```

### Step 4: Run verification

```bash
cd /home/adi/Desktop/Cortex-Workspace && uv run ruff check backend/app/core/config.py backend/app/db/bootstrap.py backend/app/main.py
cd /home/adi/Desktop/Cortex-Workspace/frontend && npx tsc --noEmit
```

---

## Task 5: Docker & CI Hardening

**Files:**
- Modify: `Dockerfile`
- Modify: `docker-compose.yml`
- Modify: `.github/workflows/ci.yml`
- Create: `.dockerignore`

### Step 1: Optimize Dockerfile

The existing Dockerfile is already multi-stage with non-root user and healthcheck. Refine with better layer caching, Rust build support for dependencies, and explicit HEALTHCHECK:

```dockerfile
# =============================================================================
# Cortex Workspace — Multi-stage Dockerfile
# =============================================================================
# Build:  docker build -t cortex .
# Run:    docker run -p 8000:8000 --env-file .env cortex
# =============================================================================

# ── Stage 1: Frontend build ──────────────────────────────────────────
FROM node:24-alpine AS frontend-build

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --prefer-offline

COPY frontend/ ./
RUN npm run build

# ── Stage 2: Backend runtime ─────────────────────────────────────────
FROM python:3.12-slim AS backend

# System deps for psycopg2, cryptography, onnxruntime
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:0.11.19 /uv /usr/local/bin/uv

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install Python dependencies
RUN uv sync --frozen --no-dev --no-install-project

# Copy backend source
COPY backend/ ./backend/
COPY alembic.ini ./
COPY migrations/ ./migrations/

# Copy frontend build output
COPY --from=frontend-build /app/frontend/.next/ ./frontend/.next/
COPY --from=frontend-build /app/frontend/public/ ./frontend/public/
COPY frontend/package.json frontend/next.config.ts frontend/tailwind.config.ts frontend/tsconfig.json frontend/postcss.config.mjs ./

# Create non-root user
RUN groupadd -r cortex && useradd -r -g cortex -d /app -s /sbin/nologin cortex \
    && mkdir -p /app/CortexMemory && chown -R cortex:cortex /app

USER cortex

EXPOSE 8000

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=10s \
    CMD curl -f http://localhost:8000/api/v1/health/live || exit 1

CMD ["uv", "run", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 2: Add model volume to docker-compose.yml

Add a persistent volume for LLM models and a network:

```yaml
services:
  db:
    image: postgres:16-alpine
    container_name: cortex-db
    restart: unless-stopped
    environment:
      POSTGRES_USER: cortex
      POSTGRES_PASSWORD: cortex
      POSTGRES_DB: cortex
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U cortex -d cortex"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: cortex-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  qdrant:
    image: qdrant/qdrant:v1.18.0
    container_name: cortex-qdrant
    restart: unless-stopped
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 10s
      timeout: 5s
      retries: 5

  cortex:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: cortex-app
    restart: unless-stopped
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - DATABASE_URL=postgresql://cortex:cortex@db:5432/cortex
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - cortex_memory:/app/CortexMemory
      - cortex_models:/app/models
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      qdrant:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health/live"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s

volumes:
  pgdata:
  qdrant_data:
  cortex_memory:
  cortex_models:
```

### Step 3: Create .dockerignore

Create `.dockerignore` at project root:

```
.git
.github
.agents
node_modules
frontend/node_modules
frontend/.next
__pycache__
*.pyc
*.pyo
.env
.env.*
!.env.example
*.db
*.sqlite
.pytest_cache
.mypy_cache
.ruff_cache
*.egg-info
dist
build
.cortex
```

### Step 4: Update CI pipeline

Update `.github/workflows/ci.yml` with Rust build support and integration test stage:

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend:
    name: Backend (Python)
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: cortex
          POSTGRES_PASSWORD: cortex
          POSTGRES_DB: cortex_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U cortex -d cortex_test"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version-file: ".python-version"

      - name: Install uv
        uses: astral-sh/setup-uv@v3
        with:
          enable-cache: true

      - name: Install Rust toolchain
        uses: dtolnay/rust-toolchain@stable
        with:
          components: rustfmt, clippy

      - name: Cache Rust build artifacts
        uses: actions/cache@v4
        with:
          path: |
            ~/.cargo/registry
            ~/.cargo/git
            target
          key: rust-${{ runner.os }}-${{ hashFiles('**/Cargo.lock') }}
          restore-keys: rust-${{ runner.os }}-

      - name: Install dependencies
        run: uv sync --frozen

      - name: Lint with ruff
        run: uv run ruff check backend/ tests/

      - name: Type check with mypy
        continue-on-error: true
        run: uv run mypy backend/ --ignore-missing-imports --explicit-package-bases --implicit-optional

      - name: Run unit tests
        env:
          DATABASE_URL: postgresql://cortex:cortex@localhost:5432/cortex_test
          REDIS_URL: redis://localhost:6379/0
          SECRET_KEY: ci-test-secret-key-not-for-production
          ENV: test
        run: uv run pytest tests/ -v --tb=short -q

  frontend:
    name: Frontend (TypeScript)
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend

    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "24"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Lint
        continue-on-error: true
        run: npx next lint

      - name: TypeScript type check
        continue-on-error: true
        run: npx tsc --noEmit

      - name: Run tests
        run: npx vitest run

      - name: Build
        run: npm run build
        env:
          NEXT_PUBLIC_API_BASE_URL: http://localhost:8000

  integration:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: [backend, frontend]

    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: cortex
          POSTGRES_PASSWORD: cortex
          POSTGRES_DB: cortex_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U cortex -d cortex_test"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version-file: ".python-version"

      - name: Install uv
        uses: astral-sh/setup-uv@v3
        with:
          enable-cache: true

      - name: Install dependencies
        run: uv sync --frozen

      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://cortex:cortex@localhost:5432/cortex_test
          REDIS_URL: redis://localhost:6379/0
          SECRET_KEY: ci-test-secret-key-not-for-production
          ENV: test
        run: uv run pytest tests/test_api_agents.py tests/test_api_search.py tests/test_api_conversations.py tests/test_api_models.py -v --tb=short

  docker:
    name: Docker Build
    runs-on: ubuntu-latest
    needs: [integration]
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build Docker image
        run: docker build -t cortex:${{ github.sha }} .

      - name: Smoke test Docker image
        run: |
          docker run -d --name cortex-test -p 8000:8000 \
            -e DATABASE_URL=sqlite:///./test.db \
            -e SECRET_KEY=test-key \
            -e ENV=test \
            cortex:${{ github.sha }}
          sleep 5
          curl -f http://localhost:8000/api/v1/health/live || exit 1
          docker stop cortex-test
          docker rm cortex-test
```

### Step 5: Verify

```bash
cd /home/adi/Desktop/Cortex-Workspace && docker build -t cortex-test .
```

---

## Exit Criteria

- [ ] `uv run pytest tests/ -v` — all backend tests pass
- [ ] `cd frontend && npx vitest run` — all frontend tests pass
- [ ] Security headers present: `x-content-type-options`, `x-frame-options`, `referrer-policy`, `permissions-policy`
- [ ] CSRF exemptions cover all auth endpoints (`/api/auth/`, `/api/v1/auth/`)
- [ ] Three.js, @react-three/fiber, @react-three/drei, @types/three removed from package.json
- [ ] GZip compression enabled on API responses
- [ ] Database pool configurable via settings
- [ ] Dockerfile builds cleanly with `docker build`
- [ ] docker-compose includes cortex app service with model volume
- [ ] CI runs unit tests → integration tests → Docker build in sequence
- [ ] `.dockerignore` prevents unnecessary files from entering Docker context
- [ ] All code passes ruff lint and tsc type check
