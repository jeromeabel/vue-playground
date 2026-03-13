# Vue Playground

Vue Playground is a small Vue application used to turn technical blog posts into runnable, isolated examples. 

## Scripts

- `pnpm dev` starts the Vite dev server.
- `pnpm build` runs the TypeScript build check and creates the production bundle.
- `pnpm preview` serves the built app locally.
- `pnpm typecheck` runs `vue-tsc` against the application sources.
- `pnpm lint` checks the project with ESLint.
- `pnpm lint:fix` applies safe ESLint fixes.
- `pnpm test` starts Vitest in watch mode.
- `pnpm test:run` runs the test suite once.

## Project Layout

- `src/router` contains the Vue Router bootstrap.
- `src/components` contains shared UI pieces such as the app header.
- `src/pages` contains route-level pages.
- `src/style.css` defines the Tailwind entrypoint and global design tokens.

## Next Milestones

1. Add the GBIF-powered species explorer pages.
2. Add benchmark routes for large-table rendering experiments.
3. Add chunk-error handling and version-banner infrastructure.
