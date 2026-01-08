# AutoAnn Platform - Production UI Design Specification

## Executive Summary

This document outlines the design specification for the **CaliperAI AutoAnn Platform** - an enterprise-grade AI annotation service where customers upload data, run annotation models, and download results.

---

## 1. Design Philosophy

### Target Audience
- **Enterprise ML Teams** running production annotation workloads
- **Data Scientists** who need reliable, trackable annotation pipelines
- **Operations Teams** monitoring job status and resource usage

### Design Principles
1. **Data-First**: Jobs and their status are the primary focus
2. **Professional Trust**: Clean, minimal design that conveys reliability
3. **Efficiency**: Minimize clicks to complete common tasks
4. **Clarity**: Clear visual hierarchy and status indicators

### Inspiration References
- **Replicate.com** - Clean model execution interface
- **Hugging Face Spaces** - Modern AI platform aesthetic
- **Vercel Dashboard** - Professional deployment tracking
- **Linear** - Premium dark theme execution

---

## 2. Color Palette

### Primary Theme: Dark Professional

```
Background Layers:
├── Base Background:     #0a0e1a (Deep navy black)
├── Card/Surface:        #111827 (Elevated surface)
├── Sidebar:             #080c14 (Darker sidebar)
└── Hover/Active:        #1f2937 (Interactive states)

Brand Colors:
├── Primary Accent:      #8b5cf6 (Violet - main CTA)
├── Primary Hover:       #a78bfa (Lighter violet)
└── Primary Glow:        rgba(139, 92, 246, 0.3)

Status Colors:
├── Success:             #10b981 (Emerald green)
├── Running:             #3b82f6 (Blue with pulse animation)
├── Queued:              #f59e0b (Amber)
├── Failed:              #ef4444 (Red)
└── Cancelled:           #6b7280 (Gray)

Text Hierarchy:
├── Primary Text:        #f9fafb (Near white)
├── Secondary Text:      #9ca3af (Muted gray)
├── Tertiary Text:       #6b7280 (Subtle gray)
└── Disabled:            #4b5563 (Dark gray)

Borders:
├── Default:             #1f2937 (Subtle)
├── Hover:               #374151 (Visible on interaction)
└── Focus:               #8b5cf6 (Brand color ring)
```

---

## 3. Typography

```
Font Family: Inter (Google Font) or system-ui fallback

Headings:
├── H1 (Page Title):     32px / 700 weight / -0.02em tracking
├── H2 (Section):        24px / 600 weight / -0.01em tracking
├── H3 (Card Title):     18px / 600 weight / normal
└── H4 (Label):          14px / 500 weight / normal

Body:
├── Body Large:          16px / 400 weight / normal
├── Body:                14px / 400 weight / normal
├── Body Small:          13px / 400 weight / normal
└── Caption:             12px / 400 weight / 0.02em tracking

Monospace (for IDs, paths):
└── Code:                13px / JetBrains Mono or monospace
```

---

## 4. Page Layouts

### 4.1 Login Page

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  ┌─────────────────────────┐  ┌──────────────────────────────────┐  │
│  │                         │  │                                  │  │
│  │     BRANDING PANEL      │  │         LOGIN FORM               │  │
│  │                         │  │                                  │  │
│  │  ┌───────────────────┐  │  │   ┌────────────────────────┐     │  │
│  │  │    [LOGO ICON]    │  │  │   │  Welcome Back          │     │  │
│  │  │                   │  │  │   │  Sign in to continue   │     │  │
│  │  │    CaliperAI      │  │  │   └────────────────────────┘     │  │
│  │  │                   │  │  │                                  │  │
│  │  │  Auto-Annotation  │  │  │   Email                          │  │
│  │  │     Platform      │  │  │   ┌────────────────────────┐     │  │
│  │  └───────────────────┘  │  │   │ admin@example.com      │     │  │
│  │                         │  │   └────────────────────────┘     │  │
│  │  "Enterprise-grade AI   │  │                                  │  │
│  │   annotation at scale"  │  │   Password                       │  │
│  │                         │  │   ┌────────────────────────┐     │  │
│  │  ┌─────────────────────┐│  │   │ ••••••••               │     │  │
│  │  │ ✓ 50M+ annotations  ││  │   └────────────────────────┘     │  │
│  │  │ ✓ 99.9% uptime      ││  │                                  │  │
│  │  │ ✓ SOC2 compliant    ││  │   ┌────────────────────────┐     │  │
│  │  └─────────────────────┘│  │   │      Sign In  →        │     │  │
│  │                         │  │   └────────────────────────┘     │  │
│  │  Gradient background    │  │                                  │  │
│  │  with subtle pattern    │  │   Forgot password?               │  │
│  │                         │  │                                  │  │
│  └─────────────────────────┘  └──────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

