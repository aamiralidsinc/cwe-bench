// The adapters import media types from `tinacms`. The helpers are only needed
// if a test imports the client media stores (it does not), but they keep the
// stub faithful.

export const DEFAULT_MEDIA_UPLOAD_TYPES: string[] = [];

export function sanitizeFilename(name: string): string {
  return String(name).replace(/[^a-zA-Z0-9._-]/g, '-');
}
