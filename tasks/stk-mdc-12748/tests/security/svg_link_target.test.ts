import { describe, expect, it } from 'vitest'
import { parseMarkdown } from '../support/parser'
import { renderBody, unsafe, xlinkHrefValues } from '../support/render'

describe('SVG link targets', () => {
  it('drops an unsafe target from an SVG link', async () => {
    const { body } = await parseMarkdown('<svg viewBox="0 0 10 10"><a xlink:href="javascript:alert(1)">go</a></svg>')
    const html = await renderBody(body)
    expect(unsafe(xlinkHrefValues(html))).toEqual([])
  })

  it('drops an inline-document target from an SVG link', async () => {
    const { body } = await parseMarkdown('<svg><a xlink:href="data:text/html,<script>marker()</script>">go</a></svg>')
    const html = await renderBody(body)
    expect(unsafe(xlinkHrefValues(html))).toEqual([])
  })
})
