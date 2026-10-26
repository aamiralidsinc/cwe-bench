import { describe, expect, it } from 'vitest'
import { parseMarkdown } from '../support/parser'
import { hrefValues, renderBody, srcValues, unsafe } from '../support/render'

describe('inline-document URL targets', () => {
  it('drops an inline-document target from a link', async () => {
    const { body } = await parseMarkdown('<a href="data:text/html,<script>marker()</script>">open</a>')
    const html = await renderBody(body)
    expect(unsafe(hrefValues(html))).toEqual([])
  })

  it('drops an inline-document target from an embedded frame', async () => {
    const { body } = await parseMarkdown('<iframe src="data:text/html,<script>marker()</script>"></iframe>')
    const html = await renderBody(body)
    expect(unsafe(srcValues(html))).toEqual([])
  })

  it('drops an inline-document image source built from markdown syntax', async () => {
    const { body } = await parseMarkdown('![x](data:text/html;base64,PHNjcmlwdD5tYXJrZXIoKTwvc2NyaXB0Pg==)')
    const html = await renderBody(body)
    expect(unsafe(srcValues(html))).toEqual([])
  })

  it('drops an inline-document link target built from markdown syntax', async () => {
    const { body } = await parseMarkdown('[x](data:text/html;base64,PHNjcmlwdD5tYXJrZXIoKTwvc2NyaXB0Pg==)')
    const html = await renderBody(body)
    expect(unsafe(hrefValues(html))).toEqual([])
  })
})
