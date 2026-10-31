---
name: MCP Studio Minimal
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#434655'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#737686'
  outline-variant: '#c3c6d7'
  surface-tint: '#0053db'
  primary: '#004ac6'
  on-primary: '#ffffff'
  primary-container: '#2563eb'
  on-primary-container: '#eeefff'
  inverse-primary: '#b4c5ff'
  secondary: '#0058be'
  on-secondary: '#ffffff'
  secondary-container: '#2170e4'
  on-secondary-container: '#fefcff'
  tertiary: '#4d556b'
  on-tertiary: '#ffffff'
  tertiary-container: '#656d84'
  on-tertiary-container: '#eef0ff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dbe1ff'
  primary-fixed-dim: '#b4c5ff'
  on-primary-fixed: '#00174b'
  on-primary-fixed-variant: '#003ea8'
  secondary-fixed: '#d8e2ff'
  secondary-fixed-dim: '#adc6ff'
  on-secondary-fixed: '#001a42'
  on-secondary-fixed-variant: '#004395'
  tertiary-fixed: '#dae2fd'
  tertiary-fixed-dim: '#bec6e0'
  on-tertiary-fixed: '#131b2e'
  on-tertiary-fixed-variant: '#3f465c'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  display-sm:
    fontFamily: Geist
    fontSize: 1.75rem
    fontWeight: '600'
    lineHeight: 2.25rem
    letterSpacing: -0.025em
  headline-lg:
    fontFamily: Geist
    fontSize: 1.5rem
    fontWeight: '600'
    lineHeight: 2rem
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Geist
    fontSize: 1.25rem
    fontWeight: '600'
    lineHeight: 1.75rem
    letterSpacing: -0.015em
  headline-sm:
    fontFamily: Geist
    fontSize: 1.125rem
    fontWeight: '500'
    lineHeight: 1.5rem
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 1rem
    fontWeight: '400'
    lineHeight: 1.5rem
    letterSpacing: -0.005em
  body-md:
    fontFamily: Inter
    fontSize: 0.875rem
    fontWeight: '400'
    lineHeight: 1.375rem
    letterSpacing: -0.005em
  body-sm:
    fontFamily: Inter
    fontSize: 0.75rem
    fontWeight: '400'
    lineHeight: 1.125rem
    letterSpacing: '0'
  label-lg:
    fontFamily: JetBrains Mono
    fontSize: 0.875rem
    fontWeight: '500'
    lineHeight: 1.25rem
    letterSpacing: -0.01em
  label-md:
    fontFamily: JetBrains Mono
    fontSize: 0.75rem
    fontWeight: '500'
    lineHeight: 1rem
    letterSpacing: -0.005em
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 0.6875rem
    fontWeight: '500'
    lineHeight: 0.875rem
    letterSpacing: 0.02em
  code-block:
    fontFamily: JetBrains Mono
    fontSize: 0.8125rem
    fontWeight: '400'
    lineHeight: 1.35rem
    letterSpacing: '0'
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-compact: 0.5rem
  margin: 1.5rem
  margin-compact: 0.75rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1rem
  space-xl: 1.5rem
---

## Brand & Style

This design system embodies a disciplined, hyper-focused developer workspace tailored for technical architects, systems engineers, and tool-integrators orchestrating Model Context Protocol (MCP) servers and clients. The aesthetic is rooted in high-density utility, functional clarity, and distraction-free spatial composition—drawing direct influence from modern developer tooling like Linear, Raycast, and VS Code.

The emotional signature is quiet confidence, speed, and structural precision. Visual embellishments and decorative artifacts are discarded in favor of:
- **Hairline Geometry**: Deliberate, 1px structural demarcations replacing heavy elevated surfaces.
- **Calm Density**: Compact UI footprints balanced by intentional macro whitespace to prevent cognitive fatigue during complex orchestration workflows.
- **Monochrome Dominance with Singular Accentuation**: An interface primarily rendered in pure neutrals, reserving vivid blue exclusively for active states, key affordances, and protocol indicators.

## Colors

The palette leverages a crisp, daylight-calibrated surface system built on pure white and subtle cool off-whites, contrasted against high-clarity slate typography and hairline slate borders.

