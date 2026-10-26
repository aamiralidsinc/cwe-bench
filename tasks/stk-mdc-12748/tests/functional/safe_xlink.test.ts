import { describe, expect, it } from 'vitest'
import { parseMarkdown } from '../support/parser'
import { renderBody, xlinkHrefValues } from '../support/render'

describe('SVG sprite references', () => {
  it('keeps an absolute SVG link target', async () => {
    const { body } = await parseMarkdown('<svg><a xlink:href="https://example.com/sprite.svg#icon">icon</a></svg>')
    const html = await renderBody(body)
    expect(xlinkHrefValues(html)).toContain('https://example.com/sprite.svg#icon')
  })

  it('keeps a relative SVG link target', async () => {
    const { body } = await parseMarkdown('<svg><a xlink:href="/sprite.svg#icon">icon</a></svg>')
    const html = await renderBody(body)
    expect(xlinkHrefValues(html)).toContain('/sprite.svg#icon')
  })
})
