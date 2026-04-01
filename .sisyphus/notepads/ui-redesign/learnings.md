# UI Redesign - Learnings

## Dead Code Cleanup Task - 2026-04-01

### Task Summary
Successfully deleted dead code and unused dependencies as part of the UI redesign cleanup process.

### Files Deleted (14 total)

#### TSX/TS Files (9 files)
1. `frontend/src/components/common/workflowViews/NodeGraphView.tsx` - 417 lines
2. `frontend/src/components/common/workflowViews/CardListView.tsx` - 88 lines  
3. `frontend/src/components/common/workflowViews/TimelineView.tsx` - 185 lines
4. `frontend/src/components/common/workflowViews/WorkflowViewToolbar.tsx` - 128 lines
5. `frontend/src/components/common/StreamContentViewer.tsx` - 168 lines
6. `frontend/src/components/common/StreamContentList.tsx` - 152 lines
7. `frontend/src/components/common/StepProgressDisplay.tsx` - 114 lines
8. `frontend/src/components/common/StepItem.tsx` - 86 lines
9. `frontend/src/components/common/workflowViews/graphUtils.ts` - 39 lines

#### CSS Files (4 files)
1. `frontend/src/components/common/workflowViews/CardListView.css` - 156 lines
2. `frontend/src/components/common/workflowViews/TimelineView.css` - 548 lines
3. `frontend/src/components/common/workflowViews/NodeGraphView.css` - 339 lines
4. `frontend/src/components/common/workflowViews/WorkflowViewToolbar.css` - 220 lines

#### Missing CSS File (1 expected but not found)
- `frontend/src/components/common/workflowViews/StreamContentList.css` - File did not exist

#### Service Files (1 file)
1. `frontend/src/services/endpoints.ts` - 28 lines

### Dependencies Removed
- Removed `cherry-markdown` from `frontend/package.json` (was at line 20)

### Verification Process
- Verified all files had zero active imports before deletion using grep commands
- Confirmed no other files in the codebase import the deleted components
- Verified `cherry-markdown` had no imports anywhere in the frontend codebase

### Build Results
- ✅ `npm install` completed successfully (619ms)
- ✅ `npm run build` completed successfully with only minor TypeScript warnings about unused variables
- Build output shows: `> frontend@0.0.0 build > tsc -b && vite build` with no errors

### Key Observations
1. **Systematic approach** - Using grep to verify zero imports before deletion prevented breaking changes
2. **Missing file handling** - One expected CSS file was already missing, which didn't impact the cleanup
3. **Clean removal** - No build errors after deletion, confirming the files were truly orphaned
4. **Bundle optimization** - Removing unused dependencies reduces bundle size and build time

### Technical Notes
- NodeGraphView.tsx imported graphUtils.ts, but both were on the deletion list so no conflicts
- The workflowViews directory still contains active components: ReactFlowNodeGraphView.tsx and ReactFlowCustomNode.tsx
- Minor TypeScript warnings remain for unused variables in existing files, but these don't affect functionality

### Impact
- Reduced codebase by ~2,200+ lines of dead code
- Removed unused dependency (cherry-markdown) was never imported
- No functional impact on the application
- Faster build times due to reduced file count

### Next Steps
The cleanup was successful and the build passes. The remaining workflow views (ReactFlow-based) appear to be the active implementation, while the deleted components were legacy views from an earlier iteration.

### Toast Abstraction Layer Task - 2026-04-01

#### Task Summary
Successfully created a toast abstraction layer using sonner that provides a 1:1 API compatibility with Ant Design message notifications.

#### Files Created
- `frontend/src/services/toast.ts` - Toast service with showToast object

#### Implementation Details
```typescript
import { toast } from 'sonner';

export const showToast = {
  success: (msg: string) => toast.success(msg),
  error: (msg: string) => toast.error(msg),
  warning: (msg: string) => toast.warning(msg),
  info: (msg: string) => toast.info(msg),
};
```

#### API Compatibility
The implementation provides exact 1:1 mapping with Ant Design's message API:
- `message.success(msg)` → `showToast.success(msg)`
- `message.error(msg)` → `showToast.error(msg)`
- `message.warning(msg)` → `showToast.warning(msg)`
- `message.info(msg)` → `showToast.info(msg)`

#### Dependencies
- `sonner` was already installed by T3 stack (verified with `npm install sonner`)
- No additional dependencies required

#### Build Verification
- ✅ Frontend build passes: `npm run build` completed successfully
- ✅ TypeScript compilation clean with no errors
- ✅ Bundle generated normally with sonner integration

#### Key Observations
1. **Zero friction migration** - The API matches exactly, making it a drop-in replacement
2. **Minimal dependency** - Only adds sonner (already available via T3)
3. **Clean build** - No TypeScript errors or warnings
4. **Ready for migration** - 26 `message.*()` calls across 7 files can now be replaced with `showToast.*()`