Left Panel: Gradient from #1e1b4b → #0f172a with subtle grid pattern
Right Panel: Solid dark #0a0e1a
```

---

### 4.2 Dashboard (Main View After Login)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ SIDEBAR (240px)           │  MAIN CONTENT AREA                               │
│ ─────────────────────────────────────────────────────────────────────────────│
│ ┌───────────────────────┐ │  ┌────────────────────────────────────────────┐  │
│ │ [◆] CaliperAI         │ │  │  HEADER BAR                                │  │
│ └───────────────────────┘ │  │  Dashboard          [+ New Job] [🔔] [👤]  │  │
│                           │  └────────────────────────────────────────────┘  │
│ MAIN NAVIGATION           │                                                  │
│ ┌───────────────────────┐ │  ┌─────────────────────────────────────────────┐ │
│ │ ◉ Dashboard           │ │  │  WELCOME BANNER                            │ │
│ │ ○ Jobs                │ │  │  "Good morning, Admin"                     │ │
│ │ ○ Pipelines           │ │  │  "You have 3 jobs running"     [View All →]│ │
│ │ ○ Data Sources        │ │  └─────────────────────────────────────────────┘ │
│ └───────────────────────┘ │                                                  │
│                           │  STATS ROW                                       │
│ QUICK ACTIONS             │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────┐ │
│ ┌───────────────────────┐ │  │ Total    │ │ Running  │ │ Success  │ │Failed│ │
│ │ [+] New Annotation Job│ │  │   47     │ │    3     │ │   41     │ │  3   │ │
│ └───────────────────────┘ │  │ ↑12%     │ │ ● active │ │ 95.3%    │ │ 6.4% │ │
│                           │  └──────────┘ └──────────┘ └──────────┘ └──────┘ │
│ ─────────────────────────────────────────────────────────────────────────────│
│                           │                                                  │
│ RESOURCES                 │  ACTIVE JOBS (Live updating)                     │
│ ┌───────────────────────┐ │  ┌─────────────────────────────────────────────┐ │
│ │ ○ Documentation       │ │  │ ● RUNNING  image_auto_annotation_2d        │ │
│ │ ○ API Reference       │ │  │   gs://bucket/project-a/batch-001           │ │
│ │ ○ Support             │ │  │   Started 12 min ago    ████████░░ 78%     │ │
│ └───────────────────────┘ │  ├─────────────────────────────────────────────┤ │
│                           │  │ ● RUNNING  3d_point_cloud_segmentation     │ │
│                           │  │   gs://bucket/lidar-data/scene-42           │ │
│ ─────────────────────────────│   Started 3 min ago     ██░░░░░░░░ 15%     │ │
│                           │  ├─────────────────────────────────────────────┤ │
│ WORKSPACE                 │  │ ◐ QUEUED   semantic_segmentation           │ │
│ ┌───────────────────────┐ │  │   gs://bucket/street-view/batch-12          │ │
│ │ Org: Caliper AI       │ │  │   Waiting in queue (position #2)           │ │
│ │ Plan: Enterprise      │ │  └─────────────────────────────────────────────┘ │
│ │ Usage: 847/1000 jobs  │ │                                                  │
│ └───────────────────────┘ │  RECENT COMPLETED                                │
│                           │  ┌─────────────────────────────────────────────┐ │
│ ┌───────────────────────┐ │  │ Job ID      Pipeline         Status   Time │ │
│ │ [?] Help & Support    │ │  │ ─────────────────────────────────────────── │ │
│ └───────────────────────┘ │  │ job_a8f2   2d_detection     ✓ Done   2m ago│ │
│                           │  │ job_7bc1   3d_tracking      ✓ Done   15m   │ │
│                           │  │ job_4de9   segmentation     ✗ Failed 1h    │ │
│                           │  └─────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘

Sidebar: #080c14 background
Main: #0a0e1a background  
Cards: #111827 with 1px #1f2937 border
Active nav item: #8b5cf6 left border + #1f2937 background
```

