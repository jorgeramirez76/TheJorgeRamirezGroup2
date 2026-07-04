import { describe, expect, it } from 'vitest';
import { parseAuthCallback, parseRedirectUri } from '../../src/scripts/oauth-callback.js';

describe('parseAuthCallback', () => {
  it('extracts the authorization code from a successful redirect', () => {
    expect(parseAuthCallback('/oauth/google/callback?code=abc123&scope=gmail')).toEqual({ code: 'abc123' });
  });

  it('surfaces an error param from a denied/failed consent screen', () => {
    expect(parseAuthCallback('/oauth/google/callback?error=access_denied')).toEqual({ error: 'access_denied' });
  });

  it('reports missing_code when neither code nor error is present', () => {
    expect(parseAuthCallback('/oauth/google/callback')).toEqual({ error: 'missing_code' });
  });
});

describe('parseRedirectUri', () => {
  it('extracts the loopback port and path', () => {
    expect(parseRedirectUri('http://localhost:4820/oauth/google/callback')).toEqual({ port: 4820, path: '/oauth/google/callback' });
  });

  it('accepts 127.0.0.1 as well as localhost', () => {
    expect(parseRedirectUri('http://127.0.0.1:9000/callback')).toEqual({ port: 9000, path: '/callback' });
  });

  it('rejects a non-loopback redirect URI (the desktop flow requires localhost)', () => {
    expect(() => parseRedirectUri('https://example.com/callback')).toThrow(/loopback/);
  });
});
