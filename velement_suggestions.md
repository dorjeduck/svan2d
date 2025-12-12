# VElement Interface Improvement Suggestions

This document outlines suggestions to make the VElement interface more intuitive while preserving its full power and flexibility.

---

## 1. Naming Clarity: `transition_config` → `transition_to_next`

**Problem:** `transition_config` on a KeyState controls the segment *from* that keystate to the next one, not *to* it. This is counterintuitive.

**Current:**
```python
KeyState(state=s1, transition_config=TransitionConfig(easing={"pos": in_out}))
```

**Suggestion:** Rename to `transition_to_next` or `outgoing_transition`:
```python
KeyState(state=s1, transition_to_next=TransitionConfig(easing={"pos": in_out}))
```

**Visual clarification for docs:**
```
KeyState(s1, transition_to_next=...)  →  KeyState(s2)
         ↑ controls this segment ↑
```

---

## 2. Time Distribution: Add Explicit Control

**Problem:** The 3-tier time anchoring logic is complex and surprising:

| Input | Result |
|-------|--------|
| `[s1, s2, s3]` | `[(0, s1), (0.5, s2), (1, s3)]` |
| `[s1, (0.5, s2)]` | `[(0, s1), (0.5, s2)]` — stops at 0.5! |
| `[(0.2, s1), s2, (0.8, s3)]` | s2 placed at 0.5, not evenly in gap |

**Suggestions:**

### Option A: Add `full_range` parameter
```python
VElement(keystates=[s1, (0.5, s2)], full_range=True)
# Forces normalization to [(0, s1), (0.5, s2), (1.0, s2)]
```

### Option B: Factory methods with clear semantics
```python
# Always distributes 0.0-1.0
VElement.from_states([s1, s2, s3])

# Explicit times only, no auto-distribution
VElement.from_timed_states([(0.0, s1), (0.5, s2), (1.0, s3)])

# Current flexible behavior (for power users)
VElement(keystates=[...])
```

---

## 3. Simplify Easing with Intention-Revealing Methods

**Problem:** The 4-level easing priority system requires users to understand the full precedence stack:
1. Attribute keystate easing (highest)
2. VElement `attribute_easing`
3. Segment `transition_config.easing`
4. State `DEFAULT_EASING` (lowest)

**Suggestion:** Provide convenience methods for common cases:

```python
# Apply single easing to all attributes
VElement.with_easing(keystates, easing.in_out)

# Apply easing to position only (most common case)
VElement.with_pos_easing(keystates, easing.bounce)

# Apply different easings per attribute
VElement.with_attribute_easing(keystates, {
    "pos": easing.in_out,
    "opacity": easing.linear
})
```

These hide the priority system for simple cases while keeping the full API available.

---

## 4. Explicit `attribute_keystates` Range Behavior

**Problem:** Attribute keystates silently extend to 0.0-1.0, even if the element's keystates span a different range (e.g., 0.2-0.8).

```python
# Element exists 0.2-0.8
VElement(
    keystates=[(0.2, s1), (0.8, s2)],
    attribute_keystates={"opacity": [(0.5, 0.5)]}
    # Opacity extends to [(0.0, 0.5), ..., (1.0, 0.5)] — beyond element range!
)
```

**Suggestions:**

### Option A: Add alignment parameter
```python
VElement(
    keystates=[...],
    attribute_keystates={...},
    align_attribute_keystates=True  # Clip to element's keystate range
)
```

### Option B: Emit warning on mismatch
```
Warning: attribute_keystates range [0.0-1.0] extends beyond element keystates range [0.2-0.8]
```

---

## 5. Path Function Scope Clarity

**Problem:** Path functions only affect the `pos` field, but users might expect them to work on other Point2D fields. The limitation is silent.

**Suggestions:**

### Option A: Rename for clarity
```python
# Current
TransitionConfig(path=bezier([...]))

# Suggested
TransitionConfig(pos_path=bezier([...]))
```

### Option B: Support multiple fields
```python
TransitionConfig(
    field_paths={
        "pos": path.bezier([Point2D(0, 200)]),
        "anchor": path.arc_clockwise(100)
    }
)
```

### Option C: Warning when path has no effect
```
Warning: path function specified but no 'pos' field transition in this segment
```

---

## 6. Validation Mode with Helpful Errors

**Suggestion:** Add validation that catches common mistakes early:

```python
# Enable strict validation
VElement(keystates=[...], validate=True)

# Or explicit validation call
element = VElement(keystates=[...])
element.validate()  # Raises descriptive errors
```

**Validations to include:**
- Keystates with duplicate times
- Attribute keystates referencing non-existent fields on the state
- Morphing between incompatible state types
- Time values outside 0.0-1.0 range
- Empty keystates list
- Conflicting easing specifications

**Error message examples:**
```
ValidationError: Duplicate keystate time 0.5 found at indices 1 and 3
ValidationError: attribute_keystates references 'fill_color' but CircleState has no such field
ValidationError: Cannot morph between CircleState and TextState (incompatible types)
```

---

