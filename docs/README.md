# NetRaven Documentation

This directory contains the documentation for the NetRaven project. The documentation is organized in a way that makes it easy to find information about different aspects of the system.

## Documentation Structure

- **architecture/**: Contains architectural documentation describing system components, their interactions, and design decisions.
- **guides/**
  - **developer/**: Developer guides, coding standards, and development workflows.
  - **user/**: End-user documentation for using the application.
- **reference/**: API references, configuration options, and other technical details.

## Documentation Standards

### File Format

All documentation is written in Markdown (.md) format for consistent rendering across different platforms and tools.

### File Naming

- Use lowercase names
- Use hyphens (-) to separate words in filenames
- Use descriptive names that clearly indicate the content
- Examples: `credential-store.md`, `api-authentication.md`

### Document Structure

Each document should follow this general structure:

1. **Title**: Clear, descriptive title at the top (H1)
2. **Overview**: Brief introduction explaining the purpose and scope
3. **Table of Contents**: For documents longer than a few screens
4. **Main Content**: Organized with appropriate headings (H2, H3, H4)
5. **References**: Links to related documents or external resources (if applicable)

### Headings

- Use Title Case for main headings (H1)
- Use Sentence case for all other headings (H2-H6)
- Structure headings hierarchically (H1 > H2 > H3, etc.)

### Code Examples

- Use code blocks with appropriate language specifiers
- Keep examples concise and focused
- Include comments in complex examples

### Diagrams

When diagrams are included:
- Store diagram source files (if applicable) in a `diagrams/` subdirectory
- Prefer SVG format for vector graphics
- Include a text description for accessibility

## Contributing to Documentation

When contributing to the documentation:

1. Follow the existing structure and formatting
2. Update the Table of Contents when adding new sections
3. Verify all links work correctly
4. Run a spelling and grammar check before submitting

## Documentation TODOs

- [ ] Complete API reference documentation
- [ ] Add sequence diagrams for key processes
- [ ] Create troubleshooting guide 