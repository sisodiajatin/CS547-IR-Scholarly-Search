---
name: ScholarPulse Precision Terminal
colors:
  surface: '#0b1326'
  surface-dim: '#0b1326'
  surface-bright: '#31394d'
  surface-container-lowest: '#060e20'
  surface-container-low: '#131b2e'
  surface-container: '#171f33'
  surface-container-high: '#222a3d'
  surface-container-highest: '#2d3449'
  on-surface: '#dae2fd'
  on-surface-variant: '#bdc8d1'
  inverse-surface: '#dae2fd'
  inverse-on-surface: '#283044'
  outline: '#87929a'
  outline-variant: '#3e484f'
  surface-tint: '#7bd0ff'
  primary: '#8ed5ff'
  on-primary: '#00354a'
  primary-container: '#38bdf8'
  on-primary-container: '#004965'
  inverse-primary: '#00668a'
  secondary: '#4edea3'
  on-secondary: '#003824'
  secondary-container: '#00a572'
  on-secondary-container: '#00311f'
  tertiary: '#ffc174'
  on-tertiary: '#472a00'
  tertiary-container: '#f59e0b'
  on-tertiary-container: '#613b00'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#c4e7ff'
  primary-fixed-dim: '#7bd0ff'
  on-primary-fixed: '#001e2c'
  on-primary-fixed-variant: '#004c69'
  secondary-fixed: '#6ffbbe'
  secondary-fixed-dim: '#4edea3'
  on-secondary-fixed: '#002113'
  on-secondary-fixed-variant: '#005236'
  tertiary-fixed: '#ffddb8'
  tertiary-fixed-dim: '#ffb95f'
  on-tertiary-fixed: '#2a1700'
  on-tertiary-fixed-variant: '#653e00'
  background: '#0b1326'
  on-background: '#dae2fd'
  surface-variant: '#2d3449'
typography:
  headline-xl:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 30px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Geist
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 18px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Geist
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: -0.005em
  body-md:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  body-sm:
    fontFamily: Geist
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 14px
  label-code-md:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: -0.01em
  label-code-sm:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 13px
    letterSpacing: -0.005em
  label-code-xs:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '500'
    lineHeight: 12px
  label-kbd:
    fontFamily: JetBrains Mono
    fontSize: 9.5px
    fontWeight: '600'
    lineHeight: 10px
    letterSpacing: 0.02em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 0.5rem
  margin: 0.75rem
  space-xs: 0.125rem
  space-sm: 0.25rem
  space-md: 0.5rem
  space-lg: 0.75rem
  space-xl: 1rem
---

## Brand & Style

This design system serves scientists, computational researchers, and literature analysts who require relentless signal-to-noise efficiency. Drawing inspiration from modern high-density utility workflows (Linear, Raycast) combined with the information saturation of institutional finance terminals (Bloomberg), the interface rejects decorative fluff in favor of immediate data manipulation, spatial discipline, and rapid context switching.

The visual style is **Technical Minimalist / Hyper-Dense Utility**:
- **Information-First Ergonomics:** Compact typographic leading, high-density line heights, and explicit column-based data alignment allow scanning thousands of citations, metrics, and synthesis graphs without cognitive friction.
- **Micro-Hairline Definition:** Structural depth is achieved strictly through sharp 1px borders, avoiding soft blurred elevations. Panes lock together with mathematical precision.
- **Instrumental Tactility:** Subtle state transitions (sub-100ms), crisp active tab markers, visual keyboard affordances (`⌘K`, `J`, `K`, `G G`), and persistent split-pane dividers provide immediate feedback tailored to keyboard-first power users.

## Colors

The palette uses a slate and deep charcoal foundation with surgical, syntax-inspired semantic highlights.

### Base Surface Architecture
- **Root Canvas (`#090d16`):** The foundational viewport backing.
- **Primary Panel Surface (`#0f172a`):** Main analytical workspace, reading panes, and inspection sheets.
- **Secondary / Recessed Surface (`#0b0f19`):** Persistent side rails, command bars, and table header rows.
- **Elevated / Popover Surface (`#1e293b`):** Modal palettes, dropdown filters, floating tooltips, and shortcut cheatsheets.

