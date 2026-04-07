import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    globals: true,
    environment: "node",
    setupFiles: ["./tests/setup.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text", "cobertura"],
      reportsDirectory: "coverage",
      include: ["src/**/*.ts"],
    },
  },
});