---

### 4.3 Jobs List Page

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ [SIDEBAR]                 │  Jobs                      [+ New Job] [🔔] [👤] │
│                           │  ─────────────────────────────────────────────── │
│                           │                                                  │
│                           │  ┌─────────────────────────────────────────────┐ │
│                           │  │ FILTER BAR                                  │ │
│                           │  │ [All ▼] [Running ▼] [Date ▼]  🔍 Search... │ │
│                           │  └─────────────────────────────────────────────┘ │
│                           │                                                  │
│                           │  ┌─────────────────────────────────────────────┐ │
│                           │  │ JOB TABLE                                   │ │
│                           │  │ ───────────────────────────────────────────  │ │
│                           │  │ Status   Job ID        Pipeline    Input    │ │
│                           │  │ ───────────────────────────────────────────  │ │
│                           │  │ ● Run    job_a8f2...   2d_detect   gs://... │ │
│                           │  │ ● Run    job_7bc1...   3d_track    gs://... │ │
│                           │  │ ◐ Queue  job_4de9...   segment     gs://... │ │
│                           │  │ ✓ Done   job_2ab3...   2d_detect   gs://... │ │
│                           │  │ ✓ Done   job_9ef4...   tracking    gs://... │ │
│                           │  │ ✗ Fail   job_1cd5...   segment     gs://... │ │
│                           │  │                                             │ │
│                           │  │ [< Prev]  Page 1 of 5  [Next >]             │ │
│                           │  └─────────────────────────────────────────────┘ │
│                           │                                                  │
└──────────────────────────────────────────────────────────────────────────────┘

Table rows: Hover state with #1f2937 background
Status badges: Pill-shaped with status color background at 20% opacity
```

---

### 4.4 New Job Page (Create Annotation Job)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ [SIDEBAR]                 │  New Annotation Job                    [👤]     │
│                           │  ─────────────────────────────────────────────── │
│                           │                                                  │
│                           │  PROGRESS STEPPER                                │
│                           │  ┌─────────────────────────────────────────────┐ │
│                           │  │  ①───────②───────③───────④                  │ │
│                           │  │  Model   Data    Config  Review              │ │
│                           │  └─────────────────────────────────────────────┘ │
│                           │                                                  │
│                           │  ┌─────────────────────────────────────────────┐ │
│                           │  │  STEP 1: Select Annotation Model            │ │
│                           │  │  ─────────────────────────────────────────  │ │
│                           │  │                                             │ │
│                           │  │  ┌─────────────┐  ┌─────────────┐           │ │
│                           │  │  │ [✓ SELECTED]│  │             │           │ │
│                           │  │  │  2D Object  │  │  3D Point   │           │ │
│                           │  │  │  Detection  │  │   Cloud     │           │ │
│                           │  │  │             │  │             │           │ │
│                           │  │  │  Detect and │  │  Segment    │           │ │
│                           │  │  │  label 2D   │  │  and label  │           │ │
│                           │  │  │  objects    │  │  3D points  │           │ │
│                           │  │  └─────────────┘  └─────────────┘           │ │
│                           │  │                                             │ │
│                           │  │  ┌─────────────┐  ┌─────────────┐           │ │
│                           │  │  │  Semantic   │  │  Instance   │           │ │
│                           │  │  │ Segmentatio │  │  Tracking   │           │ │
│                           │  │  │             │  │             │           │ │
│                           │  │  │  Pixel-wise │  │  Track obj  │           │ │
│                           │  │  │  labels     │  │  over time  │           │ │
│                           │  │  └─────────────┘  └─────────────┘           │ │
│                           │  │                                             │ │
│                           │  │              [Cancel]  [Continue →]         │ │
│                           │  └─────────────────────────────────────────────┘ │
│                           │                                                  │
└──────────────────────────────────────────────────────────────────────────────┘

Selected card: #8b5cf6 border with #8b5cf6/10 background
Unselected: #1f2937 border, hover shows #374151 border
```

