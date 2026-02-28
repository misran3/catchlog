## The Challenge
Build something that combines:
1. A fine-tuned on-device model adapted to your task
2. Agentic behavior - your system decides and acts autonomously
3. Visual input - camera, video, or screen feeding into the system
4. A genuine reason this runs on-device
5. Optional bonus: voice input and/or output.

**IMPORTANT: 1, 2, 3, and 4 are MANDATORY.**
If you deviate from this challenge, think twice before you do.

## Workflow Orchestration

### 1. Brainstorming by default
- Use superpowers:brainstorming and superpowers:writing-plans skill for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately - don't keep pushing
- Use superpowers for verification steps, not just building
- Write detailed design and implementation plans upfront to reduce ambiguity

### 2. Subagent Strategy
- Use subagents liberally to keep main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution

### 3. Self-Improvement Loop
- After ANY correction from the user: update `docs/lessons.md` with the pattern Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review `docs/lessons.md` at session start to refresh memory

### 4. Verification Before Done
- Never mark a task complete without proving it works
- Diff behavior between main and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness

### 5. Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes - don't over-engineer
- Challenge your own work before presenting it

### 6. Autonomous Bug Fixing
- When given a bug, use superpowers:systematic-debugging skill to find root cause
- Point at logs, errors, failing tests - then resolve them

## Task Management
1. **Plan First**: Write plan to `docs/plans` with checkable items
2. **Verify Plan**: Check in before starting implementation
3. **Track Progress**: Mark items complete as you go
4. **Explain Changes**: High-level summary at each step
5. **Document Results**: Add development timeline and review section to `docs/devlog.md`
6. **Capture Lessons**: Update `docs/lessons.md` after corrections

## Core Principles
- **Simplicity First**: Make every change as simple as possible. Impact minimal code.
- **No Laziness**: Find root causes. No temporary fixes. Senior developer standards.
- **Minimat Impact**: Changes should only touch what's necessary. Avoid introducing bugs.

## Resources
- Gemma models & docs: ai.google.dev/gemma
- All models on Hugging Face: huggingface.co/google
- Gemma Cookbook: github.com/google-gemini/gemma-cookbook
- Google AI Edge / LiteRT-LM: github.com/google-ai-edge/LiteRT-LM
- Fine-tuning guide: ai.google.dev/gemma/docs/tune
- FunctionGemma: huggingface.co/google/functiongemma-270m-it
- Gemma 3n developer guide: developers.googleblog.com/en/introducing-gemma-3n-developer-guide
- Google AI Studio: aistudio.google.com
