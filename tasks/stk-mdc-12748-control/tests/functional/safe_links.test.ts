import { describe, expect, it } from 'vitest'
import { parseMarkdown } from '../support/parser'
import { hrefValues, renderBody, srcValues } from '../support/render'

describe('ordinary document links and images', () => {
  it('keeps absolute, relative and root-relative links', async () => {
    const md = [
      '[external](https://example.com/some/page)',
      '[relative](../guide/page.md)',
      '[root](/getting-started)',
      '[anchor](#section)',
    ].join('\n\n')
    const { body } = await parseMarkdown(md)
    const html = await renderBody(body)
    const links = hrefValues(html)
    expect(links).toContain('https://example.com/some/page')
    expect(links).toContain('../guide/page.md')
    expect(links).toContain('/getting-started')
    expect(links).toContain('#section')
  })

  it('keeps inline raster image sources', async () => {
    const { body } = await parseMarkdown('![pixel](data:image/png;base64,iVBORw0KGgoAAAANSUhEUg==)')
    const html = await renderBody(body)
    expect(srcValues(html)).toContain('data:image/png;base64,iVBORw0KGgoAAAANSUhEUg==')
  })

  it('keeps ordinary image sources', async () => {
    const { body } = await parseMarkdown('![picture](/images/picture.png)')
    const html = await renderBody(body)
    expect(srcValues(html)).toContain('/images/picture.png')
  })
})
