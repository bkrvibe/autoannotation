# Frontend Style Guide

This document describes the styling system, colors, fonts, and design patterns used in the AutoAnnotation frontend. Use this as a reference for implementing similar styling in other applications.

---

## Tech Stack

| Component | Technology | Version |
|-----------|------------|---------|
| CSS Framework | Tailwind CSS | v3.3.0 |
| Component Library | Radix UI | Various |
| Icon Library | Lucide React | v0.562.0 |
| Variant Management | Class Variance Authority (CVA) | v0.7.1 |
| Class Merging | tailwind-merge | v3.4.0 |
| Animations | tailwindcss-animate | v1.0.7 |

---

## Color System

The application uses HSL-based CSS variables for complete theming flexibility. All colors are defined in `globals.css` and referenced via Tailwind config.

### CSS Variables

```css
:root {
  /* Background Colors */
  --background: 222 47% 5%;           /* Main dark navy background */
  --foreground: 210 40% 98%;          /* Primary text (near-white) */

  /* Card & Popover */
  --card: 222 47% 7%;                 /* Card background */
  --card-foreground: 210 40% 98%;     /* Card text */
  --popover: 222 47% 7%;              /* Popover background */
  --popover-foreground: 210 40% 98%;  /* Popover text */

  /* Primary Brand Color (Violet) */
  --primary: 258 90% 66%;             /* Bright violet */
  --primary-foreground: 0 0% 100%;    /* White on primary */

  /* Accent (Same as primary for consistency) */
  --accent: 258 90% 66%;
  --accent-foreground: 0 0% 100%;

  /* Secondary & Muted */
  --secondary: 222 47% 11%;           /* Darker secondary bg */
  --secondary-foreground: 210 40% 98%;
  --muted: 222 47% 11%;               /* Muted background */
  --muted-foreground: 215 20% 55%;    /* Gray muted text */

  /* Status Colors */
  --destructive: 0 84% 60%;           /* Red (errors/delete) */
  --destructive-foreground: 0 0% 100%;
  --success: 152 76% 40%;             /* Green (completion) */
  --success-foreground: 0 0% 100%;
  --warning: 38 92% 50%;              /* Orange (warnings) */
  --warning-foreground: 0 0% 0%;
  --info: 217 91% 60%;                /* Blue (information) */
  --info-foreground: 0 0% 100%;

  /* UI Elements */
  --border: 222 47% 12%;              /* Border color */
  --input: 222 47% 11%;               /* Input background */
  --ring: 258 90% 66%;                /* Focus ring (violet) */
  --radius: 0.5rem;                   /* Default border radius (8px) */

  /* Sidebar Specific */
  --sidebar: 222 47% 4%;              /* Darkest (sidebar bg) */
  --sidebar-foreground: 210 40% 98%;
  --sidebar-border: 222 47% 10%;
  --sidebar-accent: 258 90% 66%;
  --sidebar-muted: 215 20% 45%;
}
```

### Hex Color Reference

| Purpose | HSL | Approximate Hex |
|---------|-----|-----------------|
| Background | 222 47% 5% | `#0a0e1a` |
| Card | 222 47% 7% | `#0f1424` |
| Secondary | 222 47% 11% | `#151c30` |
| Border | 222 47% 12% | `#171f35` |
| Primary (Violet) | 258 90% 66% | `#8b5cf6` |
| Foreground | 210 40% 98% | `#f8fafc` |
| Muted Text | 215 20% 55% | `#7e8a9f` |
| Destructive | 0 84% 60% | `#ef4444` |
| Success | 152 76% 40% | `#16a34a` |
| Warning | 38 92% 50% | `#f59e0b` |
| Info | 217 91% 60% | `#3b82f6` |

### Status Badge Colors

```css
/* Status-specific colors with transparency */
.status-queued    { bg: amber-500/15,   text: amber-400,   border: amber-500/20 }
.status-running   { bg: blue-500/15,    text: blue-400,    border: blue-500/20 }
.status-success   { bg: emerald-500/15, text: emerald-400, border: emerald-500/20 }
.status-failed    { bg: red-500/15,     text: red-400,     border: red-500/20 }
.status-cancelled { bg: zinc-500/15,    text: zinc-400,    border: zinc-500/20 }
.status-pending   { bg: violet-500/15,  text: violet-400,  border: violet-500/20 }
```