---

### 4.5 Job Detail Page

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ [SIDEBAR]                 │  ← Back to Jobs                        [👤]     │
│                           │  ─────────────────────────────────────────────── │
│                           │                                                  │
│                           │  ┌─────────────────────────────────────────────┐ │
│                           │  │  JOB HEADER                                 │ │
│                           │  │  ───────────────────────────────────────────│ │
│                           │  │  job_a8f2c91d                   ● RUNNING  │ │
│                           │  │  image_auto_annotation_2d                   │ │
│                           │  │  Started: Jan 9, 2026 at 10:42 AM           │ │
│                           │  │                                             │ │
│                           │  │  [Cancel Job]  [View Logs]  [Download ↓]   │ │
│                           │  └─────────────────────────────────────────────┘ │
│                           │                                                  │
│                           │  ┌──────────────────┐ ┌────────────────────────┐ │
│                           │  │ PROGRESS         │ │ DETAILS                │ │
│                           │  │ ────────────────  │ │ ──────────────────────│ │
│                           │  │                  │ │                        │ │
│                           │  │  ████████████░░  │ │  Pipeline:             │ │
│                           │  │     78%         │ │  image_auto_annotation │ │
│                           │  │                  │ │                        │ │
│                           │  │  ETA: ~4 min     │ │  Input:                │ │
│                           │  │                  │ │  gs://bucket/data/...  │ │
│                           │  │  Items: 780/1000 │ │                        │ │
│                           │  │                  │ │  Output:               │ │
│                           │  └──────────────────┘ │  gs://bucket/output/.. │ │
│                           │                       │                        │ │
│                           │  ┌──────────────────┐ │  Airflow Run ID:       │ │
│                           │  │ LIVE LOGS        │ │  manual__2026-01-09... │ │
│                           │  │ ────────────────  │ └────────────────────────┘ │
│                           │  │ [10:42:01] Start │                            │
│                           │  │ [10:42:03] Load  │                            │
│                           │  │ [10:42:15] Proc  │                            │
│                           │  │ [10:43:22] Batch │                            │
│                           │  │ ...              │                            │
│                           │  └──────────────────┘                            │
└──────────────────────────────────────────────────────────────────────────────┘

Progress bar: Gradient from #8b5cf6 to #3b82f6
Logs panel: Monospace font, #080c14 background
```

---

## 5. Component Specifications

### 5.1 Buttons

```
PRIMARY (Main CTA)
├── Background: #8b5cf6
├── Text: #ffffff
├── Hover: #a78bfa + subtle glow
├── Border-radius: 8px
├── Padding: 12px 24px
└── Font: 14px / 500 weight

SECONDARY
├── Background: transparent
├── Border: 1px solid #374151
├── Text: #f9fafb
├── Hover: Background #1f2937
└── Same sizing as primary

GHOST
├── Background: transparent
├── Text: #9ca3af
├── Hover: Text #f9fafb, Background #1f2937
└── No border

