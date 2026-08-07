# Prompt 1 --- Project Initialization & Folder Structure

We are starting a brand-new production-grade project.

Do **NOT** build any pages yet.

This prompt is **ONLY** for creating the project foundation.

I have placed these files inside the project root.

-   `PROJECT_GUIDELINES.md`
-   `README.md`
-   `UI_GUIDELINE.md`

You **MUST** read these documents before generating anything.

## Priority Order

1.  UI_GUIDELINE.md (Highest Priority)
2.  PROJECT_GUIDELINES.md
3.  README.md

If there is any conflict, always follow **UI_GUIDELINE.md**.

------------------------------------------------------------------------

## Project Structure

Create a clean monorepo structure.

``` text
/
├── frontend/
└── backend/
```

Backend will be developed later.

Do **NOT** generate backend code.

Only create an empty `backend` folder with a `README.md` containing:

> Backend will be implemented later using Python FastAPI.

------------------------------------------------------------------------

## Frontend Initialization

Inside `frontend`, initialize a modern React application using:

-   React
-   JavaScript
-   Vite

Install and configure:

-   Tailwind CSS
-   React Router
-   Zustand
-   React Query
-   Framer Motion
-   Recharts
-   Lucide React
-   shadcn/ui

Configure all dependencies properly.

------------------------------------------------------------------------

## Folder Architecture

``` text
frontend/
└── src/
    ├── app/
    ├── layouts/
    ├── pages/
    ├── components/
    │   ├── ui/
    │   ├── common/
    │   ├── dashboard/
    │   ├── cards/
    │   ├── charts/
    │   ├── forms/
    │   ├── navigation/
    │   ├── profile/
    │   ├── finance/
    │   ├── investments/
    │   ├── advisor/
    │   └── reports/
    ├── hooks/
    ├── store/
    ├── services/
    ├── constants/
    ├── types/
    ├── utils/
    ├── config/
    ├── assets/
    │   ├── icons/
    │   ├── images/
    │   └── fonts/
    ├── styles/
    ├── routes/
    ├── mock/
    ├── contexts/
    ├── providers/
    └── lib/
```

Create proper barrel exports wherever appropriate.

Avoid deeply nested imports.

------------------------------------------------------------------------

## Path Aliases

Configure JavaScript (JSX) and Vite aliases:

-   @
-   @components
-   @pages
-   @hooks
-   @store
-   @utils
-   @types
-   @assets

------------------------------------------------------------------------

## Development Tooling

Set up:

-   ESLint
-   Prettier
-   EditorConfig
-   Husky
-   lint-staged

------------------------------------------------------------------------

## Tailwind & Theme

Configure Tailwind.

Create a global theme file.

Do **NOT** use random colors.

Use design tokens only.

Create:

-   Global CSS
-   Typography system
-   Spacing system
-   Shadow tokens
-   Radius tokens
-   Animation tokens
-   Color variables

Do **NOT** implement actual UI yet.

------------------------------------------------------------------------

## Routing

Set up React Router with placeholder routes:

-   /
-   /dashboard
-   /profile
-   /finance
-   /investments
-   /ai-advisor
-   /reports
-   /settings

Each page should only display:

> Coming Soon

------------------------------------------------------------------------

## Root Layout

Create a root layout containing:

-   Header placeholder
-   Sidebar placeholder
-   Main content
-   Responsive layout

------------------------------------------------------------------------

## Constraints

-   Application should compile successfully.
-   No UI implementation.
-   No business logic.
-   No mock data.
-   No dashboard.
-   No cards.
-   No charts.

Only create the project foundation.

------------------------------------------------------------------------

## Final Output

At the end, provide:

-   Created folders
-   Installed packages
-   Architecture decisions
-   Files created
-   Recommendations before moving to Prompt 2

Wait for my approval before continuing.
