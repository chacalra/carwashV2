/**
 * Servidor MSW para Node (Vitest).
 * Cada test puede sobrescribir handlers con `server.use(...)`.
 */

import { setupServer } from "msw/node";
import { handlers } from "./handlers";

export const server = setupServer(...handlers);