## 7. Builder Pattern for Complex Animations

**Suggestion:** Offer a fluent builder API as an **additional entry point** (not a replacement) for complex setups.

**Design decision:** The current constructor API (`VElement(keystates=[s1, s2])`) remains the best choice for simple cases. The builder is an alternative for users who need complex configurations where the nested KeyState/TransitionConfig approach becomes hard to read.

```python
element = (
    VElement.builder()
    .renderer(CircleRenderer())
    .keystate(state1, at=0.0)
    .keystate(state2, at=0.5, easing={"pos": easing.in_out})
    .keystate(state3, at=1.0)
    .pos_easing(easing.bounce)  # Instance-level override
    .attribute_timeline("opacity", [1.0, 0.5, 1.0])
    .clip_to(mask_element)
    .build()
)
```

**Benefits:**
- Construction order mirrors logical flow
- IDE autocompletion guides users
- Invalid combinations caught at build time
- Self-documenting code

---

## 8. Visual Debug / Timeline Inspection

**Suggestion:** Add a method to visualize the animation timeline:

```python
element.debug_timeline()
```

**Output:**
```
VElement Timeline
═══════════════════════════════════════════════════════════
  Time:     0.0 ─────────── 0.5 ─────────── 1.0
  States:   CircleState ──► CircleState ──► CircleState

Segment Transitions:
  [0.0 → 0.5] easing: in_out (from transition_config)
  [0.5 → 1.0] easing: linear (from DEFAULT_EASING)

Attribute Timelines:
  pos:      follows main keystates, easing: bounce (instance override)
  opacity:  [0.0: 1.0] ────► [0.5: 0.5] ────► [1.0: 1.0]

Easing Priority Applied:
  pos: instance attribute_easing (bounce) > segment > default
═══════════════════════════════════════════════════════════
```

**Also useful:** `element.get_effective_easing("pos", segment=0)` to query resolved easing.

---

## 9. Discourage Mixed Input Formats

**Problem:** Mixing bare states, tuples, and KeyState objects in one list leads to unexpected time distribution:

```python
# What does this produce?
VElement(keystates=[state1, (0.5, state2), KeyState(state=state3)])
```

**Suggestion:** Emit a warning when mixing formats:

```python
# Runtime warning:
"Mixed keystate input formats detected (bare State, tuple, KeyState).
 Consider using a consistent format for predictable timing.
 See docs: https://svan2d.org/keystates"
```

**Or:** Add a `strict_input=True` parameter that raises an error on mixed formats.

---

## 10. Documentation: Decision Tree

Add a "Which approach should I use?" guide to documentation:

```
┌─────────────────────────────────────────────────────────────┐
│           CHOOSING YOUR VELEMENT CONFIGURATION              │
└─────────────────────────────────────────────────────────────┘

START: What kind of animation do you need?

├── Static (no animation)
│   └── Use: VElement(state=my_state)
│
├── Simple 2-state animation
│   └── Use: VElement(keystates=[start, end])
│
├── Multi-state with even timing
│   └── Use: VElement(keystates=[s1, s2, s3, s4])
│
├── Multi-state with custom timing
│   └── Use: VElement(keystates=[(0, s1), (0.3, s2), (1, s3)])
│
├── Need easing on position only?
│   └── Use: VElement(keystates=[...], attribute_easing={"pos": easing.bounce})
│
├── Need different easing per segment?
│   └── Use: KeyState objects with transition_config
│
├── Need independent field timelines?
│   │   (e.g., opacity animates differently than position)
│   └── Use: attribute_keystates parameter
│
└── Need morphing between different shapes?
    └── Use: KeyState with transition_config containing Morphing()


EASING PRIORITY (highest wins):
  1. attribute_keystates easing
  2. VElement attribute_easing
  3. KeyState transition_config.easing
  4. State DEFAULT_EASING
```

---

## Summary Table

| # | Suggestion | Complexity | Impact |
|---|------------|------------|--------|
| 1 | Rename `transition_config` | Low | High clarity |
| 2 | Explicit time distribution control | Medium | Reduces surprises |
| 3 | Easing convenience methods | Low | Better DX for common cases |
| 4 | Attribute keystates range alignment | Low | Prevents subtle bugs |
| 5 | Path function scope clarity | Low | Self-documenting |
| 6 | Validation mode | Medium | Catches errors early |
| 7 | Builder pattern | Medium | Alternative for complex cases |
| 8 | Debug timeline visualization | Medium | Aids understanding |
| 9 | Mixed format warnings | Low | Guides best practices |
| 10 | Decision tree docs | Low | Improves onboarding |

---

## Implementation Priority Recommendation

**Phase 1 (Quick Wins):**
- #1 Naming (or alias + deprecation)
- #5 Path scope clarity
- #9 Mixed format warnings
- #10 Documentation

**Phase 2 (High Value):**
- #6 Validation mode
- #3 Convenience methods
- #8 Debug timeline

**Phase 3 (Power Features):**
- #2 Time distribution control
- #4 Attribute keystates alignment
- #7 Builder pattern