### Structural Hairlines
- **Muted Divider (`#1e293b`):** Standard interior pane boundaries and table row separators.
- **Prominent Border (`#334155`):** Active card outlines, pane focus indicators, and focused search inputs.
- **Interactive Highlight (`#475569`):** Hover boundaries and selected table row outlines.

### Monochromatic Contrast Spectrum
- **Text Dominant (`#f8fafc`):** Paper titles, quantitative figures, primary field names.
- **Text Standard (`#e2e8f0`):** Body abstracts, parameter names, citation counts.
- **Text Secondary (`#94a3b8`):** Author lists, journal sources, metadata captions.
- **Text Muted (`#64748b`):** DOIs, timestamp hashes, inactive shortcuts, grid guides.

### Functional Accent Colors
- **Primary / Electric Cyan (`#38bdf8`):** Active selections, current cursor row, hyper-focused navigation rings, primary actions.
- **Emerald / Validated (`#10b981`):** High impact factors, replicable benchmarks, open-access indicators, verified claims.
- **Amber / Synthesis (`#f59e0b`):** Pending reviews, preprint notices, medium-confidence extractions, citation warnings.
- **Violet / Semantic Entity (`#a855f7`):** Machine-extracted entities, cross-corpus embeddings, author cluster tags.
- **Rose / Critical Deficit (`#f43f5e`):** Methodological contradictions, retracted papers, network disconnects.

## Typography

Typography prioritizes information density and numerical alignment.

- **Primary Interface Type (`Geist`):** Delivers clean geometry with engineered legibility at small sizes (11px–13px). Proportional tabular figures are activated by default (`font-feature-settings: 'tnum' 1, 'cv01' 1`) to preserve vertical column integrity across data grids.
- **Technical & Metric Type (`JetBrains Mono`):** Reserved for DOIs, keyboard bindings, statistical bounds, h-indexes, citations, and terminal-style timestamps. Its strict monospaced grid ensures alignment across nested tables and compact metadata ribbons.
- **Density Rules:** Line heights remain strictly constrained between 1.25x and 1.35x for content views and 1.15x for navigation and data tables to maximize spatial efficiency.

## Layout & Spacing

The layout is built upon an adjustable **Multi-Pane Modular Workspace** with rigid containment.

- **Split-Pane Ergonomics:** The default desktop configuration uses a persistent 3-pane split:
  1. **Navigation Rail / Query Sidebar:** Fixed 240px width (collapsible to 48px icon-rail via `[ `).
  2. **Primary Record Feed / Metric Grid:** Fluid column, 380px–640px adjustable width.
  3. **Inspection / Deep Synthesis Document Viewer:** Fluid column occupying remaining canvas space.
- **Density Grid:** Spacing relies on compact multiples of 4px. Internal element paddings rarely exceed `space-md` (8px). Gaps between toolbar icons and metric badges adhere strictly to `space-xs` (2px) or `space-sm` (4px).
- **Responsive Adaptations:**
  - **Large Desktop (≥1440px):** Full 3-pane synchronous visibility with real-time graph drawers.
  - **Laptop/Standard (1024px–1439px):** 2-pane mode with the document viewer expanding into the middle pane via breadcrumb toggle or auto-focus command.
  - **Narrow (<1024px):** Single-pane active view with quick switching between list and detail using command shortcuts or a segmented control bar.

## Elevation & Depth

This design system avoids blurry drop shadows in favor of **structural hairlines, surface luminance tiering, and sharp focus boundaries**:

1. **Surface Luminance Stacking:** Depth is expressed entirely by background value steps (`#090d16` canvas -> `#0b0f19` recessed sidebars -> `#0f172a` active workspace -> `#1e293b` command bars).
2. **Hairline Seams:** Every window pane, cell border, and divider uses a 1px solid hairline (`#1e293b`). Surfaces appear as precision-cut slabs docked flush against one another.
3. **Focused Borders:** When an element or pane receives keyboard or pointer focus, the hairline border shifts cleanly to `#38bdf8` or `#475569`, accompanied by an optional inner glow of `inset 0 0 0 1px #38bdf8`.
4. **Command Overlay:** The global command palette (`⌘K`) uses an elevated `#0f172a` backdrop encased in a 1px `#334155` border, backed by an ultra-subtle directional drop shadow: `0 16px 32px -8px rgba(0, 0, 0, 0.7)`.

