import { describe, expect, it } from 'vitest'
import { hrefValues, renderBody, srcValues } from '../support/render'

function documentWith(nodes: any[]) {
  return { type: 'root', children: nodes }
}

describe('documents rendered from their parsed form', () => {
  it('keeps an allowed link target', async () => {
    const html = await renderBody(documentWith([{
      type: 'element',
      tag: 'a',
      props: { href: 'https://example.com/article' },
      children: [{ type: 'text', value: 'read' }],
    }]))
    expect(hrefValues(html)).toContain('https://example.com/article')
  })

  it('keeps an allowed inline image source', async () => {
    const html = await renderBody(documentWith([{
      type: 'element',
      tag: 'img',
      props: { src: 'data:image/gif;base64,R0lGODlhAQABAAAAACw=' },
      children: [],
    }]))
    expect(srcValues(html)).toContain('data:image/gif;base64,R0lGODlhAQABAAAAACw=')
  })

  it('keeps unrelated attributes', async () => {
    const html = await renderBody(documentWith([{
      type: 'element',
      tag: 'a',
      props: { href: '/local', class: 'styled', title: 'A link' },
      children: [{ type: 'text', value: 'local' }],
    }]))
    expect(html).toContain('class="styled"')
    expect(html).toContain('title="A link"')
  })
})
