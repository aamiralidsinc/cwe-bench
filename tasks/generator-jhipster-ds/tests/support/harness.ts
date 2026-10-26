/**
 * Shared verifier harness for the generated-client open paths.
 *
 * The verifier runs the real JHipster generator (see prepare.mjs) to emit Angular, React and Vue
 * clients for an entity with ImageBlob / AnyBlob / TextBlob fields. This module loads those
 * generated modules, replacing the third-party packages they import with small stubs, and then
 * executes the real generated open actions (component methods, composable methods, template event
 * expressions, React handlers) while recording every URL the code asks the browser to render.
 *
 * A record is the document the browser would display: for a blob: URL that is the Blob's type; for
 * react-jhipster it is the media type of the data: URL written into the new window's iframe (the
 * package's openFile implementation, mirrored from react-jhipster 1.0.3). A stored type that the
 * browser renders as an active document is script-capable and is rejected by the security cases.
 */
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { pathToFileURL } from 'node:url';

import ts from 'typescript';

export const FIXTURES = process.env.JHI_FIXTURES ?? '/home/agent/fixtures';

// The generated Vue components kick off service calls while setting up; their stubs resolve, but
// an unrelated rejection must not take the process down.
process.on('unhandledRejection', () => {});

const EXT = ['', '.ts', '.tsx', '.js', '.mjs', '/index.ts', '/index.tsx', '/index.js'];
const FALLBACK = 'function __jhiStub(){ return function(){ return undefined; }; }';

export interface Opened {
  type: string;
  mechanism: 'blob' | 'data-iframe';
}

export interface Recorder {
  records: Opened[];
  restore(): void;
}

