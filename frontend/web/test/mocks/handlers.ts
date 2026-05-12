/**
 * Handlers MSW por defecto (vacíos).
 * Cada test agrega los suyos via `server.use(...)`.
 *
 * Base URL = lo que el cliente apunta en dev: http://localhost:8000.
 */

import type { HttpHandler } from "msw";

export const API_BASE = "http://localhost:8000";

export const handlers: HttpHandler[] = [];
