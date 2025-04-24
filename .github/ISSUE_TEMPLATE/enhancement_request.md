---
name: ✨ Enhancement Request
about: Suggest an improvement or optimization to an existing feature
title: "[ENHANCEMENT] <brief summary>"
labels: enhancement
assignees: ''
---

## ✨ Summary

Clearly describe the enhancement you're proposing. What part of the system is affected?

---

## 🔍 Current Behavior

Briefly explain the current behavior and any limitations or inefficiencies.

---

## 💡 Proposed Improvement

Describe your suggested change and how it would work.

---

## 💻 Environment tech stack

- All services are running in Docker containers.
- NGINX config is in frontend/nginx.conf.
- Backend is FastAPI, routers are mounted at root (no /api prefix).
- DB is postgresql
- environment contol script is ./setup/manage_netraven.sh
- pytests are run via container. ex. docker exec -it netraven-api-dev bash -c "cd /app && PYTHONPATH=/app poetry run pytest tests/api/"

📝 see document /docs/source_of_truth/tech_stack_reference.md

---


## 📎 Additional Context

Include any screenshots, related issues, or external resources to help illustrate the enhancement.

## 🤖 AI Assistant Rules:

- Always start by doing a thorough analysis of the project's codebase and technology stack
- Conduct thorough analysis and research to understand the best method to introduce the enhancement or the issues root cause that aligns with the projects coding principles.
- Depending on the effort, consider breaking the work up into individual work streams if appropriate.
- Always make sure when you are considering or making coding changes you are following the projects coding principles.
- Update the original GitHub enhancement or issue regularly with comments using the GitHub tool.
- Always provide what and why of what you are doing so that other developers can follow along as you go.

---