/** Install the browser model: a new window and URL.createObjectURL that record the document type. */
export function installRecorder(): Recorder {
  const records: Opened[] = [];
  const g = globalThis as any;
  const origWindow = g.window;
  const origOpen = g.open;
  const origCreate = g.URL.createObjectURL;
  const origRevoke = g.URL.revokeObjectURL;
  const origRecord = g.__JHI_RECORD;
  g.window = globalThis;
  g.URL.createObjectURL = (blob: Blob) => {
    records.push({ type: String((blob as any)?.type ?? ''), mechanism: 'blob' });
    return 'blob:jhi-verifier';
  };
  g.URL.revokeObjectURL = () => {};
  g.open = () => ({
    onload: null,
    closed: false,
    location: { href: '' },
    document: {
      write: (markup: string) => {
        // A document written into the new window can carry a data: URL document of its own.
        const match = /data:([^;,)'"\s]+)/i.exec(String(markup ?? ''));
        if (match) records.push({ type: match[1], mechanism: 'data-document' });
      },
      close() {},
    },
  });
  g.__JHI_RECORD = (r: Opened) => records.push(r);
  return {
    records,
    restore() {
      g.window = origWindow;
      g.open = origOpen;
      g.URL.createObjectURL = origCreate;
      g.URL.revokeObjectURL = origRevoke;
      g.__JHI_RECORD = origRecord;
    },
  };
}

export function normalizeType(value: unknown): string {
  return String(value ?? '')
    .split(';')[0]
    .trim()
    .toLowerCase();
}

/** Document types a browser renders as an active document (script can run in it). */
export function scriptCapable(value: unknown): boolean {
  const type = normalizeType(value);
  if (!type) return false;
  if (type.endsWith('+xml')) return true;
  return [
    'text/html',
    'application/xhtml+xml',
    'text/xml',
    'application/xml',
    'text/xsl',
    'application/xslt+xml',
    'text/javascript',
    'application/javascript',
    'application/x-javascript',
    'text/x-javascript',
    'application/ecmascript',
    'text/ecmascript',
    'application/xhtml',
    'image/svg',
  ].includes(type);
}

export function isImageType(value: unknown): boolean {
  const type = normalizeType(value);
  return type.startsWith('image/') && !type.endsWith('+xml') && type !== 'image/svg';
}

export function entity(options: {
  imageContentType?: string | null;
  anyContentType?: string | null;
  imageData?: string;
  anyData?: string;
  text?: string;
} = {}) {
  return {
    id: 1,
    name: 'sample',
    textBlob: options.text ?? 'plain text',
    imageBlob: options.imageData ?? 'SkhpcHN0ZXI=',
    anyBlob: options.anyData ?? 'SkhpcHN0ZXI=',
    imageBlobContentType: options.imageContentType === undefined ? 'text/html' : options.imageContentType,
    anyBlobContentType: options.anyContentType === undefined ? 'text/html' : options.anyContentType,
  };
}

/* ------------------------------------------------------------------------------------------- */
/* Generated-module loader                                                                     */
/* ------------------------------------------------------------------------------------------- */

interface Loader {
  build(entry: string): string;
  resolveReal(spec: string, importer: string): string | null;
}

function makeLoader(appDir: string, overrides: Record<string, string | true>): Loader {
  const stubDir = join('/tmp', `jhi-stubs-${process.pid}-${Math.random().toString(36).slice(2)}`);
  mkdirSync(stubDir, { recursive: true });
  let counter = 0;
  const stubFiles = new Map<string, string>();
  const built = new Map<string, string>();
  const graph = new Map<string, { code: string; imports: { spec: string; real: string | null }[] }>();
  const specs = new Map<string, { names: Set<string>; def: boolean }>();

  function resolveReal(spec: string, importer: string): string | null {
    let base: string | null = null;
    if (spec.startsWith('app/')) base = join(appDir, 'src/main/webapp', spec);
    else if (spec.startsWith('@/')) base = join(appDir, 'src/main/webapp/app', spec.slice(2));
    else if (spec.startsWith('.')) base = join(dirname(importer), spec);
    if (!base) return null;
    for (const e of EXT) {
      const candidate = base + e;
      if (existsSync(candidate)) {
        try {
          readFileSync(candidate);
          return candidate;
        } catch {
          /* not readable */
        }
      }
    }
    return null;
  }

  function parseImports(src: string) {
    const out: { def: string | null; named: string; spec: string }[] = [];
    const re = /import\s+(?:([\w$]+)\s*,?\s*)?(?:\{([^}]*)\})?\s*from\s*['"]([^'"]+)['"]|import\s+['"]([^'"]+)['"]/g;
    let m: RegExpExecArray | null;
    while ((m = re.exec(src))) {
      out.push({ def: m[1] || null, named: m[2] || '', spec: m[3] || m[4] });
    }
    return out;
  }

  function namedList(named: string): string[] {
    if (!named) return [];
    return named
      .split(',')
      .map(s => s.trim())
      .filter(Boolean)
      .map(s => s.replace(/^type\s+/, '').split(/\s+as\s+/)[0].trim())
      .filter(Boolean);
  }

  function transpile(file: string, code: string): string {
    return ts.transpileModule(code, {
      fileName: file,
      compilerOptions: {
        module: ts.ModuleKind.ESNext,
        target: ts.ScriptTarget.ES2022,
        jsx: ts.JsxEmit.ReactJSX,
        experimentalDecorators: true,
        useDefineForClassFields: false,
        isolatedModules: true,
        verbatimModuleSyntax: false,
      },
    }).outputText;
  }

  function collect(file: string, seen = new Set<string>()): void {
    if (seen.has(file)) return;
    seen.add(file);
    const code = transpile(file, readFileSync(file, 'utf8'));
    const imports: { spec: string; real: string | null }[] = [];
    for (const im of parseImports(code)) {
      const real = overrides[im.spec] === true ? resolveReal(im.spec, file) : null;
      if (real && real !== file) collect(real, seen);
      else {
        const rec = specs.get(im.spec) ?? { names: new Set<string>(), def: false };
        if (im.def) rec.def = true;
        for (const n of namedList(im.named)) rec.names.add(n);
        specs.set(im.spec, rec);
      }
      imports.push({ spec: im.spec, real: real && real !== file ? real : null });
    }
    graph.set(file, { code, imports });
  }

  function writeStubs(): void {
    for (const [spec, rec] of specs) {
      const custom = overrides[spec];
      let body = typeof custom === 'string' ? custom : '';
      const missing = [...rec.names].filter(n => !new RegExp(`export\\s+(?:const|function|class|let|var)\\s+${n}\\b`).test(body));
      if (missing.length) body += '\n' + missing.map(n => `export const ${n} = ${FALLBACK};`).join('\n');
      if (rec.def && !/export\s+default/.test(body)) body += `\nexport default ${FALLBACK};`;
      const file = join(stubDir, `stub${counter++}.mjs`);
      writeFileSync(file, body);
      stubFiles.set(spec, file);
    }
  }

  function emit(file: string): string {
    const cached = built.get(file);
    if (cached) return cached;
    const entry = graph.get(file);
    if (!entry) throw new Error(`module not collected: ${file}`);
    let out = entry.code;
    for (const im of entry.imports) {
      const target = im.real ? emit(im.real) : stubFiles.get(im.spec);
      if (!target) throw new Error(`no stub for ${im.spec}`);
      const escaped = im.spec.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      out = out.replace(new RegExp(`(['"])${escaped}\\1`), JSON.stringify(pathToFileURL(target).href));
    }
    const outFile = join(stubDir, `mod${counter++}.mjs`);
    writeFileSync(outFile, out);
    built.set(file, outFile);
    return outFile;
  }

  return {
    build(entry: string) {
      collect(entry);
      writeStubs();
      return emit(entry);
    },
    resolveReal,
  };
}

