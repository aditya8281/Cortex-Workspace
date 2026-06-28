"use client";

import { useState } from "react";
import { Modal } from "@/shared/ui/Modal";
import { Input } from "@/shared/ui/Input";
import { Button } from "@/shared/ui/Button";
import { repository, type RepoEntry } from "../api";

interface AddRepoModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess: (repo: RepoEntry) => void;
}

export function AddRepoModal({ open, onClose, onSuccess }: AddRepoModalProps) {
  const [name, setName] = useState("");
  const [path, setPath] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!name.trim() || !path.trim()) {
      setError("Name and path are required");
      return;
    }
    setLoading(true);
    try {
      const repo = await repository.create({
        name: name.trim(),
        path: path.trim(),
      });
      onSuccess(repo);
      setName("");
      setPath("");
      onClose();
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to add repository",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Add Repository">
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Name"
          id="add-repo-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="my-project"
        />
        <Input
          label="Path"
          id="add-repo-path"
          value={path}
          onChange={(e) => setPath(e.target.value)}
          placeholder="/home/user/projects/my-project"
        />
        {error && <p className="text-xs text-danger">{error}</p>}
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="ghost" type="button" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={loading}>
            Add Repository
          </Button>
        </div>
      </form>
    </Modal>
  );
}
