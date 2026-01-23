---
name: 📚 Documentation
about: Suggest improvements or report issues with documentation
title: '[DOCS] '
labels: ['documentation']
assignees: []
---

## 🌿 Branch Creation Instructions

**When you're ready to work on this documentation:**

1. **Sync with latest code:**
   ```bash
   git checkout main
   git pull origin main
   ```

2. **Create documentation branch:**
   ```bash
   # Use format: docs/issue-number-descriptive-name
   git checkout -b docs/123-update-documentation-topic
   
   # Examples:
   git checkout -b docs/456-add-getting-started-guide
   git checkout -b docs/789-update-api-reference
   git checkout -b docs/101-improve-cli-help-text
   ```

3. **Push branch to your fork:**
   ```bash
   git push -u origin docs/123-update-documentation-topic
   ```

**Branch Naming Rules:**
- Must start with `docs/`
- Include issue number: `docs/123-descriptive-name`
- Use lowercase with hyphens (kebab-case)
- Be descriptive of documentation changes
- Follow pattern: `docs/issue-number-what-docs-are-updated`

---

## 📚 Documentation Request

**Type of Documentation:**
- [ ] New documentation needed
- [ ] Existing documentation needs updates
- [ ] Documentation error/correction
- [ ] Documentation reorganization
- [ ] Translation/localization

**Related Branch Type:** `docs/`

## 🎯 What Needs Documentation?

**Topic/Subject:**
Clear description of what needs to be documented.

**Target Audience:**
- [ ] New users
- [ ] Experienced users
- [ ] Developers/contributors
- [ ] Administrators
- [ ] API consumers

**Documentation Category:**
- [ ] Getting started guide
- [ ] CLI reference
- [ ] Configuration guide
- [ ] API documentation
- [ ] Troubleshooting
- [ ] Best practices
- [ ] Examples/tutorials
- [ ] Contributing guide
- [ ] Architecture/design

## 📍 Current State

**Existing Documentation:**
- Location: ___________
- Current content: ___________
- What's missing/wrong: ___________

**Gap Analysis:**
Describe the gap between current and needed documentation.

## 📋 Specific Requirements

**Content Needed:**
- [ ] Step-by-step instructions
- [ ] Code examples
- [ ] Command reference
- [ ] Configuration samples
- [ ] Screenshots/diagrams
- [ ] Troubleshooting tips
- [ ] FAQ entries
- [ ] Video/interactive content

**Key Information to Include:**
- Prerequisites
- Installation steps
- Configuration options
- Usage examples
- Common issues
- Advanced features

## 📂 Affected Documentation Files

**Files to Update/Create:**
- [ ] `README.md`
- [ ] `docs/CONTRIBUTING.md`
- [ ] `docs/CHANGELOG.md`
- [ ] CLI help text (`cli.py`)
- [ ] Function docstrings
- [ ] API documentation
- [ ] Configuration examples
- [ ] Other: ___________

**Documentation Structure:**
```
# Proposed structure or outline
1. Section 1
   - Subsection A
   - Subsection B
2. Section 2
   - Subsection C
```

## 💡 Content Suggestions

**Proposed Content:**
Describe or draft the content you'd like to see.

**Examples/Use Cases:**
```bash
# Example commands or code snippets
classdock example --help
```

**Visual Elements:**
- [ ] Diagrams needed
- [ ] Screenshots needed
- [ ] Flowcharts needed
- [ ] Code syntax highlighting
- [ ] Tables/matrices

## 🔗 Related Information

**Related Issues:**
- Related to #(issue number)
- Blocks #(issue number)
- Follows #(issue number)

**External References:**
- GitHub Classroom docs
- GitHub API docs
- Python/Poetry docs
- Related projects

**User Feedback:**
Any user feedback or questions that prompted this documentation need?

## 🎨 Style and Format

**Documentation Standards:**
- [ ] Follow existing style guide
- [ ] Use consistent terminology
- [ ] Include code examples
- [ ] Add cross-references
- [ ] Ensure accessibility

**Format Requirements:**
- [ ] Markdown format
- [ ] CLI help text
- [ ] Docstring format
- [ ] MkDocs pages
- [ ] Other: ___________

**Tone and Voice:**
- [ ] Beginner-friendly
- [ ] Technical/precise
- [ ] Step-by-step
- [ ] Reference style
- [ ] Tutorial style

## ✅ Acceptance Criteria

**Completion Checklist:**
- [ ] Content is accurate and up-to-date
- [ ] Examples work correctly
- [ ] Links are valid
- [ ] Grammar and spelling checked
- [ ] Consistent with existing docs
- [ ] Addresses user needs
- [ ] Includes troubleshooting
- [ ] Easy to navigate

**Quality Standards:**
- [ ] Clear and concise
- [ ] Comprehensive coverage
- [ ] Practical examples
- [ ] Error scenarios covered
- [ ] Regular maintenance plan

## 🧪 Testing/Validation

**Content Validation:**
- [ ] Technical accuracy verified
- [ ] Commands tested
- [ ] Examples work
- [ ] Links functional
- [ ] Cross-platform compatibility

**User Testing:**
- [ ] New user perspective
- [ ] Experienced user review
- [ ] Developer feedback
- [ ] Accessibility check

## 📅 Implementation Plan

**Priority Level:**
- [ ] High - Blocking users
- [ ] Medium - Important improvement
- [ ] Low - Nice to have

**Timeline:**
- Research: ___________
- Draft: ___________
- Review: ___________
- Publication: ___________

**Dependencies:**
- [ ] Code changes needed first
- [ ] Feature completion required
- [ ] Other documentation updates
- [ ] Tool/system setup

---

## 📝 Developer Checklist

**Branch Naming:**
- [ ] Use `docs/descriptive-name` branch naming convention
- [ ] Follow branch-name-check.yml requirements

**Documentation Standards:**
- [ ] Follow project style guide
- [ ] Use consistent terminology
- [ ] Include practical examples
- [ ] Test all code snippets
- [ ] Verify links work
- [ ] Check grammar and spelling

**File Organization:**
- [ ] Logical file structure
- [ ] Consistent naming
- [ ] Proper cross-referencing
- [ ] Update navigation/index

**Content Quality:**
- [ ] Accurate and current
- [ ] Clear and concise
- [ ] Appropriate detail level
- [ ] Inclusive language
- [ ] Accessible format

**Integration:**
- [ ] Update CLI help text
- [ ] Sync with code comments
- [ ] Update CHANGELOG.md
- [ ] Link from relevant places

---

*Thank you for helping improve ClassDock's documentation! Good docs make the tool accessible to everyone.*