async function importModule(file: string): Promise<any> {
  return import(pathToFileURL(file).href);
}

/* ------------------------------------------------------------------------------------------- */
/* Stub sources                                                                                */
/* ------------------------------------------------------------------------------------------- */

const ANGULAR_CORE = `
export const Component = () => (t) => t;
export const Service = () => (t) => t;
export const Injectable = () => (t) => t;
export const inject = () => globalThis.__JHI_DATAUTILS;
export const input = () => { const f = () => globalThis.__JHI_ENTITY; return f; };
export const signal = (v) => ({ value: v });
export const effect = (f) => { try { f(); } catch { /* ignore */ } };
export const untracked = (f) => (typeof f === 'function' ? f() : undefined);
export const computed = (f) => ({ value: typeof f === 'function' ? f() : undefined });
export const ElementRef = class {};
export const ViewChild = () => (t) => t;
export const OnInit = class {};
`;

const ANGULAR_OVER = {
  'app/shared/jhipster/data-utils': true as const,
  'app/core/util': `export const DataUtils = class {}; export const ParseLinks = class {};`,
  '@angular/core': ANGULAR_CORE,
  '@angular/core/rxjs-interop': `export const toSignal = () => () => undefined;`,
  '@angular/forms': `export const FormGroup = class {}; export const FormControl = class { constructor(v){ this.value = v; } }; export const ReactiveFormsModule = class {};`,
  '@angular/router': `export const RouterLink = class {}; export const ActivatedRoute = class {}; export const Router = class {}; export const Data = class {}; export const ParamMap = class {};`,
  '@angular/common': `export const NgClass = class {};`,
  rxjs: `export const Observable = class { constructor(f){} };
export const Observer = class {};
export const combineLatest = () => ({ pipe: () => ({}) });
export const filter = () => ({ pipe: () => undefined });
export const map = () => ({ pipe: () => ({}) });
export const tap = () => ({ pipe: () => ({}) });
export const of = (v) => ({ pipe: () => v });
export const finalize = () => ({ pipe: () => ({}) });`,
  '@fortawesome/angular-fontawesome': `export const FontAwesomeModule = class {};`,
  '@ng-bootstrap/ng-bootstrap/modal': `export const NgbModal = class {};`,
  '@ng-bootstrap/ng-bootstrap/tooltip': `export const NgbTooltip = class {};`,
  '@ngx-translate/core': `export const TranslatePipe = class {};`,
  'app/config': `export const DEFAULT_SORT_DATA = ''; export const ITEM_DELETED_EVENT = ''; export const SORT = '';`,
  'app/shared/alert': `export const Alert = class {}; export const AlertError = class {};`,
  'app/shared/sort': `export const SortByDirective = class {}; export const SortDirective = class {}; export const SortService = class {}; export const sortStateSignal = () => ({ value: {} });`,
  'app/shared/date': `export const DurationPipe = class {}; export const FormatMediumDatetimePipe = class {}; export const FormatMediumDatePipe = class {};`,
  'app/config/navigation.constants': `export const NAVIGATION = {};`,
  'app/shared/pagination': `export const ITEMS_PER_PAGE = 20;`,
  'app/shared/util/entity-utils': `export const overrideSortStateWithQueryParams = (s) => s;`,
  'app/shared/util/pagination.constants': `export const ASC = 'asc'; export const DESC = 'desc'; export const ITEMS_PER_PAGE = 20;`,
};

