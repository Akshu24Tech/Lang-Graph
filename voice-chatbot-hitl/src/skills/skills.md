# 🎯 Agent Skills Configuration

This file defines reusable skills that enhance user prompts with meta-instructions for better LLM responses.

## What are Skills?

Skills are meta-instructions that transform basic user prompts into professional, well-structured requests. They help the AI:
- Think more systematically
- Provide higher quality responses
- Follow professional writing standards
- Identify important patterns before responding

## How to Use Skills

Skills are automatically applied to user messages before being sent to the LLM. You can:
- **Enable/disable** individual skills by changing `enabled: true/false`
- **Add new skills** by following the format below
- **Customize** the enhancement text for each skill

---

## Available Skills

### 1. Step-by-Step Reasoning
**ID:** `step_by_step_thinking`  
**Enabled:** `true`  
**Purpose:** Encourages logical, structured thinking before providing answers

**Enhancement:**
```
Think step-by-step through the logic before providing the final answer. Break down complex problems into smaller steps.
```

---

### 2. Expert Professional Writing
**ID:** `expert_writing`  
**Enabled:** `true`  
**Purpose:** Ensures high-quality, professional responses without AI cliches

**Enhancement:**
```
Act as a senior expert writing for a professional audience. No fluff, no AI-style cliches like "dive into", "delve", "it's worth noting", or "in the world of". Be direct, clear, and authoritative.
```

---

### 3. Pattern Recognition
**ID:** `pattern_recognition`  
**Enabled:** `true`  
**Purpose:** Identifies key patterns before starting work

**Enhancement:**
```
Identify the 3 most important patterns, themes, or requirements in this request before starting your response. Use these to structure your answer effectively.
```

---

### 4. Concise Communication
**ID:** `concise_communication`  
**Enabled:** `true`  
**Purpose:** Promotes clear, efficient communication

**Enhancement:**
```
Be concise and to the point. Avoid unnecessary elaboration while maintaining completeness. Prioritize clarity over verbosity.
```

---

### 5. Context Awareness
**ID:** `context_awareness`  
**Enabled:** `true`  
**Purpose:** Ensures responses consider conversation history and user context

**Enhancement:**
```
Consider the full conversation context and any stored user information when crafting your response. Ensure consistency with previous interactions.
```

---

### 6. Critical Thinking (Optional)
**ID:** `critical_thinking`  
**Enabled:** `false`  
**Purpose:** Encourages questioning assumptions and exploring alternatives

**Enhancement:**
```
Challenge assumptions in the request. Consider alternative perspectives and potential edge cases before providing your answer.
```

---

### 7. Examples and Evidence (Optional)
**ID:** `examples_evidence`  
**Enabled:** `false`  
**Purpose:** Encourages providing concrete examples and evidence

**Enhancement:**
```
Support your response with specific examples, evidence, or code snippets where appropriate. Make abstract concepts concrete.
```

---

## Skill Application

Skills are applied in the following order:
1. **Pattern Recognition** - Understand the request structure
2. **Context Awareness** - Consider conversation history
3. **Step-by-Step Reasoning** - Plan the approach
4. **Expert Writing** - Set the tone and style
5. **Concise Communication** - Ensure clarity
6. **Critical Thinking** - Question assumptions (if enabled)
7. **Examples/Evidence** - Add concrete support (if enabled)

---

## Adding Custom Skills

To add a new skill, follow this format:

```markdown
### [Skill Number]. [Skill Name]
**ID:** `unique_skill_id`  
**Enabled:** `true/false`  
**Purpose:** Brief description of what this skill does

**Enhancement:**
```
The actual instruction text that will be added to the user's prompt.
```
```

---

## Notes

- **Performance:** Having too many skills enabled may make prompts too long. Start with 3-5 core skills.
- **Customization:** Modify the enhancement text to match your preferred AI behavior.
- **Priority:** Skills listed first have higher priority and are applied first.
- **Conflicts:** If skills contradict each other, consider disabling one.

---

**Last Updated:** 2026-01-15  
**Version:** 1.0
