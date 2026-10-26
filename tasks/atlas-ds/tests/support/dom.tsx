import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import { MemoryRouter } from "react-router-dom";

export const ATLAS: string = (globalThis as any).process?.env?.ATLAS_ROOT || "/workspace";

export function makeStore(state: any) {
  return configureStore({ reducer: (s: any = state) => s, middleware: (g: any) => g({ serializableCheck: false }) });
}

export function renderAt(element: React.ReactElement, state: any = {}, url = "/") {
  return renderToStaticMarkup(
    <Provider store={makeStore(state)}>
      <MemoryRouter initialEntries={[url]}>{element}</MemoryRouter>
    </Provider>
  );
}

export function parse(html: string): HTMLElement {
  const root = document.createElement("div");
  root.innerHTML = html;
  return root;
}

const UNSAFE_URL = /^\s*(javascript|data|vbscript):/i;

/** True when the rendering created an executable markup construct. */
export function executableMarkup(root: HTMLElement): string[] {
  const found: string[] = [];
  root.querySelectorAll("script,iframe,object,embed,base,meta").forEach((el) => {
    found.push("<" + el.tagName.toLowerCase() + ">");
  });
  root.querySelectorAll("*").forEach((el) => {
    Array.from(el.attributes).forEach((attr) => {
      if (/^on/i.test(attr.name)) found.push(el.tagName.toLowerCase() + "[" + attr.name + "]");
      if (
        (attr.name === "href" || attr.name === "src" || attr.name === "action") &&
        UNSAFE_URL.test(attr.value.replace(/[\u0000- ]/g, ""))
      ) {
        found.push(el.tagName.toLowerCase() + "[unsafe-url]");
      }
    });
  });
  return found;
}

/** The allowed rich-text vocabulary that must keep rendering. */
export function formattingPresent(root: HTMLElement): boolean {
  return Boolean(
    root.querySelector("b,strong,em,u,ul,ol,li,p,h1,h2,h3,h4") &&
    root.querySelector('a[href^="https://"]')
  );
}