const VUE_OVER = {
  '@/shared/jhipster/data-utils': true as const,
  '@/shared/data/data-utils.service': true as const,
  './foo.service': `export default class FooService {
  constructor() {
    return () => ({
      find: async () => ({}),
      retrieve: async () => ({ data: [] }),
      update: async () => ({}),
      create: async () => ({}),
      delete: async () => ({}),
    });
  }
}`,
  '@/shared/jhipster/link-header': `export const getPageNumberFromLinkHeader = () => '';`,
  vue: `export const defineComponent = (x) => x;
export const inject = (key, factory) => (typeof factory === 'function' ? factory() : undefined);
export const ref = (v) => ({ value: v });
export const reactive = (x) => x;
export const computed = (f) => ({ value: undefined });
export const onMounted = () => {};
export const onUnmounted = () => {};
export const watch = () => {};
export const watchEffect = () => {};
export const nextTick = () => Promise.resolve();`,
  'vue-router': `export const useRoute = () => ({ params: { fooId: 1 }, query: {} });\nexport const useRouter = () => ({ go() {}, push() {}, back() {} });`,
  'vue-i18n': `export const useI18n = () => ({ t: (k) => k });`,
  '@vuelidate/core': `export const useVuelidate = () => ({ value: { $validate() {}, $touch() {}, $reset() {}, $invalid: false } });`,
  '@/shared/composables': `export const useDateFormat = () => ({ formatDate: (x) => x, formatDateLong: (x) => x });\nexport const useValidation = () => ({});`,
  '@/shared/alert/alert.service': `export const useAlertService = () => ({ showHttpError() {}, showError() {}, showInfo() {}, showSuccess() {} });`,
};

const REACT = `
export const Fragment = Symbol('Fragment');
export const useState = (init) => { const v = typeof init === 'function' ? init() : init; return [v, () => {}]; };
export const useEffect = () => {};
export const useMemo = (f) => (typeof f === 'function' ? f() : f);
export const useCallback = (f) => f;
export const useRef = (v) => ({ current: v });
export const useContext = () => ({});
export const createContext = () => ({ Provider: function () { return null; } });
export const createElement = (type, props, ...children) => ({ type, props: { ...(props || {}), children: children.length <= 1 ? children[0] : children } });
const React = { Fragment, useState, useEffect, useMemo, useCallback, useRef, useContext, createElement };
export default React;
`;

const JSX = `
export const Fragment = Symbol('Fragment');
const el = (type, props) => ({ type, props: props || {} });
export const jsx = el; export const jsxs = el; export const jsxDEV = el;
`;

// Mirrors react-jhipster 1.0.3's util/data-utils.openFile: build a data: URL for the stored type and
// write an iframe for it into a new window.
const REACT_JHIPSTER = `
export const openFile = (contentType, data) => () => {
  const fileURL = 'data:' + contentType + ';base64,' + data;
  if (globalThis.__JHI_RECORD) globalThis.__JHI_RECORD({ type: contentType, mechanism: 'data-iframe' });
  return fileURL;
};
export const byteSize = () => '0 bytes';
export const getSortState = () => ({ sort: 'id', order: 'asc' });
export const setFileData = () => {};
export const Translate = function Translate(props) { return props && props.children !== undefined ? props.children : null; };
export const TextFormat = function TextFormat() { return null; };
export const ValidatedBlobField = function ValidatedBlobField() { return null; };
`;

const REACT_OVER = {
  'app/shared/jhipster/data-utils': true as const,
  react: REACT,
  'react/jsx-runtime': JSX,
  'react/jsx-dev-runtime': JSX,
  'react-jhipster': REACT_JHIPSTER,
  'react-router': `export const Link = function Link(){ return null; }; export const useParams = () => ({ id: '1' }); export const useLocation = () => ({ pathname: '/foo', search: '', hash: '' }); export const useNavigate = () => () => {};`,
  'react-bootstrap': `const C = function C(props){ return props && props.children !== undefined ? props.children : null; };
export const Button = C; export const Col = C; export const Row = C; export const Table = C; export const FormControl = C; export const InputGroup = C; export const Form = C; export const OverlayTrigger = C; export const Tooltip = C; export const Badge = C; export const Modal = C;`,
  '@fortawesome/react-fontawesome': `export const FontAwesomeIcon = function FontAwesomeIcon(){ return null; };`,
  '@fortawesome/free-solid-svg-icons': `export const faSort = {}; export const faSortUp = {}; export const faSortDown = {};`,
  'app/config/store': `export const useAppDispatch = () => () => {};\nexport const useAppSelector = (sel) => sel(globalThis.__JHI_STATE);`,
  'app/shared/util/entity-utils': `export const overrideSortStateWithQueryParams = (s) => s; export const getSortState = () => ({ sort: 'id', order: 'asc' }); export const sortStateToSearchParams = () => '';`,
  'app/shared/util/pagination.constants': `export const ASC = 'asc'; export const DESC = 'desc'; export const ITEMS_PER_PAGE = 20;`,
  'app/shared/DurationFormat': `export const DurationFormat = function DurationFormat(){ return null; };`,
  'app/config/constants': `export const APP_DATE_FORMAT = 'x'; export const APP_LOCAL_DATE_FORMAT = 'y';`,
  'app/shared/util/date-utils': `export const convertDateTimeFromServer = (x) => x; export const convertDateTimeToServer = (x) => x;`,
  'app/config/notification-middleware': `export const notificationMiddleware = () => (next) => (action) => next(action);`,
};

