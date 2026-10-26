import { describe, expect, it } from 'vitest'
import { h } from 'vue'
import { parseMarkdown } from '../support/parser'
import { hrefValues, renderBody } from '../support/render'

describe('binding syntax', () => {
  it('keeps a bound link target carrying an allowed value', async () => {
    const { body } = await parseMarkdown('<a :href="https://example.com/ok">go</a>')
    const html = await renderBody(body)
    expect(hrefValues(html)).toContain('https://example.com/ok')
  })

  it('keeps component props given through binding syntax', async () => {
    const { body } = await parseMarkdown('::::button{:to="$doc.snippet.link" appearance="primary"}\nText\n::::')
    const Button = {
      props: ['to', 'appearance'],
      render(this: any) {
        return h('button', { 'data-to': this.to, 'data-appearance': this.appearance }, 'Text')
      },
    }
    const html = await renderBody(body, { components: { button: Button } })
    expect(html).toContain('data-to="$doc.snippet.link"')
    expect(html).toContain('data-appearance="primary"')
  })
})
