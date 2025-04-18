---
name: 🐛 Bug Report
about: Report a problem to help us improve the project
title: "[BUG] <brief description>"
labels: bug
assignees: ''
---

## 🐞 Bug Description

A clear and concise description of what the bug is.

---

## ✅ Expected Behavior

What did you expect to happen instead?

---

## 🖼️ Screenshots / Logs

If applicable, add screenshots or error logs to help explain the issue.

---

## 💻 Environment tech stack

- All services are running in Docker containers.
- NGINX config is in frontend/nginx.conf.
- Backend is FastAPI, routers are mounted at root (no /api prefix).
- DB is postgresql
- environment contol script is ./setup/manage_netraven.sh

📝 see document /docs/source_of_truth/tech_stack_reference.md

---

## 🤖 AI Assistant Rules:

- Always start by doing a thorough analsysis of the projects codebase and technology stack
- Conduct thorough analysis and research to understand issue and determine root cause.
- Then create an implemenation plan to fix the root cause. If necessary break the work up into indivual work streams.
- Always make sure when you are considering or making coding changes you are following the projects coding princples.
- Update the original Github issue regularly with comments using the github tool.
- Always provide the what and why of what you are doing so that other developers can follow along as you go.

---

## log details:


---