/* ------------------------------------------------------------------------------------------- */
/* Drivers                                                                                     */
/* ------------------------------------------------------------------------------------------- */

function appFile(client: string, rel: string): string {
  return join(FIXTURES, client, 'src/main/webapp/app', rel);
}

function readTemplate(client: string, rel: string): string {
  return readFileSync(join(FIXTURES, client, 'src/main/webapp', rel), 'utf8');
}

function stripNonNull(expr: string): string {
  return expr.replace(/([)\]\w$])!(?=[.)\s,;]|$)/g, '$1');
}

function evalExpression(expr: string, scope: Record<string, unknown>): void {
  const cleaned = stripNonNull(expr);
  try {
    // eslint-disable-next-line no-new-func
    new Function('scope', `with(scope){ return (${cleaned}); }`)(scope);
  } catch {
    // eslint-disable-next-line no-new-func
    new Function('scope', `with(scope){ ${cleaned} }`)(scope);
  }
}

function clickExpressions(template: string, attr: 'click' | 'vue'): string[] {
  const re = attr === 'click' ? /\(click\)="([^"]*)"/g : /@click="([^"]*)"/g;
  const out: string[] = [];
  let m: RegExpExecArray | null;
  while ((m = re.exec(template))) out.push(m[1]);
  return out;
}

function runClickExpressions(template: string, attr: 'click' | 'vue', scope: Record<string, unknown>): void {
  for (const expr of clickExpressions(template, attr)) {
    try {
      evalExpression(expr, scope);
    } catch {
      // An unrelated handler on the same page may not be evaluable outside a browser; its failure
      // does not open anything. The security cases still require an open to be delivered.
    }
  }
}

function signalOf(value: unknown): any {
  const fn: any = () => value;
  return new Proxy(fn, {
    get: (_t, key) => (value && typeof value === 'object' && key in (value as any) ? (value as any)[key] : undefined),
    apply: () => value,
  });
}

function prototypeScope(Cls: any, dataUtils: unknown, extra: Record<string, unknown>): Record<string, unknown> {
  let instance: any;
  try {
    instance = new Cls();
  } catch {
    instance = Object.create(Cls.prototype);
  }
  instance.dataUtils = dataUtils;
  const scope: Record<string, unknown> = Object.create(null);
  for (const name of Object.getOwnPropertyNames(Cls.prototype)) {
    if (name === 'constructor') continue;
    const value = Cls.prototype[name];
    if (typeof value === 'function') scope[name] = value.bind(instance);
  }
  scope.dataUtils = dataUtils;
  Object.assign(scope, extra);
  return scope;
}

async function loadAngularService(): Promise<any> {
  const loader = makeLoader(join(FIXTURES, 'angular'), ANGULAR_OVER as any);
  const service = loader.resolveReal('app/core/util/data-util.service', appFile('angular', 'x.ts'));
  if (!service) throw new Error('generated Angular DataUtils service not found');
  return importModule(loader.build(service));
}

export interface AngularContext {
  dataUtils: any;
  detail: any;
  list: any;
  update: any;
}

export async function loadAngular(): Promise<AngularContext> {
  const g = globalThis as any;
  const serviceModule = await loadAngularService();
  const dataUtils = new serviceModule.DataUtils();
  g.__JHI_DATAUTILS = dataUtils;
  const detailLoader = makeLoader(join(FIXTURES, 'angular'), ANGULAR_OVER as any);
  const detail = await importModule(detailLoader.build(appFile('angular', 'entities/foo/detail/foo-detail.ts')));
  const listLoader = makeLoader(join(FIXTURES, 'angular'), ANGULAR_OVER as any);
  const list = await importModule(listLoader.build(appFile('angular', 'entities/foo/list/foo.ts')));
  const updateLoader = makeLoader(join(FIXTURES, 'angular'), ANGULAR_OVER as any);
  const update = await importModule(updateLoader.build(appFile('angular', 'entities/foo/update/foo-update.ts')));
  return { dataUtils, detail, list, update };
}

function angularEditForm(ent: any) {
  return {
    value: ent,
    get: (name: string) => ({ value: ent[name] }),
    patchValue: () => {},
    setValue: () => {},
  };
}

export function driveAngularDetail(ctx: AngularContext, ent: any): void {
  const scope = prototypeScope(ctx.detail.FooDetail, ctx.dataUtils, {
    fooRef: signalOf(ent),
    foo: ent,
    editForm: angularEditForm(ent),
  });
  runClickExpressions(readTemplate('angular', 'app/entities/foo/detail/foo-detail.html'), 'click', scope);
}

export function driveAngularList(ctx: AngularContext, ent: any): void {
  const scope = prototypeScope(ctx.list.Foo, ctx.dataUtils, {
    foo: ent,
    foos: () => [ent],
    editForm: angularEditForm(ent),
  });
  runClickExpressions(readTemplate('angular', 'app/entities/foo/list/foo.html'), 'click', scope);
}

export function driveAngularUpdate(ctx: AngularContext, ent: any): void {
  const scope = prototypeScope(ctx.update.FooUpdate, ctx.dataUtils, {
    foo: ent,
    fooRef: signalOf(ent),
    imageBlobRef: { value: ent.imageBlob },
    anyBlobRef: { value: ent.anyBlob },
    textBlobRef: { value: ent.textBlob },
    nameRef: { value: ent.name },
    editForm: angularEditForm(ent),
  });
  runClickExpressions(readTemplate('angular', 'app/entities/foo/update/foo-update.html'), 'click', scope);
}

export interface VueContext {
  composable: any;
  details: any;
  list: any;
  update: any;
}

export async function loadVue(): Promise<VueContext> {
  const composableLoader = makeLoader(join(FIXTURES, 'vue'), VUE_OVER as any);
  const composable = await importModule(
    composableLoader.build(appFile('vue', 'shared/data/data-utils.service.ts')),
  );
  const detailsLoader = makeLoader(join(FIXTURES, 'vue'), VUE_OVER as any);
  const details = await importModule(
    detailsLoader.build(appFile('vue', 'entities/foo/foo-details.component.ts')),
  );
  const listLoader = makeLoader(join(FIXTURES, 'vue'), VUE_OVER as any);
  const list = await importModule(listLoader.build(appFile('vue', 'entities/foo/foo.component.ts')));
  const updateLoader = makeLoader(join(FIXTURES, 'vue'), VUE_OVER as any);
  const update = await importModule(
    updateLoader.build(appFile('vue', 'entities/foo/foo-update.component.ts')),
  );
  return { composable, details, list, update };
}

function unwrapSetup(result: Record<string, any>, ent: any): Record<string, unknown> {
  const scope: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(result)) {
    const isRef =
      value && typeof value === 'object' && 'value' in (value as any) && Object.keys(value as any).length === 1;
    scope[key] = isRef ? (value as any).value : value;
  }
  scope.foo = ent;
  return scope;
}