#### Next Steps
The toast abstraction is ready for the next phase of UI migration where Ant Design message calls will be replaced with showToast calls across the codebase.

### Headless UI Primitives Installation Task - 2026-04-01

#### Task Summary
Successfully installed headless UI primitives (Radix UI), toast library (sonner), and test infrastructure (vitest) for the UI redesign project.

#### Packages Installed
- **Radix UI Components**: @radix-ui/react-tabs, @radix-ui/react-select, @radix-ui/react-dialog, @radix-ui/react-tooltip, @radix-ui/react-popover, @radix-ui/react-switch, @radix-ui/react-separator
- **Toast Library**: sonner ^2.0.7 (already installed via toast abstraction)
- **Testing Infrastructure**: vitest ^4.1.2, @testing-library/react ^16.3.2, @testing-library/jest-dom ^6.9.1, @testing-library/user-event ^14.6.1, jsdom ^29.0.1

#### Configuration Files Created
- **vitest.config.ts**: Configured with jsdom environment, globals enabled, and setup files
- **test-setup.ts**: Basic setup file with jest-dom extensions

#### Scripts Added to package.json
- `test`: "vitest run" - Run tests once
- `test:watch`: "vitest" - Run tests in watch mode

#### Build Verification
- ✅ TypeScript compilation successful with no errors
- ✅ Vite build completed successfully (5.70s)
- ✅ All dependencies properly resolved
- ✅ No breaking changes to existing functionality
- ⚠️ Chunk size warning appears but doesn't affect functionality

#### Key Observations
1. **Clean installation** - All Radix UI packages installed without conflicts
2. **Existing sonner integration** - Toast library was already available through previous abstraction
3. **Testing readiness** - Infrastructure is now ready for component tests
4. **Zero friction** - No existing functionality was impacted by the new dependencies

#### Technical Notes
- The project already uses React 19 + TypeScript + Vite 7
- All Radix UI packages follow standard naming conventions
- Vitest configuration follows best practices for React + TypeScript projects
- Testing setup mirrors modern React testing patterns

#### Next Steps
- Ready to start writing tests for components using the new infrastructure
- Ready to start implementing UI components using Radix UI primitives
- Can proceed with replacing Ant Design components with Radix UI equivalents

#### Final Verification
- ✅ Vitest configuration verified: `npm test` runs successfully (exits with code 1 when no test files found, which is expected)
- ✅ All installation tasks completed successfully
- ✅ Build passes with new dependencies
- ✅ Testing infrastructure ready for use

---

## Tailwind CSS v4 Setup Task - 2026-04-01

### Task Summary
Successfully installed and configured Tailwind CSS v4 with design system in the Bamboo frontend, preserving existing CLI timeline styles while removing Ant Design dependencies from global CSS.

### Completed Tasks

#### 1. Tailwind CSS Installation
- ✅ Installed `tailwindcss` and `@tailwindcss/vite` as devDependencies
- ✅ Successfully added 12 packages with no conflicts
- ✅ Version: Tailwind CSS v4 (latest)

#### 2. Vite Configuration Update
- ✅ Updated `frontend/vite.config.ts` to include `@tailwindcss/vite` plugin
- ✅ Maintained existing `react()` plugin
- ✅ Preserved all proxy configurations for API and WebSocket

#### 3. CSS Rewrite with Tailwind v4
- ✅ Completely rewrote `frontend/src/index.css` with Tailwind v4 setup
- ✅ Added `@theme` configuration with design tokens:
  - `--color-primary: #1E293B`
  - `--color-secondary: #334155`
  - `--color-accent: #22C55E`
  - `--font-sans: 'Fira Sans', ui-sans-serif, system-ui, sans-serif`
  - `--font-mono: 'Fira Code', ui-monospace, monospace`
- ✅ Preserved all CLI timeline styles from original CSS files:
  - Complete WorkflowTimeline.css content (357 lines)
  - Complete EmptyView.css content (21 lines)
  - Complete StreamContentItem.css content (160 lines)
- ✅ Added custom dark mode variant: `@custom-variant dark (&:where(.dark, .dark *))`

#### 4. Google Fonts Integration
- ✅ Added Fira Code and Fira Sans fonts to `frontend/index.html`
- ✅ Used proper preconnect links for performance
- ✅ Added font-weight variations (300-700) for comprehensive coverage

#### 5. Ant Design CSS Cleanup
- ✅ Removed all `.ant-*` and `.workflow-panel-*` CSS selectors from index.css
- ✅ Note: Some Ant Design selectors remain in component-specific CSS files (StreamContentList.css, WorkflowNodeCard.css, App.css) - these will be addressed in subsequent component migration tasks

