import { describe, expect, it } from 'vitest';
import { upsertEnvVar } from '../../src/scripts/env-file.js';

describe('upsertEnvVar', () => {
  it('appends a new key on an empty file', () => {
    expect(upsertEnvVar('', 'GMAIL_REFRESH_TOKEN', 'abc123')).toBe('GMAIL_REFRESH_TOKEN=abc123\n');
  });

  it('appends a new key after existing content, adding a trailing newline first if missing', () => {
    const result = upsertEnvVar('CRM_PORT=4820', 'GMAIL_REFRESH_TOKEN', 'abc123');
    expect(result).toBe('CRM_PORT=4820\nGMAIL_REFRESH_TOKEN=abc123\n');
  });

  it('replaces an existing key in place rather than duplicating it', () => {
    const before = 'CRM_PORT=4820\nGMAIL_REFRESH_TOKEN=old-token\nCRM_LOG_LEVEL=info\n';
    const after = upsertEnvVar(before, 'GMAIL_REFRESH_TOKEN', 'new-token');
    expect(after).toBe('CRM_PORT=4820\nGMAIL_REFRESH_TOKEN=new-token\nCRM_LOG_LEVEL=info\n');
  });

  it('does not corrupt other keys that share a prefix', () => {
    const before = 'GMAIL_FROM=old@example.com\nGMAIL_FROM_DISPLAY=Old Name\n';
    const after = upsertEnvVar(before, 'GMAIL_FROM', 'new@example.com');
    expect(after).toContain('GMAIL_FROM=new@example.com');
    expect(after).toContain('GMAIL_FROM_DISPLAY=Old Name');
  });
});
