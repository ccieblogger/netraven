name: Enhancement
title: "[Enhancement] <short-title>"
labels: ["type/enhancement"]
body:
  - type: textarea
    id: spec
    attributes:
      label: What & Why
      description: Link to spec section
  - type: textarea
    id: acceptance
    attributes:
      label: Acceptance Criteria
  - type: dropdown
    id: area
    attributes:
      label: Area
      options: ["ui", "api", "devops", "docs"]