function driveVueComponent(component: any, templateRel: string, ent: any): void {
  const setupResult = component.setup();
  if (setupResult.foo && typeof setupResult.foo === 'object') setupResult.foo.value = ent;
  if (setupResult.foos && typeof setupResult.foos === 'object') setupResult.foos.value = [ent];
  const scope = unwrapSetup(setupResult, ent);
  runClickExpressions(readTemplate('vue', templateRel), 'vue', scope);
}

export function driveVueDetails(ctx: VueContext, ent: any): void {
  driveVueComponent(ctx.details.default ?? ctx.details, 'app/entities/foo/foo-details.vue', ent);
}

export function driveVueList(ctx: VueContext, ent: any): void {
  driveVueComponent(ctx.list.default ?? ctx.list, 'app/entities/foo/foo.vue', ent);
}

export function driveVueUpdate(ctx: VueContext, ent: any): void {
  driveVueComponent(ctx.update.default ?? ctx.update, 'app/entities/foo/foo-update.vue', ent);
}

export interface ReactContext {
  detail: any;
  list: any;
}

export async function loadReact(): Promise<ReactContext> {
  const detailLoader = makeLoader(join(FIXTURES, 'react'), REACT_OVER as any);
  const detail = await importModule(detailLoader.build(appFile('react', 'entities/foo/foo-detail.tsx')));
  const listLoader = makeLoader(join(FIXTURES, 'react'), REACT_OVER as any);
  const list = await importModule(listLoader.build(appFile('react', 'entities/foo/foo.tsx')));
  return { detail, list };
}

