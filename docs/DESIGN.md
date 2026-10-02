# Design direction

> Copied from docs/SPEC.md. If the two ever differ, SPEC.md wins.

Save as `docs/DESIGN.md`. Every phase must follow it.

### 6.1 Mood
Quiet luxury, natural materials, architecture with greenery. Think a well-designed architecture studio website, not a SaaS template. Calm, confident, a lot of white space.

### 6.2 Tokens (put in `config/brand.yaml` and the CSS theme)
- Background: warm off-white `#F7F5F0`; surfaces `#FFFFFF`; subtle surface `#EFECE5`
- Ink (text): `#1C1F1D`; secondary text `#5E635F`; borders `#E3DFD6`
- Primary: deep forest `#2F4A3A`; sidebar `#1F2E27` with off-white text
- Accent: clay `#B5643C`, used rarely (one call to action per screen, active states)
- Status (muted, not neon): good `#3E7C59`, watch `#C08A2E`, risk `#B4483C`, neutral `#7A7F7B`
- Charts: forest, sage `#8FA88F`, sand `#C9B38C`, clay; never more than 4 colours in one chart
- Fonts: **Fraunces** for landing headings and big console page titles; **Manrope** for everything else; tabular numbers for all figures
- Radius: 10px for console cards, 2px on landing page images and buttons (sharper, architectural feel)
- Borders over shadows: 1px borders, shadows only on hover cards and drawers
- Spacing on an 8px grid; 24 to 32px between sections

### 6.3 Avoid these "AI-made" signs
Purple or blue gradients, glassmorphism, emoji as icons, every element centred, identical three-card feature grids with icons in circles, count-up number animations, generic copy like "Welcome to the future of...", lorem ipsum, stock "business people shaking hands" photos, ten different colours on one page, random badges everywhere.

### 6.4 Anti-congestion rules `[MUST]`
- Max **4 KPI cards** in a row. Max 5 KPI cards on any page.
- Above the fold: KPI row plus at most **two** main visuals. Everything else goes below or into **tabs** inside the page.
- Tables show 6 to 7 columns by default. Extra columns are available from a column chooser.
- Hover cards show 8 to 12 facts maximum.
- Drawers use tabs; each tab fits on one screen where possible.
- Content max width 1440px, centred, with generous side padding.
- Every chart has a short title that says what it shows ("Collections vs demands, last 12 months"), not just "Chart".
- Empty, loading (skeleton) and error states exist for every data block.

### 6.5 Interaction feel
- Hover cards open after about 300 ms and close on mouse leave; keyboard focus also opens them; on touch, tap opens the drawer.
- Transitions 150 to 250 ms. Respect `prefers-reduced-motion`.
- Rows highlight softly on hover. The cursor shows what is clickable.
- Drawer state lives in the URL (`?view=customer:123`), so the browser Back button closes drawers naturally.


