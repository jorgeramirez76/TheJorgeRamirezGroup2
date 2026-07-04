/** Parses the `code`/`error` query params off the OAuth2 redirect Google sends the desktop flow. */
export function parseAuthCallback(requestUrl: string, base = 'http://localhost'): { code: string } | { error: string } {
  const url = new URL(requestUrl, base);
  const error = url.searchParams.get('error');
  if (error) return { error };
  const code = url.searchParams.get('code');
  if (!code) return { error: 'missing_code' };
  return { code };
}

/** `GOOGLE_REDIRECT_URI` must be a loopback URL for the desktop flow — extracts the port + path to listen on. */
export function parseRedirectUri(redirectUri: string): { port: number; path: string } {
  const url = new URL(redirectUri);
  if (url.hostname !== 'localhost' && url.hostname !== '127.0.0.1') {
    throw new Error(`GOOGLE_REDIRECT_URI must be a loopback address for the desktop OAuth flow, got: ${redirectUri}`);
  }
  const port = Number(url.port || 80);
  return { port, path: url.pathname };
}
