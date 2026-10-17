/**
 * Access tokens live in memory only (never localStorage) — reduces the
 * XSS blast radius, since a short-lived access token isn't sitting in
 * storage for a malicious script to read. The refresh token IS kept in
 * localStorage (see authService.js) so a session can survive a page
 * reload — a reasonable middle ground given the backend issues both
 * tokens as JSON rather than httpOnly cookies.
 */
let accessToken = null;
const listeners = new Set();

export function getAccessToken() {
  return accessToken;
}

export function setAccessToken(token) {
  accessToken = token;
  listeners.forEach((fn) => fn(token));
}

export function onAccessTokenChange(fn) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}
