import { createSSRApp, h } from 'vue'
import { renderToString } from 'vue/server-renderer'
import MDCRenderer from '../../src/runtime/components/MDCRenderer.vue'

/**
 * Render a parsed document through the library's real renderer and return the HTML.
 */
export async function renderBody(body: any, options: { data?: any, components?: any } = {}) {
  const app = createSSRApp({
    render: () => h(MDCRenderer as any, {
      body,
      data: options.data || {},
      components: options.components || {},
    }),
  })
  return await renderToString(app)
}

const SCHEMES = ['javascript:', 'vbscript:', 'data:text/html', 'data:text/javascript', 'data:text/vbscript', 'data:text/css', 'data:text/plain', 'data:text/xml']

/** Values of every attribute whose local name is `href` (including prefixed names like xlink:href). */
export function hrefValues(html: string): string[] {
  return attributeValues(html, '(?:[\\w.-]+:)?href')
}

/** Values of the `xlink:href` attribute only. */
export function xlinkHrefValues(html: string): string[] {
  return attributeValues(html, 'xlink:href')
}

/** Values of every `src` attribute. */
export function srcValues(html: string): string[] {
  return attributeValues(html, 'src')
}

function attributeValues(html: string, namePattern: string): string[] {
  const re = new RegExp(`(?:^|\\s)${namePattern}\\s*=\\s*"([^"]*)"`, 'gi')
  return [...html.matchAll(re)].map(m => m[1])
}

/** The subset of values that starts with one of the schemes this library refuses. */
export function unsafe(values: string[]): string[] {
  return values.filter(v => SCHEMES.some(prefix => v.trim().toLowerCase().startsWith(prefix)))
}
