import { describe, expect, it } from 'vitest'
import { parseMarkdown } from '../support/parser'
import { hrefValues, renderBody, unsafe } from '../support/render'

describe('bound URL targets', () => {
  it('drops an unsafe target supplied through short binding syntax', async () => {
    const { body } = await parseMarkdown('<a :href="javascript:alert(1)">go</a>')
    const html = await renderBody(body)
    expect(unsafe(hrefValues(html))).toEqual([])
  })

  it('drops an unsafe target supplied through long binding syntax', async () => {
    const { body } = await parseMarkdown('<a v-bind:href="vbscript:alert(1)">go</a>')
    const html = await renderBody(body)
    expect(unsafe(hrefValues(html))).toEqual([])
  })
})