## Shapes

The design system uses a sharp architectural silhouette. Radii are kept minimal (4px base) to retain an instrumental, terminal-grade precision.

- **Interactive Nodes (Buttons, Chips, Inputs):** 4px (`roundedness: 1`), keeping clickable surfaces defined without softening interface edges.
- **Keyboard Badges (KBD):** 3px border-radius with crisp 1px borders, mimicking physical low-profile keycaps.
- **Split-Panes and Containers:** 0px (completely flush) against adjacent panels. Outer container boundaries apply a strict 6px radius to the overall application frame.
- **Syntax Badges and Tags:** 3px radius, avoiding rounded pills to conserve horizontal character density.

## Components

### 1. Buttons & Utility Triggers
- **Primary Utility Button:** Background `#38bdf8`, text `#090d16`, font `label-code-xs` (bold), height 26px, padding 0 8px, border-radius 4px. Focus produces a 1px offset ring.
- **Secondary Ghost Trigger:** Background transparent, border 1px solid `#334155`, text `#e2e8f0`, hover background `#1e293b`.
- **Keyboard Shortcut Affordance:** Buttons display trailing `<kbd>` tokens (e.g., `Save Abstract` `[⌘S]`).

### 2. Syntax Badges & Metadata Chips
- **Structural Spec:** Compact inline container, height 18px, padding 0 5px, font `label-code-xs`, border-radius 3px.
- **Variants:**
  - *Open Access / Replicated:* Background `rgba(16, 185, 129, 0.1)`, text `#34d399`, border `1px solid rgba(16, 185, 129, 0.25)`.
  - *Preprint / In-Review:* Background `rgba(245, 158, 11, 0.1)`, text `#fbbf24`, border `1px solid rgba(245, 158, 11, 0.25)`.
  - *Semantic / ML Extraction:* Background `rgba(168, 85, 247, 0.1)`, text `#c084fc`, border `1px solid rgba(168, 85, 247, 0.25)`.
  - *Metric Citation Pill:* Background `#1e293b`, text `#94a3b8`, border `1px solid #334155`.

### 3. Keyboard Shortcut Badges (`<kbd>`)
- Height 16px, min-width 16px, padding 0 4px, background `#1e293b`, border `1px solid #334155`, bottom-border `2px solid #475569`, text `#94a3b8`, font `label-kbd`.

### 4. Input Fields & Inline Filters
- Height 28px, background `#0b0f19`, border `1px solid #1e293b`, font `body-md`, text `#f8fafc`. Placeholder text `#64748b`.
- Active focus switches border to `#38bdf8` with no layout shift.
- Leading icon or scope chip integrated with a vertical 1px `#1e293b` divider.

### 5. Data Tables & Literature Lists
- **Row Anatomy:** Fixed 32px row height for compact view, 52px for summary view.
- **Borders:** Bottom hairline 1px solid `#1e293b`.
- **States:** Hover background `#161f30`; keyboard-selected row (`J`/`K`) receives background `#1e293b`, text `#f8fafc`, and a 2px vertical indicator bar in `#38bdf8` on the extreme left edge.

### 6. Command Palette (`⌘K`)
- Width 600px, anchored at 15% viewport height.
- Contains instant-filter input, dynamic shortcut list (`Enter` to select, `Tab` to chain, `Esc` to close), and contextual preview split for highlighted academic entities.

### 7. Monospace Data Ribbon
- Strip component placed directly under pane headers displaying query performance, corpus slice size, and token rate:
  `[CORPUS: 1.42M PAPERS] [INDEX: 12ms] [ACTIVE DOI: 10.1038/s41586-024-00000]`.