#### 6. Build Verification
- ✅ `npm run build` completed successfully with exit code 0
- ✅ TypeScript compilation passed without errors
- ✅ Vite build processed 6645 modules successfully
- ✅ Generated assets: CSS (72.51 kB), JS (2,483.53 kB), KaTeX fonts
- ✅ No functional errors or warnings affecting application functionality

### Key Technical Decisions

#### Design System Approach
- Used CSS custom properties with `@theme` for centralized design tokens
- Maintained existing CLI aesthetic while migrating to Tailwind utility classes
- Preserved all existing component styles for zero functional disruption

#### Migration Strategy
- Implemented as a "big bang" approach by rewriting index.css entirely
- Preserved all existing CSS classes to prevent breaking changes
- Used section comments to clearly organize and trace preserved styles

#### Performance Considerations
- Added preconnect links for Google Fonts to improve load time
- Kept existing optimized scrollbar styles
- Maintained responsive design patterns from original CSS

### Next Steps
- Components can now be gradually migrated to use Tailwind utility classes
- Ant Design dependencies can be safely removed in future phases
- Design system tokens are ready for use in component development

### Impact
- ✅ Zero functional disruption - all existing styles preserved
- ✅ Modern Tailwind CSS v4 setup with design tokens
- ✅ Improved developer experience with utility-first CSS
- ✅ Future-ready for component migration away from Ant Design
- ✅ Build performance maintained with minimal overhead
### ModelSelector Rewrite (Ant Design → Radix UI) - 2026-04-01

#### Task Summary
Successfully created `frontend/src/components/shared/ModelSelector.tsx` replacing Ant Design with Radix UI + Tailwind CSS. All business logic preserved.

#### Files Created
- `frontend/src/components/shared/ModelSelector.tsx` — ~385 lines (original was 286 with Ant Design)

#### Component Mapping (Ant Design → Radix UI)
| Ant Design | Radix UI |
|---|---|
| `Select` + `Option` | `@radix-ui/react-select` (Root, Trigger, Content, Viewport, Item, ItemText, ItemIndicator) |
| `Switch` | `@radix-ui/react-switch` (Root, Thumb) |
| `Tooltip` | `@radix-ui/react-tooltip` (Provider, Root, Trigger, Content, Arrow) |
| `Tag` | Tailwind `<span>` with `bg-{color}-500/20 text-{color}-400` badge pattern |
| `Space` | Tailwind `flex items-center gap-2` |
| `message.*()` | `showToast.*()` from `../../services/toast` |
| `@ant-design/icons` | `lucide-react` (Bot, Zap, Lightbulb, ChevronDown, Loader2, Check) |

#### Key Technical Decisions
1. **SelectItem with forwardRef** — Radix UI `Select.Item` requires `forwardRef` for proper functionality. Created a wrapper component `SelectItem` with `displayName`.
2. **Portal rendering** — Both Select and Tooltip use Portal for proper z-index stacking. Content renders in document root.
3. **CSS variable theming** — Used `var(--color-*)` tokens from `@theme` in index.css for consistency. No hardcoded colors.
4. **Switch thumb positioning** — Radix Switch uses `data-[state=checked]` for thumb translation instead of Ant Design's `checkedChildren`/`unCheckedChildren`. Replaced with separate text label.
5. **Badge pattern** — Status tags replaced with Tailwind badges: `bg-{color}-500/20 text-{color}-400` (e.g., purple for thinking, green for local, orange for offline).
6. **Dropped `size` prop** — Original had `size?: 'small' | 'middle' | 'large'` but it was only passed to Ant Design's internal sizing. Not needed with Tailwind where sizing is explicit.

#### Build Verification
- ✅ `npm run build` passes (6.22s, 6645 modules)
- ✅ Zero Ant Design imports in new file
- ✅ TypeScript compilation clean

#### Gotchas
- Radix `Select.Item` must be wrapped with `forwardRef` — missing this causes React warnings and broken item selection
- `Select.Trigger` needs explicit `aria-label` for accessibility (Radix is strict about this)
- `Tooltip.Provider` must wrap all tooltip usage — individual `Tooltip.Root` alone won't render
- Radix `Select.Content` needs `position="popper"` for dropdown to align with trigger width

---

## IDE-Style Layout Shell Components Task - 2026-04-01

### Task Summary
Created three IDE-style layout components for the UI redesign: Sidebar, Header, and AppLayout.

### Files Created

