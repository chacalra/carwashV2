/**
 * Setup global de Vitest.
 * - Carga matchers de @testing-library/jest-dom (toBeInTheDocument, etc.).
 * - Arranca el servidor MSW para interceptar fetch en todos los tests.
 * - Reset de handlers entre tests.
 */

import "@testing-library/jest-dom/vitest";
import { afterAll, afterEach, beforeAll } from "vitest";
import { server } from "./mocks/server";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
