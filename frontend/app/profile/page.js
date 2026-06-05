"use client";

import { useEffect, useMemo, useState } from "react";
import { Badge, Button, Card, Input, Loader } from "../../src/shared/ui";
import { getSessionToken } from "../../src/shared/auth/session";

function splitList(value) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function joinList(value) {
  return Array.isArray(value) ? value.join(", ") : "";
}

function NodeChip({ label, tone = "cyan", title }) {
  return (
    <div className="rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 px-cortex-12 py-cortex-8">
      <div className="font-mono text-[11px] uppercase tracking-[0.12em] text-cortex-text-muted">{title}</div>
      <div className={`mt-cortex-4 font-medium ${tone === "green" ? "text-cortex-green" : "text-cortex-cyan"}`}>
        {label || "n/a"}
      </div>
    </div>
  );
}

export default function ProfilePage() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [jobTitle, setJobTitle] = useState("");
  const [location, setLocation] = useState("");
  const [bio, setBio] = useState("");
  const [interests, setInterests] = useState("");
  const [goals, setGoals] = useState("");
  const [focusAreas, setFocusAreas] = useState("");
  const [languages, setLanguages] = useState("");

  async function loadProfile() {
    try {
      const token = getSessionToken();
      const response = await fetch("/api/profile", {
        cache: "no-store",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.error || data?.detail || "Profile request failed");
      }

      setProfile(data);
      setDisplayName(data.display_name || "");
      setJobTitle(data.job_title || "");
      setLocation(data.location || "");
      setBio(data.bio || "");
      setInterests(joinList(data.interests));
      setGoals(joinList(data.goals));
      setFocusAreas(joinList(data.focus_areas));
      setLanguages(joinList(data.primary_languages));
      setError("");
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Profile request failed");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadProfile();
  }, []);

  const completion = profile?.completion_percent || 0;
  const cortexMemoryMap = useMemo(
    () => [
      { title: "Nickname", label: displayName, tone: "cyan" },
      { title: "Profession", label: jobTitle, tone: "cyan" },
      { title: "Location", label: location, tone: "cyan" },
      { title: "Interests", label: interests, tone: "green" },
      { title: "Goals", label: goals, tone: "green" },
      { title: "Focus", label: focusAreas, tone: "green" },
      { title: "Languages", label: languages, tone: "cyan" },
    ],
    [displayName, jobTitle, location, interests, goals, focusAreas, languages]
  );

  async function saveProfile(event) {
    event.preventDefault();
    setSaving(true);
    setError("");

    try {
      const token = getSessionToken();
      const response = await fetch("/api/profile", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          display_name: displayName.trim() || null,
          job_title: jobTitle.trim() || null,
          location: location.trim() || null,
          bio: bio.trim() || null,
          interests: splitList(interests),
          goals: splitList(goals),
          focus_areas: splitList(focusAreas),
          primary_languages: splitList(languages),
        }),
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.error || data?.detail || "Profile update failed");
      }

      setProfile(data);
      setError("");
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Profile update failed");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="grid gap-cortex-16 xl:grid-cols-[minmax(0,1.4fr)_360px]">
      <div className="grid gap-cortex-16">
        <div className="flex items-start justify-between gap-cortex-16">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-cyan">Profile</p>
            <h1 className="mt-cortex-8 text-2xl font-medium text-cortex-text">Identity and Memory Profile</h1>
            <p className="mt-cortex-8 max-w-2xl text-sm leading-6 text-cortex-text-muted">
              Local profile context used by Cortex for personalisation, memory, and workspace recall.
            </p>
          </div>
          <div className="flex items-center gap-cortex-12">
            <Badge variant={completion >= 80 ? "green" : "warning"}>{completion}% complete</Badge>
            <Button variant="secondary" size="sm" onClick={loadProfile}>
              {loading ? (
                <span className="inline-flex items-center gap-cortex-8">
                  <Loader className="h-3.5 w-3.5" />
                  Syncing
                </span>
              ) : (
                "Refresh"
              )}
            </Button>
          </div>
        </div>

        {error ? (
          <Card className="border-cortex-error/45 bg-cortex-error/10 text-cortex-error">
            <div className="font-mono text-sm">Error: {error}</div>
          </Card>
        ) : null}

        <Card className="grid gap-cortex-12">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-text-muted">Edit profile</p>
            <h2 className="mt-cortex-8 text-lg font-medium text-cortex-text">Profile fields</h2>
          </div>

          <form className="grid gap-cortex-12" onSubmit={saveProfile}>
            <div className="grid gap-cortex-12 md:grid-cols-2">
              <Input value={displayName} onChange={(event) => setDisplayName(event.target.value)} placeholder="Display name" />
              <Input value={jobTitle} onChange={(event) => setJobTitle(event.target.value)} placeholder="Profession" />
            </div>
            <div className="grid gap-cortex-12 md:grid-cols-2">
              <Input value={location} onChange={(event) => setLocation(event.target.value)} placeholder="Location" />
              <Input value={languages} onChange={(event) => setLanguages(event.target.value)} placeholder="Primary languages" />
            </div>
            <textarea
              value={bio}
              onChange={(event) => setBio(event.target.value)}
              rows={5}
              placeholder="Bio"
              className="w-full rounded-cortex border border-cortex-border bg-cortex-bg-secondary px-cortex-16 py-cortex-12 font-mono text-sm text-cortex-text outline-none transition duration-cortex focus:border-cortex-cyan/35 focus:shadow-cortex-cyan"
            />
            <div className="grid gap-cortex-12 md:grid-cols-3">
              <Input value={interests} onChange={(event) => setInterests(event.target.value)} placeholder="Interests, comma-separated" />
              <Input value={goals} onChange={(event) => setGoals(event.target.value)} placeholder="Goals, comma-separated" />
              <Input value={focusAreas} onChange={(event) => setFocusAreas(event.target.value)} placeholder="Focus areas, comma-separated" />
            </div>
            <div className="flex items-center justify-between gap-cortex-12">
              <span className="font-mono text-xs uppercase tracking-[0.12em] text-cortex-text-muted">
                These fields feed Cortex memory and profile context.
              </span>
              <Button type="submit" variant="primary" disabled={saving}>
                {saving ? "Saving..." : "Save profile"}
              </Button>
            </div>
          </form>
        </Card>
      </div>

      <div className="grid gap-cortex-16">
        <Card className="grid gap-cortex-12">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-text-muted">How Cortex remembers you</p>
            <h2 className="mt-cortex-8 text-lg font-medium text-cortex-text">Profile memory graph</h2>
          </div>
          <div className="grid gap-cortex-8">
            {cortexMemoryMap.map((item) => (
              <NodeChip key={item.title} title={item.title} label={item.label} tone={item.tone} />
            ))}
          </div>
        </Card>

        <Card className="grid gap-cortex-12">
          <div className="flex items-center justify-between gap-cortex-12">
            <div>
              <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-text-muted">Onboarding</p>
              <h2 className="mt-cortex-8 text-lg font-medium text-cortex-text">Completion state</h2>
            </div>
            <Badge variant={profile?.onboarding_completed ? "green" : "warning"}>
              {profile?.onboarding_completed ? "complete" : "pending"}
            </Badge>
          </div>
          <div className="grid gap-cortex-8 rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12 font-mono text-sm text-cortex-text-muted">
            <div className="flex items-center justify-between">
              <span>Display name</span>
              <span className="text-cortex-text">{profile?.display_name || "n/a"}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Job title</span>
              <span className="text-cortex-text">{profile?.job_title || "n/a"}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Location</span>
              <span className="text-cortex-text">{profile?.location || "n/a"}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Stored interests</span>
              <span className="text-cortex-text">{profile?.interests?.length || 0}</span>
            </div>
          </div>
        </Card>
      </div>
    </section>
  );
}
