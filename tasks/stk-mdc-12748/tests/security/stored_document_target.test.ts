import { describe, expect, it } from 'vitest'
import { hrefValues, renderBody, srcValues, unsafe } from '../support/render'

function documentWith(node: any) {
  return { type: 'root', children: [node] }
}

describe('documents rendered from their parsed form', () => {
  it('drops an unsafe link target', async () => {
    const html = await renderBody(documentWith({
      type: 'element',
      tag: 'a',
      props: { href: 'javascript:alert(1)' },
      children: [{ type: 'text', value: 'go' }],
    }))
    expect(unsafe(hrefValues(html))).toEqual([])
  })

  it('drops an unsafe embedded resource target', async () => {
    const html = await renderBody(documentWith({
      type: 'element',
      tag: 'img',
      props: { src: 'data:text/html,<script>marker()</script>' },
      children: [],
    }))
    expect(unsafe(srcValues(html))).toEqual([])
  })
})
