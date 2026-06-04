---
name: project-context-system
description: Implementation plan for the universal Context System in Cortex
metadata:
  type: project
---

# Universal Context System Implementation

## Overview
This document outlines the implementation plan for the universal Context System in Cortex, which will allow users to explicitly provide files, folders, repositories, memory entries, URLs, and terminal output as context for conversations.

## Components to Implement

### 1. Frontend: ChatComposer Component
- Add "+" button for context attachment
- Create context attachment dropdown with options for all context types
- Display context chips above the input area
- Allow removal of context items

### 2. Frontend: Context Store
- Manage attached context items per session
- Provide APIs for attaching, removing, listing, and resolving context
- Integrate with zustand for state management

### 3. Backend: Context Manager
- Create centralized ContextManager service
- Implement context item storage and retrieval
- Handle different context types (file, folder, repo, memory, URL, terminal)

### 4. Backend: API Endpoints
- Attach Context endpoint
- Remove Context endpoint
- List Context endpoint
- Resolve Context endpoint

### 5. Backend: Integration with AI Flow
- Modify QueryRequest model to include context items
- Update context compiler to handle attached context
- Implement context prioritization (Attached > Workspace > Conversation > Memory > Retrieval)