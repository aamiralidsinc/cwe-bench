import { createApp, h } from 'vue';
import MdPreview from '~~/MdPreview';
import { config, globalConfig } from '~/config';

export type Mounted = {
  el: HTMLDivElement;
  app: ReturnType<typeof createApp>;
  preview: HTMLElement;
};

/** Mount the public preview component with the given props. */
export const mountPreview = (props: Record<string, unknown>): Mounted => {
  const el = document.createElement('div');
  document.body.appendChild(el);
  const app = createApp({ render: () => h(MdPreview as never, props) });
  // A hostile identifier can make the component's own unrelated event wiring throw; the
  // rendered markup is what these checks look at.
  app.config.errorHandler = () => {};
  app.mount(el);
  const preview = el.querySelector('.md-editor-preview') as HTMLElement;
  return { el, app, preview };
};

export const unmount = (m: Mounted) => {
  m.app.unmount();
  m.el.remove();
};

/** Configure the display texts for the en-US language. */
export const setEnglishText = (copyCode: Record<string, string>) => {
  config({
    editorConfig: { languageUserDefined: { 'en-US': { copyCode } } }
  } as never);
};

/** Pre-load an optional renderer instance the way a host application can. */
export const setInstance = (
  name: 'highlight' | 'katex' | 'mermaid' | 'echarts',
  instance: unknown
) => {
  const extensions = globalConfig.editorExtensions as Record<string, unknown>;
  extensions[name] = { ...(extensions[name] as object), instance };
};

export const clearInstance = (
  name: 'highlight' | 'katex' | 'mermaid' | 'echarts'
) => {
  const extensions = globalConfig.editorExtensions as Record<string, unknown>;
  const current = extensions[name] as Record<string, unknown> | undefined;
  if (current) delete current.instance;
};

/** The optional renderers a check does not need to exercise. */
export const QUIET = { noKatex: true, noMermaid: true, noEcharts: true } as const;