---

## Typography

### Font Families

```javascript
// Google Fonts (Next.js configuration)
import { Inter, Orbitron } from 'next/font/google';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter'
});

const orbitron = Orbitron({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-orbitron'
});
```

| Font | Usage | CSS Variable |
|------|-------|--------------|
| **Inter** | Body text, UI elements | `--font-inter` |
| **Orbitron** | Branding, display headings | `--font-orbitron` |

### Tailwind Font Config

```javascript
// tailwind.config.js
fontFamily: {
  orbitron: ['var(--font-orbitron)'],
}
```

### Typography Scale

| Class | Size | Usage |
|-------|------|-------|
| `text-xs` | 12px | Small labels, timestamps |
| `text-sm` | 14px | Default text, inputs |
| `text-base` | 16px | Body text, card titles |
| `text-lg` | 18px | Section headers |
| `text-2xl` | 24px | Large headings |
| `text-3xl` | 30px | Stats, major values |

### Font Weights

| Class | Weight | Usage |
|-------|--------|-------|
| `font-medium` | 500 | Interactive elements |
| `font-semibold` | 600 | Card titles, labels |
| `font-bold` | 700 | Major headings, stats |

---

## Spacing System

Standard Tailwind spacing scale is used:

| Value | Pixels | Common Usage |
|-------|--------|--------------|
| `1` | 4px | Tiny gaps |
| `1.5` | 6px | Icon spacing |
| `2` | 8px | Small padding |
| `3` | 12px | Component gaps |
| `4` | 16px | Standard padding |
| `6` | 24px | Section padding |
| `8` | 32px | Major sections |

### Common Patterns

```css
/* Card padding */
p-4, p-6

/* Button padding */
px-5 py-2 (default)
px-4 py-2 (small)
px-8 py-3 (large)

/* Gap between elements */
gap-1.5, gap-2, gap-3

/* Section margins */
mt-8, mb-6
```

---

## Border Radius

```javascript
// tailwind.config.js
borderRadius: {
  lg: 'var(--radius)',              // 8px (0.5rem)
  md: 'calc(var(--radius) - 2px)', // 6px
  sm: 'calc(var(--radius) - 4px)', // 4px
}
```

| Class | Size | Usage |
|-------|------|-------|
| `rounded-sm` | 4px | Small elements |
| `rounded-md` | 6px | Buttons, inputs |
| `rounded-lg` | 8px | Cards, modals |
| `rounded-full` | 9999px | Badges, avatars |

---

## Component Variants (CVA Pattern)

### Button Variants

```typescript
import { cva } from 'class-variance-authority';

const buttonVariants = cva(
  // Base classes
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90 hover:shadow-[0_0_20px_-5px_hsl(var(--primary)/0.4)]",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-border bg-transparent hover:bg-secondary",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-secondary hover:text-foreground",
        link: "text-primary underline-offset-4 hover:underline",
        success: "bg-[hsl(var(--success))] text-white hover:bg-[hsl(var(--success))]/90",
      },
      size: {
        default: "h-10 px-5 py-2",
        sm: "h-9 rounded-lg px-4 text-xs",
        lg: "h-12 rounded-lg px-8 text-base",
        icon: "h-10 w-10",
        "icon-sm": "h-8 w-8",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);
```

### Badge Variants

```typescript
const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground",
        secondary: "border-transparent bg-secondary text-secondary-foreground",
        destructive: "border-transparent bg-destructive text-destructive-foreground",
        outline: "text-foreground",
        success: "border-transparent bg-green-100 text-green-800 dark:bg-green-900",
        warning: "border-transparent bg-yellow-100 text-yellow-800 dark:bg-yellow-900",
        info: "border-transparent bg-blue-100 text-blue-800 dark:bg-blue-900",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);
```

---

## Custom Utility Classes

Add these to your `globals.css`:

