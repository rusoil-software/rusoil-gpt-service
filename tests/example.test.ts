// Minimal Jest + TypeScript test template
// Purpose: copy this into new frontend/backend TS tests. Keep tests fast and focused.

import { describe, test, expect } from '@jest/globals';

describe('example suite', () => {
  test('happy path', () => {
    expect(1 + 2).toBe(3);
  });

  test('edge case', () => {
    expect(Number('')).toBe(0);
  });
});
