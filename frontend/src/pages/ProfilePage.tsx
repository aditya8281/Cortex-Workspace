import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { User, Sparkles, Target, Code2, CheckCircle2 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { useProfileStore } from "@/stores/profileStore";
import { useAppStore } from "@/stores/appStore";
import { getMyProfile, updateMyProfile } from "@/api/profile";
import { getMe } from "@/api/auth";

const STEPS = [
  { title: "Identity", icon: User, fields: ["displayName", "jobTitle", "location"] },
  { title: "About you", icon: Sparkles, fields: ["bio"] },
  { title: "Interests", icon: Target, fields: ["interests"] },
  { title: "Goals & focus", icon: CheckCircle2, fields: ["goals", "focusAreas"] },
  { title: "Tech stack", icon: Code2, fields: ["primaryLanguages"] },
];

const FOCUS_PRESETS = ["AI/ML", "Backend", "Frontend", "DevOps", "Research", "Product", "Security"];

export function ProfilePage() {
  const navigate = useNavigate();
  const token = useAppStore((s) => s.token);
  const setToast = useAppStore((s) => s.setToast);
  const setCurrentUser = useAppStore((s) => s.setCurrentUser);
  const profile = useProfileStore((s) => s.profile);
  const setProfile = useProfileStore((s) => s.setProfile);
  const addInterest = useProfileStore((s) => s.addInterest);
  const addGoal = useProfileStore((s) => s.addGoal);
  const removeInterest = useProfileStore((s) => s.removeInterest);
  const removeGoal = useProfileStore((s) => s.removeGoal);
  const completion = useProfileStore((s) => s.completionPercent);

  const [step, setStep] = useState(profile.onboardingStep);
  const [interestInput, setInterestInput] = useState("");
  const [goalInput, setGoalInput] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!token) return;
    void (async () => {
      try {
        const [me, remote] = await Promise.all([getMe(), getMyProfile()]);
        setCurrentUser(me);
        setProfile({
          displayName: remote.display_name ?? me.full_name,
          email: remote.email ?? me.email,
          jobTitle: remote.job_title ?? "",
          location: remote.location ?? "",
          bio: remote.bio ?? "",
          interests: remote.interests,
          goals: remote.goals,
          focusAreas: remote.focus_areas,
          primaryLanguages: remote.primary_languages,
          onboardingComplete: remote.onboarding_completed,
          onboardingStep: remote.onboarding_completed ? STEPS.length : step,
        });
      } catch {
        /* profile API optional until migrated */
      }
    })();
  }, [token, setCurrentUser, setProfile, step]);

  const persist = async (patch: Parameters<typeof setProfile>[0], complete = false) => {
    setProfile(patch);
    if (!token) return;
    setSaving(true);
    try {
      await updateMyProfile({
        display_name: patch.displayName ?? profile.displayName,
        job_title: patch.jobTitle ?? profile.jobTitle,
        location: patch.location ?? profile.location,
        bio: patch.bio ?? profile.bio,
        interests: patch.interests ?? profile.interests,
        goals: patch.goals ?? profile.goals,
        focus_areas: patch.focusAreas ?? profile.focusAreas,
        primary_languages: patch.primaryLanguages ?? profile.primaryLanguages,
        onboarding_completed: complete || profile.onboardingComplete,
      });
      setToast("Profile saved");
    } catch {
      setToast("Saved locally (sign in to sync to server)");
    } finally {
      setSaving(false);
    }
  };

  const toggleFocus = (area: string) => {
    const next = profile.focusAreas.includes(area)
      ? profile.focusAreas.filter((a) => a !== area)
      : [...profile.focusAreas, area];
    void persist({ focusAreas: next });
  };

  const nextStep = () => {
    const next = Math.min(step + 1, STEPS.length - 1);
    setStep(next);
    setProfile({ onboardingStep: next });
    void persist({ onboardingStep: next });
  };

  const finishOnboarding = () => {
    setProfile({ onboardingComplete: true, onboardingStep: STEPS.length });
    void persist({ onboardingComplete: true }, true);
    navigate("/");
  };

  const StepIcon = STEPS[step]?.icon ?? User;

  return (
    <div className="h-full overflow-y-auto p-6 md:p-8">
      <div className="mx-auto max-w-2xl space-y-6">
        <div className="flex items-start gap-4">
          <div
            className="flex h-16 w-16 items-center justify-center rounded-2xl text-2xl font-bold text-white"
            style={{ background: profile.avatarColor }}
          >
            {(profile.displayName || "?").charAt(0).toUpperCase()}
          </div>
          <div className="flex-1">
            <h2 className="text-xl font-semibold">Your Cortex profile</h2>
            <p className="text-sm text-cortex-muted">
              Build your identity so Cortex can personalize assistance, memory, and proactive insights.
            </p>
            <div className="mt-3">
              <Progress value={completion()} label="Profile completeness" />
            </div>
          </div>
        </div>

        {!profile.onboardingComplete && (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <StepIcon className="h-5 w-5 text-cortex-accent" />
                <div>
                  <CardTitle className="text-base">
                    Step {step + 1} of {STEPS.length}: {STEPS[step].title}
                  </CardTitle>
                  <CardDescription>Profile builder</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {step === 0 && (
                <>
                  <Input
                    placeholder="Display name"
                    value={profile.displayName}
                    onChange={(e) => setProfile({ displayName: e.target.value })}
                    onBlur={() => void persist({ displayName: profile.displayName })}
                  />
                  <Input
                    placeholder="Job title (e.g. AI Engineer)"
                    value={profile.jobTitle}
                    onChange={(e) => setProfile({ jobTitle: e.target.value })}
                    onBlur={() => void persist({ jobTitle: profile.jobTitle })}
                  />
                  <Input
                    placeholder="Location"
                    value={profile.location}
                    onChange={(e) => setProfile({ location: e.target.value })}
                    onBlur={() => void persist({ location: profile.location })}
                  />
                </>
              )}
              {step === 1 && (
                <textarea
                  className="min-h-[120px] w-full rounded-lg border border-cortex-border bg-cortex-elevated p-3 text-sm"
                  placeholder="Tell Cortex about your work, interests, and how you use your machine…"
                  value={profile.bio}
                  onChange={(e) => setProfile({ bio: e.target.value })}
                  onBlur={() => void persist({ bio: profile.bio })}
                />
              )}
              {step === 2 && (
                <>
                  <div className="flex gap-2">
                    <Input
                      placeholder="Add interest"
                      value={interestInput}
                      onChange={(e) => setInterestInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          addInterest(interestInput);
                          setInterestInput("");
                          void persist({ interests: [...profile.interests, interestInput.trim()] });
                        }
                      }}
                    />
                    <Button
                      variant="secondary"
                      onClick={() => {
                        addInterest(interestInput);
                        setInterestInput("");
                        void persist({ interests: profile.interests });
                      }}
                    >
                      Add
                    </Button>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {profile.interests.map((i) => (
                      <Badge key={i} className="cursor-pointer" onClick={() => { removeInterest(i); void persist({}); }}>
                        {i} ×
                      </Badge>
                    ))}
                  </div>
                </>
              )}
              {step === 3 && (
                <>
                  <div className="flex flex-wrap gap-2">
                    {FOCUS_PRESETS.map((f) => (
                      <button
                        key={f}
                        type="button"
                        className={`rounded-lg border px-3 py-1 text-xs ${profile.focusAreas.includes(f) ? "border-cortex-accent bg-cortex-accent-soft text-cortex-accent" : "border-cortex-border"}`}
                        onClick={() => toggleFocus(f)}
                      >
                        {f}
                      </button>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <Input
                      placeholder="Add a goal"
                      value={goalInput}
                      onChange={(e) => setGoalInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && goalInput.trim()) {
                          addGoal(goalInput);
                          setGoalInput("");
                          void persist({ goals: profile.goals });
                        }
                      }}
                    />
                    <Button variant="secondary" onClick={() => { addGoal(goalInput); setGoalInput(""); }}>
                      Add
                    </Button>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {profile.goals.map((g) => (
                      <Badge key={g} onClick={() => removeGoal(g)}>
                        {g}
                      </Badge>
                    ))}
                  </div>
                </>
              )}
              {step === 4 && (
                <Input
                  placeholder="Languages & tools (comma-separated)"
                  value={profile.primaryLanguages.join(", ")}
                  onChange={(e) =>
                    setProfile({
                      primaryLanguages: e.target.value.split(",").map((s) => s.trim()).filter(Boolean),
                    })
                  }
                  onBlur={() => void persist({ primaryLanguages: profile.primaryLanguages })}
                />
              )}
              <div className="flex justify-between pt-2">
                <Button variant="ghost" disabled={step === 0} onClick={() => setStep(step - 1)}>
                  Back
                </Button>
                {step < STEPS.length - 1 ? (
                  <Button onClick={nextStep}>Continue</Button>
                ) : (
                  <Button onClick={finishOnboarding} disabled={saving}>
                    Complete profile
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Profile summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <p>
              <span className="text-cortex-muted">Name:</span> {profile.displayName || "—"}
            </p>
            <p>
              <span className="text-cortex-muted">Role:</span> {profile.jobTitle || "—"}
            </p>
            <p>
              <span className="text-cortex-muted">Bio:</span> {profile.bio || "—"}
            </p>
            <div className="flex flex-wrap gap-1">
              {profile.interests.map((i) => (
                <Badge key={i}>{i}</Badge>
              ))}
            </div>
            {!profile.onboardingComplete && (
              <Button variant="secondary" onClick={() => setProfile({ onboardingComplete: false, onboardingStep: 0 })}>
                Restart profile builder
              </Button>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