### Surface Architecture
- **Canvas Base (`#ffffff`)**: The default ground plane for interactive editor canvases, active panels, and primary content modules.
- **Surface Muted (`#f9fafb`)**: Applied to toolbars, sidebars, inactive inspector docks, and collapsible sub-drawers.
- **Surface Subtle (`#f3f4f6`)**: Code block backgrounds, table header bars, inline terminal segments, and badge backgrounds.

### Border System
- **Hairline Border (`#e5e7eb`)**: The standard 1px boundary dividing panels, card structures, and table rows.
- **Border Strong (`#cbd5e1`)**: Boundary state for active focus rings, selected tree nodes, and hovered form inputs.

### Text & Glyph Hierarchy
- **Text Primary (`#0f172a`)**: Dominant slate-black for headers, active values, parameter keys, and primary code syntax.
- **Text Secondary (`#475569`)**: Medium slate for explanatory labels, standard body copy, structural descriptions, and metadata keys.
- **Text Muted (`#94a3b8`)**: Passive slate for timestamps, inactive tab labels, placeholders, and keyboard shortcut glyphs.

### Accent Allocation
- **Accent Primary (`#2563eb`)**: High-intent primary buttons, active protocol indicators, active radio pills, and focus halos.
- **Accent Hover (`#1d4ed8`)**: Interactive hover states on active actions.
- **Accent Subtle (`#eff6ff`)**: Soft blue tint for selected tree item rows, badge fills, and highlighted diff segments.

## Typography

The typographic hierarchy couples **Geist** for crisp structural UI headers, **Inter** for neutral, legible parameter reading, and **JetBrains Mono** for all machine-readable values, tools, JSON payloads, and shortcuts.

- **Geist (Display & Headlines)**: Tight letter-spacing with a clean geometric structure. Headlines should remain concise, strictly sentence-cased, and avoid emotional cadence.
- **Inter (Body)**: Tuned for neutral visual transmission in lists, descriptions, and data tables. Never styled with heavy weights—standardize on `400` for content and `500` for item titles.
- **JetBrains Mono (Code & Metadata)**: Anchors server endpoints, schema definitions, protocol method badges (e.g., `prompts/list`, `tools/call`), terminal logs, and system metrics. Tabular figures are enforced across numbers to maintain vertical alignment in tables.

## Layout & Spacing

Layouts adhere to an engineering IDE composition: multi-pane structural layouts, pinned header utilities, and strict grid alignments that mirror modern desktop command centers.

### Layout Model
- **Three-Tier Workspace Layout**:
  1. *Sidebar Dock* (fixed 240px–280px): Hierarchical navigation, registered servers, and tool collections.
  2. *Primary Canvas* (fluid flex-fill): The active context editor, JSON schema inspector, or payload log.
  3. *Auxiliary Inspector* (collapsible 320px–360px): Connection stats, latency readouts, environment variable maps, and test call runtimes.
- **Visual Section Limit**: Cap screens at 3–4 visible content panes simultaneously to preserve scan speed and reduce sensory clutter.
- **Whitespace Discipline**: Use macro whitespace (`space-xl` / `margin`) along panel margins to separate disparate functional domains, but rely on micro spacing (`space-xs` to `space-sm`) inside tool groups and list trees to preserve technical density.

### Breakpoints & Adaptations
- **Desktop (>= 1280px)**: Three panes visible simultaneously, fixed 1px vertical panel dividers.
- **Tablet / Laptop (1024px – 1279px)**: Auxiliary Inspector collapses into an on-demand slide-over drawer; sidebar switches to icon-and-label compact mode.
- **Mobile (< 1024px)**: Single-pane stack with bottom sheet execution triggers and slide-in side navigation.

## Elevation & Depth

Visual hierarchy is constructed entirely through **planar layering, tonal variation, and 1px hairline dividers**. Deep drop shadows, colored glows, and blurred diffusion filters are deliberately omitted.

