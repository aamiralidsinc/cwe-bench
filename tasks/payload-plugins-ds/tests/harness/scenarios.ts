import { buildWorld } from './world.ts'

/** The common two-collection world used by the reporting paths. */
export function healthWorld(
  options: { failFind?: string[]; mediaRead?: any; secretRead?: any } = {},
) {
  return buildWorld({
    collections: [
      {
        slug: 'media',
        access: { read: options.mediaRead ?? (() => true), update: () => true },
      },
      {
        slug: 'secret',
        access: {
          read: options.secretRead ?? (({ req }: any) => req.user?.role === 'admin'),
          update: () => false,
        },
      },
    ],
    docs: {
      media: [
        { alt: 'A cat on a mat', filename: 'cat.png', id: 'm1', mimeType: 'image/png' },
        { alt: '', filename: 'dog.png', id: 'm2', mimeType: 'image/png' },
      ],
      secret: [
        { alt: 'SECRET-ALT-ONE', filename: 'secret-1.png', id: 's1', mimeType: 'image/png' },
        { alt: '', filename: 'secret-2.png', id: 's2', mimeType: 'image/png' },
      ],
    },
    failFind: options.failFind,
  })
}