```css
@layer components {
  /* Gradient text effect */
  .text-gradient {
    @apply bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent;
  }

  /* Violet glow effect */
  .glow {
    box-shadow: 0 0 20px -5px hsl(var(--primary) / 0.4);
  }

  .glow-sm {
    box-shadow: 0 0 10px -3px hsl(var(--primary) / 0.3);
  }

  /* Glassmorphism effect */
  .glass {
    @apply bg-card/80 backdrop-blur-xl;
  }
}

@layer utilities {
  /* Consistent focus ring */
  .focus-ring {
    @apply focus:ring-2 focus:ring-primary/50 focus:ring-offset-2 focus:ring-offset-background;
  }

  /* Transition presets */
  .transition-default {
    @apply transition-all duration-150 ease-out;
  }

  .transition-slow {
    @apply transition-all duration-300 ease-out;
  }
}
```

---

## Animations

### Keyframe Definitions

```css
@keyframes status-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
```

### Animation Classes

```css
.animate-status-pulse {
  animation: status-pulse 2s ease-in-out infinite;
}

.animate-fade-in {
  animation: fade-in 0.3s ease-out;
}

.skeleton {
  background: linear-gradient(
    90deg,
    hsl(var(--muted)) 25%,
    hsl(var(--muted-foreground) / 0.1) 50%,
    hsl(var(--muted)) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}
```

### Tailwind Animation Config

```javascript
// tailwind.config.js
keyframes: {
  "accordion-down": {
    from: { height: "0" },
    to: { height: "var(--radix-accordion-content-height)" },
  },
  "accordion-up": {
    from: { height: "var(--radix-accordion-content-height)" },
    to: { height: "0" },
  },
},
animation: {
  "accordion-down": "accordion-down 0.2s ease-out",
  "accordion-up": "accordion-up 0.2s ease-out",
},
```

---

## Global Styles

```css
@layer base {
  * {
    @apply border-border;
  }

  html {
    @apply antialiased;
  }

  body {
    @apply bg-background text-foreground;
    font-feature-settings: "rlig" 1, "calt" 1;
  }

  /* Custom scrollbar */
  ::-webkit-scrollbar {
    width: 6px;
    height: 6px;
  }

  ::-webkit-scrollbar-track {
    background: transparent;
  }

  ::-webkit-scrollbar-thumb {
    background: hsl(var(--border));
    border-radius: 3px;
  }

  ::-webkit-scrollbar-thumb:hover {
    background: hsl(var(--muted-foreground) / 0.5);
  }
}
```

---

## Tailwind Config (Complete)

```javascript
// tailwind.config.js
const { fontFamily } = require("tailwindcss/defaultTheme");

/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        orbitron: ['var(--font-orbitron)'],
      },
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
```

---

## Utility Function

```typescript
// lib/utils.ts
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

---

## NPM Dependencies

```json
{
  "dependencies": {
    "tailwindcss": "^3.3.0",
    "tailwind-merge": "^3.4.0",
    "tailwindcss-animate": "^1.0.7",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "@radix-ui/react-avatar": "^1.1.11",
    "@radix-ui/react-dropdown-menu": "^2.1.16",
    "@radix-ui/react-progress": "^1.1.8",
    "@radix-ui/react-separator": "^1.1.8",
    "@radix-ui/react-slot": "^1.2.4",
    "@radix-ui/react-tooltip": "^1.2.8",
    "lucide-react": "^0.562.0"
  }
}
```

---

## Design Principles

1. **CSS Variable-Driven**: All colors use HSL CSS variables for easy theming
2. **Dark-First**: Optimized for dark theme (no light mode)
3. **Violet Branding**: Primary violet (`#8b5cf6`) as the brand accent
4. **Status Colors**: Semantic colors for different states (success, warning, error)
5. **Glassmorphism**: Semi-transparent cards with backdrop blur
6. **Glow Effects**: Subtle violet glow on interactive elements
7. **Consistent Focus States**: Ring-based focus indicators
8. **Smooth Animations**: Subtle transitions (150-300ms)
9. **Minimal Border Radius**: 8px default, rounded-full for badges

---

## Quick Start for New Project

1. Install dependencies:
```bash
npm install tailwindcss postcss autoprefixer tailwind-merge tailwindcss-animate class-variance-authority clsx lucide-react
npm install @radix-ui/react-avatar @radix-ui/react-dropdown-menu @radix-ui/react-progress @radix-ui/react-separator @radix-ui/react-slot
```

2. Copy the CSS variables to your `globals.css`
3. Copy the `tailwind.config.js` configuration
4. Add the `cn()` utility function
5. Import Google Fonts (Inter + Orbitron)
6. Set `className="dark"` on your `<html>` element