function collectHandlers(node: any, out: ((...args: any[]) => void)[]): void {
  if (Array.isArray(node)) {
    for (const item of node) collectHandlers(item, out);
    return;
  }
  if (node && typeof node === 'object' && 'props' in node) {
    const props = (node as any).props ?? {};
    for (const [name, value] of Object.entries(props)) {
      if (/^on[A-Z]/.test(name) && typeof value === 'function') out.push(value as any);
    }
    collectHandlers(props.children, out);
  }
}

function renderReact(Component: any, ent: any): void {
  const state = {
    foo: { entity: ent, entities: [ent], loading: false, totalItems: 1, updating: false },
    authentication: { account: {}, isAuthenticated: true },
    applicationProfile: { ribbonEnv: '' },
  };
  (globalThis as any).__JHI_STATE = state;
  const tree = Component();
  const handlers: ((...args: any[]) => void)[] = [];
  collectHandlers(tree, handlers);
  for (const handler of handlers) {
    try {
      handler();
    } catch {
      // Unrelated page handlers are stubbed; failures there do not open anything.
    }
  }
}

export interface HelperContext {
  openFile(data: string, contentType: string | null | undefined, blobType?: string): void;
  byteSize(data: string): string;
}

/** Load the shared generated helper from one client's emitted source. */
export async function loadHelper(client: 'angular' | 'react' | 'vue'): Promise<HelperContext> {
  const overrides = client === 'vue' ? VUE_OVER : client === 'react' ? REACT_OVER : ANGULAR_OVER;
  const spec = client === 'vue' ? '@/shared/jhipster/data-utils' : 'app/shared/jhipster/data-utils';
  const loader = makeLoader(join(FIXTURES, client), overrides as any);
  const file = loader.resolveReal(spec, appFile(client, 'x.ts'));
  if (!file) throw new Error(`generated ${client} shared helper not found`);
  return importModule(loader.build(file));
}

export function driveReactDetail(ctx: ReactContext, ent: any): void {
  const Component = ctx.detail.FooDetail ?? Object.values(ctx.detail).find(v => typeof v === 'function');
  renderReact(Component, ent);
}

export function driveReactList(ctx: ReactContext, ent: any): void {
  const Component = ctx.list.Foo ?? Object.values(ctx.list).find(v => typeof v === 'function');
  renderReact(Component, ent);
}

/* ------------------------------------------------------------------------------------------- */
/* Assertions                                                                                  */
/* ------------------------------------------------------------------------------------------- */

export function scriptOpenings(records: Opened[]): Opened[] {
  return records.filter(r => scriptCapable(r.type));
}

export function check(condition: unknown, message: string): void {
  if (!condition) throw new Error(message);
}

/** Assert an action was delivered and never opened a script-capable document. */
export function assertDeliveredSafely(records: Opened[], where: string): void {
  check(records.length > 0, `${where}: the open action delivered nothing (${describeRecords(records)})`);
  const unsafe = scriptOpenings(records);
  check(unsafe.length === 0, `${where}: a script-capable document was opened (${describeRecords(unsafe)})`);
}

/** Assert the action opened an inline raster image of the given type. */
export function assertImageOpened(records: Opened[], expected: string, where: string): void {
  assertDeliveredSafely(records, where);
  const wanted = normalizeType(expected);
  check(
    records.some(r => normalizeType(r.type) === wanted),
    `${where}: expected an inline ${wanted} preview, got ${describeRecords(records)}`,
  );
}

export function describeRecords(records: Opened[]): string {
  return records.length ? records.map(r => `${r.mechanism}:${r.type || '(none)'}`).join(', ') : '(nothing opened)';
}