### Depth Mechanisms
- **Level 0 (Base Canvas)**: Pure white (`#ffffff`) for active work surfaces, editor panels, and table cells.
- **Level 1 (Sub-Panels & Sidebars)**: Solid `#f9fafb` with a right/left 1px border of `#e5e7eb`. No drop shadow.
- **Level 2 (Dropdowns, Overlays & Command Menus)**: Solid `#ffffff` surface, bounded by a 1px `#cbd5e1` hairline border, accompanied by a precise micro-shadow: `0 1px 3px 0 rgba(15, 23, 42, 0.05)`.
- **Level 3 (Modal Dialogs)**: Solid `#ffffff` with a hairline `#cbd5e1` border, backed by a clean neutral dimming scrim: `rgba(15, 23, 42, 0.35)`.

## Shapes

The design system employs a restrained **Soft (`1`)** corner geometry. Roundedness is strictly constrained to maintain an engineered, precision-tooled feel.

- **Base Radius (`0.25rem` / 4px)**: Standard for inputs, buttons, tree item hover states, code tags, and inline badges.
- **Container Radius (`0.375rem` / 6px to `0.5rem` / 8px)**: Applied to cards, code view containers, floating command panels, and modal shells.
- **Pill Exceptions**: Avoid fully rounded pill geometries, except for live server connection status indicators (e.g., a 6px circular dot) and numeric count chips.

## Components

### Buttons
- **Primary**: Background `#2563eb`, text `#ffffff`, border transparent, hover `#1d4ed8`. Height: 32px (compact) or 36px (standard). Typography: `body-sm` with medium weight.
- **Secondary / Outline**: Background `#ffffff`, text `#0f172a`, 1px border `#e5e7eb`, hover background `#f9fafb`, active `#f3f4f6`.
- **Ghost / Tool**: Background transparent, text `#475569`, hover text `#0f172a`, hover background `#f3f4f6`. Used in panel headers, icon buttons, and code copy triggers.
- **Single Primary Rule**: Only one primary blue button may exist per panel context to eliminate workflow ambiguity.

### Inputs & Form Fields
- **Text & Search Inputs**: Height 32px or 36px. Background `#ffffff`, border 1px `#e5e7eb`, text `#0f172a`, placeholder `#94a3b8`. Focus state applies a 1px border `#2563eb` and an outer hairline ring `0 0 0 1px #2563eb`.
- **Monospace Parameters**: Background `#f9fafb`, font `label-md` (JetBrains Mono). Used for tool parameters, URI inputs, and authentication tokens.

### Tree Views & Lists
- **Item Heights**: 28px for dense tree nodes, 36px for server lists.
- **Selection State**: Background `#eff6ff`, text `#2563eb`, with a vertical 2px left border accent of `#2563eb`.
- **Hover State**: Background `#f9fafb`, text `#0f172a`.
- **Row Separators**: 1px border-bottom `#f3f4f6`.

### Chips & Badges
- **Protocol Method Badges**: `GET`, `POST`, `RPC`, `TOOL`, `PROMPT`. Background `#f3f4f6`, text `#475569`, border 1px `#e5e7eb`, font `label-sm`.
- **Active State Chip**: Background `#eff6ff`, text `#2563eb`, border 1px `rgba(37, 99, 235, 0.2)`.

### Checkboxes & Toggle Controls
- **Checkbox**: 14x14px box, 2px corner radius. Inactive: border 1px `#cbd5e1`. Checked: background `#2563eb`, white checkmark icon.
- **Switch**: 28px width, 16px height. Inactive track: `#e2e8f0`. Active track: `#2563eb`. Thumb: 12px white circle.

### Code & Schema Panels
- **Container**: Border 1px `#e5e7eb`, header toolbar `#f9fafb`, body `#ffffff` or `#f9fafb`.
- **Syntax Display**: Typography `code-block` (JetBrains Mono). Crisp line numbering in `#94a3b8`, hairline vertical guide lines in `#e5e7eb`.

### Command Palette (Raycast-Style)
- **Overlay Window**: Max-width 640px, floating centered, background `#ffffff`, border 1px `#cbd5e1`, micro-shadow.
- **Search Header**: Monospace or Geist search field, borderless bottom separator `#e5e7eb`.
- **List Results**: Keybinding hints floated right in discrete `#f3f4f6` kbd chips with text `#64748b`.