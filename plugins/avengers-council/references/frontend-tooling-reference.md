# Frontend Tooling & Patterns Reference — Read on demand when relevant

## When to use

Read this reference when the review involves React components, design systems, Next.js/SSR patterns, accessibility, or frontend performance. Detects installed frontend skills (ui-ux-pro-max, vercel-react-best-practices, frontend-design, next-best-practices) to leverage deeper analysis. Skip for backend, infra, or non-UI reviews.

## Frontend Deep Dive (Enhanced Mode)

**Check for specialized frontend tooling:**

```bash
# Check for ui-ux-pro-max skill
ls ~/.claude/skills/ui-ux-pro-max/SKILL.md 2>/dev/null >/dev/null && echo "✓ ui-ux-pro-max available"

# Check for vercel-react-best-practices skill
ls ~/.claude/skills/vercel-react-best-practices/SKILL.md 2>/dev/null >/dev/null && echo "✓ Vercel patterns available"

# Check for frontend-design skill
ls ~/.claude/skills/frontend-design/SKILL.md 2>/dev/null >/dev/null && echo "✓ Frontend design patterns available"

# Check for next-best-practices skill
ls ~/.claude/skills/next-best-practices/SKILL.md 2>/dev/null >/dev/null && echo "✓ Next.js best practices available"
```

## If ui-ux-pro-max IS available:

**Reference design system patterns:**
- **50 design styles**: glassmorphism, claymorphism, minimalism, brutalism, neumorphism, bento grid, dark mode, skeuomorphism, flat design
- **21 color palettes**: Pre-defined harmonious color schemes
- **50 font pairings**: Typography combinations for different aesthetics
- **shadcn/ui integration**: Component library with MCP server access

**Example finding format:**
```
❌ MEDIUM: Component uses hardcoded colors instead of design tokens
Recommendation: Use ui-ux-pro-max palette system or shadcn/ui theme for consistency
Reference: Design systems best practices - token-based theming
```

**Design patterns to cite:**
- Bento grid for dashboard layouts
- Glassmorphism for card/modal aesthetics
- Dark mode implementation with CSS custom properties
- Responsive typography with clamp() functions

## If vercel-react-best-practices IS available:

**Reference React optimization patterns:**

**Server vs Client Components:**
- Flag client components that could be server components
- Check RSC boundaries (async server components, client interactivity)
- Validate data fetching at component level (fetch in RSC, not useEffect)

**Composition patterns:**
- Detect boolean prop proliferation (>3 boolean props -> suggest compound components)
- Reference composition over configuration
- Cite render props or children patterns

**Performance patterns:**
- Bundle optimization (dynamic imports, route-based splitting)
- Image optimization (next/image with proper sizing)
- Font optimization (next/font with subset loading)

**Example finding format:**
```
⚠️ MEDIUM: Component has 6 boolean props (isLoading, isError, isDisabled, etc.)
Recommendation: Use compound component pattern per vercel-composition-patterns
Reference: React composition patterns that scale
```

## If next-best-practices IS available:

**Reference Next.js-specific patterns:**

**File Conventions:**
- App Router: `app/` directory structure, page.tsx, layout.tsx, loading.tsx, error.tsx
- Server Components: async by default, fetch at component level
- Client Components: 'use client' directive for interactivity
- Route handlers: route.ts for API endpoints

**RSC Boundaries:**
- Flag client components that could be server components
- Check for 'use client' placed too high in tree (entire subtree becomes client)
- Validate async server components (don't wrap in useEffect)

**Data Fetching Patterns:**
- Server: fetch with cache controls, revalidation
- Client: SWR or React Query for client data fetching
- Streaming: Suspense boundaries with loading.tsx

**Performance Optimization:**
- Image optimization: next/image with proper width/height
- Font optimization: next/font with display=swap
- Script optimization: next/script with strategy
- Metadata API: generateMetadata for SEO

**Example finding:**
```
⚠️ MEDIUM: Client component could be server component (ProductCard.tsx)
Issue: Component marked 'use client' but has no interactivity
Recommendation: Remove 'use client' directive, make it a server component
Impact: Reduce bundle size, improve initial page load
Reference: next-best-practices - RSC boundaries
```

## If frontend-design IS available:

**Reference creative design patterns:**
- Algorithmic art for data visualization
- Canvas-based interactive elements
- Distinctive design avoiding generic AI aesthetics

## If NO frontend tools available (Fallback):

**Use built-in React/UX knowledge:**

**Core patterns to check:**
- React composition (avoid prop drilling, use composition)
- Accessibility (WCAG 2.1 AA minimum)
- Performance (memoization, code splitting, lazy loading)
- State management (local > context > external store)
- Responsive design (mobile-first, breakpoints)

**Common issues to flag:**
- Missing accessibility (ARIA, keyboard navigation, focus management)
- Performance anti-patterns (inline functions in render, missing keys)
- Security concerns with innerHTML usage
- Layout shifts (missing dimensions, dynamic content)
