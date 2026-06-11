# MCP and Tool Plan

## Principle

Tools are the body of the OS. Add them only after the local brain and control plane are stable.

## Connector Order

### 1. GitHub

Allowed first:
- read issues;
- draft issues;
- create issues after approval;
- read PRs;
- draft PR summaries.

Denied first:
- merge PRs;
- delete repos/branches;
- change secrets;
- push without review.

### 2. Calendar / Tasks

Allowed first:
- read availability;
- draft time blocks;
- suggest schedule changes.

Denied first:
- invite external people;
- delete events;
- book paid services.

### 3. Obsidian / Files

Allowed first:
- read selected folders;
- create summaries;
- index projects, goals, decisions.

Denied first:
- ingest private journals/health notes without explicit opt-in;
- rewrite personal memory in bulk.

### 4. Email / Telegram

Allowed first:
- triage inbox;
- draft replies;
- prepare outbound messages.

Denied first:
- send messages without approval;
- scrape personal chats broadly;
- use private data in public drafts.

## Approval Log

Every external action should log:

- requested action;
- agent;
- risk;
- approval owner;
- timestamp;
- result;
- rollback or follow-up.