DESTRUCTIVE
├── Background: #ef4444
├── Text: #ffffff
├── Hover: #dc2626
└── Used for cancel/delete actions
```

### 5.2 Status Badges

```
┌─────────────────────────────────────────┐
│  ● Running   - Blue (#3b82f6)           │
│               Pulsing dot animation     │
│               Background: #3b82f6/15    │
├─────────────────────────────────────────┤
│  ◐ Queued    - Amber (#f59e0b)          │
│               Background: #f59e0b/15    │
├─────────────────────────────────────────┤
│  ✓ Success   - Green (#10b981)          │
│               Background: #10b981/15    │
├─────────────────────────────────────────┤
│  ✗ Failed    - Red (#ef4444)            │
│               Background: #ef4444/15    │
├─────────────────────────────────────────┤
│  ○ Cancelled - Gray (#6b7280)           │
│               Background: #6b7280/15    │
└─────────────────────────────────────────┘

Badge specs:
├── Padding: 4px 12px
├── Border-radius: 9999px (pill)
├── Font: 12px / 500 weight
└── Dot: 6px circle with matching color
```

### 5.3 Cards

```
DEFAULT CARD
├── Background: #111827
├── Border: 1px solid #1f2937
├── Border-radius: 12px
├── Padding: 24px
└── Hover: Border #374151 (interactive cards)

STAT CARD
├── Same as default
├── Icon: 40px container, #8b5cf6/15 background
├── Value: 32px / 600 weight
├── Label: 14px / muted color
└── Change indicator: Small text with ↑/↓ icon

PIPELINE CARD (Selection)
├── Same as default
├── Selected state: #8b5cf6 border, #8b5cf6/10 background
├── Checkmark icon in corner when selected
└── Hover: Slight scale transform (1.02)
```

### 5.4 Input Fields

```
TEXT INPUT
├── Background: #111827
├── Border: 1px solid #374151
├── Border-radius: 8px
├── Padding: 12px 16px
├── Text: #f9fafb
├── Placeholder: #6b7280
├── Focus: Border #8b5cf6, Ring 2px #8b5cf6/20
└── Height: 44px

TEXTAREA
├── Same as text input
├── Min-height: 120px
└── Resize: vertical only

SELECT/DROPDOWN
├── Same as text input
├── Chevron icon on right
└── Dropdown: Same card styling as cards
```

---

## 6. Micro-interactions & Animations

### Transitions
```
Default transition: 150ms ease-out
├── Hover states
├── Focus states
└── Color changes

Slower transitions: 300ms ease-out
├── Sidebar collapse
├── Modal open/close
└── Page transitions

Animations:
├── Running status: Pulse animation (2s infinite)
├── Loading: Spin animation (1s linear infinite)
├── Success: Brief scale + fade (check icon)
└── Progress bar: Smooth width transition
```

### Loading States
```
SKELETON LOADERS
├── Background: Linear gradient animation
├── From: #1f2937
├── To: #374151
└── Duration: 1.5s infinite

SPINNER
├── Border: 2px solid #374151
├── Border-top: 2px solid #8b5cf6
├── Size: 20px (small), 32px (medium), 48px (large)
└── Animation: Spin 1s linear infinite
```

---

## 7. Responsive Behavior

```
BREAKPOINTS
├── Mobile: < 768px (sidebar collapses to bottom nav)
├── Tablet: 768px - 1024px (sidebar collapsible)
├── Desktop: 1024px - 1440px (full layout)
└── Large: > 1440px (max-width container)

MOBILE ADAPTATIONS
├── Sidebar → Bottom tab bar with 4 main items
├── Stats grid → 2 columns instead of 4
├── Job table → Card list view
└── Stepper → Vertical on mobile
```

---

## 8. Approval Checklist

Please review and confirm:

- [ ] **Color Palette**: Dark theme with violet accent acceptable?
- [ ] **Layout Structure**: Sidebar + main content layout works?
- [ ] **Status Indicators**: Color coding for job states clear?
- [ ] **Typography**: Inter font family acceptable?
- [ ] **Component Style**: Rounded corners, subtle borders approach?
- [ ] **Login Page**: Split layout with branding panel?
- [ ] **Dashboard Focus**: Active jobs prominently displayed?
- [ ] **Job Creation**: Multi-step wizard with card selection?

---

## 9. Implementation Notes

Once approved, implementation will:

1. Update CSS variables in `globals.css`
2. Install Inter font via `next/font`
3. Rebuild all layout components
4. Redesign each page with new components
5. Add proper loading states and animations
6. Test across all pages for consistency

**Estimated time**: 2-3 hours for full implementation

---

*Prepared for: CaliperAI AutoAnn Platform*
*Version: 1.0*
*Date: January 9, 2026*
