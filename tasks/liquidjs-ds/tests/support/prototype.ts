/**
 * Shared fixtures for the hidden suites. Nothing here imports product code:
 * the pollution is installed by hand, the arrays are built by hand, and the
 * markers are plain strings.
 */

export const ARRAY_MARKERS = ['__LQ_PROTO_A0__', '__LQ_PROTO_A1__', '__LQ_PROTO_A2__']
export const OBJECT_MARKER = '__LQ_PROTO_OBJ__'
export const FIRST_MARKER = '__LQ_PROTO_FIRST__'
export const LAST_MARKER = '__LQ_PROTO_LAST__'
export const SIZE_MARKER = '__LQ_PROTO_SIZE__'

export const ALL_MARKERS = [...ARRAY_MARKERS, OBJECT_MARKER, FIRST_MARKER, LAST_MARKER, SIZE_MARKER]

/** A sequence with the first `length` slots unset. */
export function sparse (length: number): any[] {
  const arr: any[] = []
  arr.length = length
  return arr
}

/** A sequence whose slots are all supplied. */
export function dense (): string[] {
  return ['own-zero', 'own-one', 'own-two']
}

/**
 * Install prototype values for the duration of `fn` and remove them again.
 * Assertions run after cleanup so the test framework itself is never exposed.
 */
export function withArrayPrototype<T> (fn: () => T): T {
  const proto = Array.prototype as any
  ARRAY_MARKERS.forEach((marker, i) => { proto[i] = marker })
  try {
    return fn()
  } finally {
    for (let i = 0; i < ARRAY_MARKERS.length; i++) delete proto[i]
  }
}

/** Install object prototype values for the duration of `fn`; see above. */
export function withObjectPrototype<T> (fn: () => T): T {
  const proto = Object.prototype as any
  const previous = {
    secret: Object.getOwnPropertyDescriptor(proto, 'secret'),
    first: Object.getOwnPropertyDescriptor(proto, 'first'),
    last: Object.getOwnPropertyDescriptor(proto, 'last'),
    size: Object.getOwnPropertyDescriptor(proto, 'size')
  }
  proto.secret = OBJECT_MARKER
  proto.first = FIRST_MARKER
  proto.last = LAST_MARKER
  proto.size = SIZE_MARKER
  try {
    return fn()
  } finally {
    for (const key of Object.keys(previous) as Array<keyof typeof previous>) {
      const descriptor = previous[key]
      if (descriptor) Object.defineProperty(proto, key, descriptor)
      else delete proto[key]
    }
  }
}

/** Assert that none of the prototype values reached the rendered output. */
export function expectNoMarkers (out: unknown, markers: string[] = ALL_MARKERS) {
  const text = String(out)
  for (const marker of markers) {
    expect(text).not.toContain(marker)
  }
}
