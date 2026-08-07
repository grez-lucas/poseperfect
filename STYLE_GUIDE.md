# Design System & Style Guide

**Application Name:** StageReady Bodybuilding Posing & Symmetry Analyzer  
**Design Theme:** Stage Dark / High-Contrast Purple & Gold Accent Palette  
**Version:** 1.0  

---

## 1. Aesthetic Vision & Color Palette

The visual design is engineered for high contrast in low-light gym and stage backstage environments. Dark surface cards with subtle borders prevent eye strain while high-luminance accent colors draw attention to symmetry metrics and active controls.

### Color Tokens

```kotlin
// Background & Surfaces
val StageDark = Color(0xFF1A1B1F)         // Primary Application Canvas Background
val StageSurface = Color(0xFF252528)      // Elevated Containers, Bottom Nav, App Bar
val StageCard = Color(0xFF323038)         // Content Cards, Dialogs, Bottom Sheets
val StageBorder = Color(0xFF49454F)       // Divider lines & Container strokes (1.dp)

// Primary & Accent Colors (M3 Dark Scheme Compliant)
val ElegantPurplePrimary = Color(0xFFD0BCFF)  // Primary active elements, icons, selected tabs
val DeepPurpleContainer = Color(0xFF381E72)   // Selected state backgrounds, badges
val OnPurpleContainer = Color(0xFFE8DEF8)     // Text/Icons on primary containers

// Visual Accents & Symmetry Indicators
val SymmetryGreen = Color(0xFFB6F2AF)     // Balanced Symmetry (Score >= 90%)
val SymmetryYellow = Color(0xFFE8DEF8)    // Minor Asymmetry Warning (Score 70% - 89%)
val SymmetryRed = Color(0xFFFFB4AB)       // Significant Asymmetry Alert (Score < 70%)

// Text Colors
val TextPrimary = Color(0xFFE3E2E6)       // Headlines, Title text, High emphasis
val TextSecondary = Color(0xFFC9C5D0)     // Captions, Secondary labels, Medium emphasis
```

---

## 2. Typography & Hierarchy

The application uses modern sans-serif typography with generous line heights and distinct visual weight contrast.

- **Display Large (`32.sp`, Bold):** Main countdown timer display, overall score highlights.
- **Title Large (`22.sp`, SemiBold):** Screen titles, Pose names in detail view.
- **Title Medium (`16.sp`, Medium):** Card headers, section titles, dialog headers.
- **Body Medium (`14.sp`, Normal):** Execution cues, feedback text, description paragraphs.
- **Label Small (`11.sp`, Medium):** Badge indicators, metadata tags, button labels.

---

## 3. UI Component Specifications

### 1. Cards (`StageCard`)
- **Background:** `StageCard` (`#323038`)
- **Border:** `1.dp` solid `StageBorder` (`#49454F`)
- **Corner Radius:** `16.dp`
- **Content Padding:** `16.dp` standard internal padding

### 2. Buttons & Action Chips
- **Primary Action Button:**
  - Background: `ElegantPurplePrimary` (`#D0BCFF`)
  - Content Color: `DeepPurpleContainer` (`#381E72`)
  - Shape: Fully rounded (`CircleShape`) or `12.dp` rounded corners
  - Minimum Touch Target: `48.dp x 48.dp`
- **Secondary / Surface Action Button:**
  - Background: `StageSurface` (`#252528`)
  - Border: `1.dp` `StageBorder`
  - Content Color: `TextPrimary` (`#E3E2E6`)

### 3. Bottom Navigation Bar
- **Container Color:** `StageSurface` (`#252528`)
- **Indicator Color:** `DeepPurpleContainer` (`#381E72`)
- **Selected Icon & Text Color:** `ElegantPurplePrimary` (`#D0BCFF`)
- **Unselected Icon & Text Color:** `TextSecondary` (`#C9C5D0`) with `0.7f` alpha

### 4. Symmetry Overlay & Canvas Guidelines
- **Center Alignment Line:** Dashed vertical stroke (`2.dp`), `SymmetryGreen` when centered.
- **Guideline Outlines:** Stroke width `3.dp`, color alpha `0.35f` to `0.85f`.
- **Level Gauge / HUD:** Floating semi-transparent pill container (`Color(0x99252528)`) with `CircleShape` icon toggles.

---

## 4. Spacing, Layout & Touch Rules

1. **8dp Spatial Grid:** All margins, paddings, and component heights follow multiples of 8dp (`8.dp`, `16.dp`, `24.dp`, `32.dp`).
2. **Edge-to-Edge:** Scaffold containers must handle `WindowInsets` appropriately (`statusBars`, `navigationBars`).
3. **Accessibility:** All interactive elements must maintain a minimum clickable area of `48.dp x 48.dp` and include meaningful `contentDescription` text.
4. **Test Tags:** Every interactive element must include `Modifier.testTag("snake_case_tag")` for automated verification.
