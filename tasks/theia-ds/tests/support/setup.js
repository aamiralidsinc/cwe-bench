'use strict';

// Shared setup for both hidden test groups. The product code is browser code, so
// give it a DOM and a frontend application config before any product module is
// required. The ESM/stylesheet hooks come from @theia/test-setup and
// ignore-styles, which test.sh loads first.
const { enableJSDOM } = require('@theia/core/lib/browser/test/jsdom');
enableJSDOM();

const { FrontendApplicationConfigProvider } = require('@theia/core/lib/browser/frontend-application-config-provider');
FrontendApplicationConfigProvider.set({});