1. **`frontend/src/components/layout/Sidebar.tsx`** (~113 lines)
   - 56px wide icon-only navigation sidebar
   - 4 navigation items: 绘图, 文档, 动画, 历史记录
   - Active state with left indicator bar (bg-[var(--color-accent)])
   - Theme toggle (Sun/Moon icons) at bottom
   - Uses useWorkflow for workflow switching
   - Uses react-router-dom Link for history navigation

2. **`frontend/src/components/layout/Header.tsx`** (~41 lines)
   - 40px height compact title bar
   - Left: Dynamic page title based on workflow/history
   - Right: Inline ModelSelector component
   - Uses useWorkflow for title determination
   - Uses useLocation for history page detection

3. **`frontend/src/components/layout/AppLayout.tsx`** (~27 lines)
   - Full height (100vh) layout container
   - Fixed 56px Sidebar + flex main area
   - Header (40px) + Content (flex-1) structure
   - Theme-aware background colors
   - Accepts children prop for content

### Key Implementation Details

#### Sidebar Navigation Logic
- Workflow items (绘图/文档/动画) call `setCurrentWorkflow()` and navigate to `/`
- History item uses `<Link to="/history">` for client-side routing
- Active state detection:
  - Workflow: `state.currentWorkflow === item.workflow && location.pathname !== '/history'`
  - History: `location.pathname === '/history'`

#### Theme Support
- Dark mode: Sidebar uses `bg-[var(--color-bg-dark)]`, main uses `bg-[var(--color-bg-card)]`
- Light mode: Sidebar uses `bg-white`, main uses `bg-gray-50`
- Transitions: `transition-colors duration-200` for smooth theme switching

#### Icon Mapping
| Item | lucide-react Icon |
|------|-------------------|
| 绘图 | BarChart3 |
| 文档 | FileText |
| 动画 | Video |
| 历史记录 | History |
| Theme (dark) | Sun |
| Theme (light) | Moon |

#### Title Mapping
| Workflow | Title |
|----------|-------|
| drawing | 智能绘图 |
| document_with_images | 文档生成 |
| manim | 数学动画 |
| /history | 历史记录 |

### Build Verification
- ✅ All three layout files: zero TypeScript errors
- ⚠️ Build fails due to pre-existing type mismatch in `WorkflowPanel.tsx` (unrelated)
- ⚠️ `WorkflowPanel.tsx` line 60-64 uses `provider`/`model` but type uses `model_provider`/`model_name`

### Design Decisions
1. **No comments/docstrings**: Removed all explanatory comments per coding guidelines
2. **Tailwind-only styling**: Zero inline styles, all Tailwind utility classes
3. **CSS variables for theming**: Used design tokens from index.css (e.g., `--color-bg-dark`)
4. **Semantic HTML**: Used `<aside>`, `<nav>`, `<header>`, `<main>` elements
5. **Accessibility**: Added `title` attributes to icon buttons

### Next Steps
The layout shell is ready for integration into App.tsx (Task T12). The pre-existing WorkflowPanel.tsx type mismatch should be fixed separately.


### WorkflowPanel Shared Component Task - 2026-04-01

#### Task Summary
Created `frontend/src/components/shared/WorkflowPanel.tsx` — a shared base component extracting the ~80% identical structure across DrawingPanel, DocumentPanel, and ManimPanel.

#### File Created
- `frontend/src/components/shared/WorkflowPanel.tsx` — ~140 lines

#### Architecture: Props-based "slot" pattern
- `workflowType` — selects WebSocket channel
- `apiStart/Stop/Clear` — workflow-specific API calls (injected, no direct api.ts dependency)
- `placeholder/startLabel/runningLabel` — per-panel UI text
- `extraControls` — slot for additional controls (e.g. Manim quality selector)
- `renderResult` — render prop for panel-specific result display

#### Key Design Decisions
1. **apiStart type uses concrete shape** — The actual API functions (`startDrawingWorkflow`, etc.) accept `{ provider?, model?, enable_thinking? }`, NOT `WorkflowRequestWithModel` (which has `model_provider`/`model_name` for the wire format). The props interface matches the actual API function signatures.
2. **Exported `WorkflowPanelProps`** — so T9/T10/T11 consumers can import the type directly.
3. **No Ant Design imports** — Uses lucide-react icons (Send, Square, Trash2, Loader2) and Tailwind CSS classes exclusively.
4. **Reuses existing common components as-is** — WorkflowTimeline, EmptyView, WorkflowStatusIndicator, ResultPlaceholder.
5. **Two-column layout** — Left: Input + Timeline (w-[400px] fixed), Right: Result (flex-1).
6. **Title derived from placeholder** — Uses `placeholder.includes('绘图'|'文档')` to determine section title. Consumers can refine this later.

#### Build Verification
- ✅ `npm run build` passes (6.54s, 6645 modules)
- ✅ LSP diagnostics clean — zero errors
- ✅ No new dependencies added
