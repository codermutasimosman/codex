"""Stealth helpers for Playwright Chromium sessions.

This module mirrors the public API of the ``patchright`` package and
contains a comprehensive browser fingerprint hardening routine.  The
implementation intentionally ships with the project so the application can
operate in restricted environments without fetching third-party packages at
runtime.
"""
from __future__ import annotations

from typing import Any

from playwright.sync_api import BrowserContext, Frame, Page

__all__ = ["apply_stealth_sync"]


_STEALTH_INIT_SCRIPT = """
(() => {
  const install = (target) => {
    if (!target || target.__patchrightInstalled) {
      return;
    }
    Object.defineProperty(target, '__patchrightInstalled', {
      value: true,
      configurable: false,
      enumerable: false,
      writable: false,
    });

    const safeDefineProperty = (object, property, descriptor) => {
      if (!object) {
        return;
      }
      try {
        Object.defineProperty(object, property, descriptor);
      } catch (error) {
        // Ignore descriptor redefinition errors.
      }
    };

    const defineGetter = (object, property, getter) => {
      safeDefineProperty(object, property, {
        configurable: true,
        enumerable: false,
        get: getter,
      });
    };

    const defineDataProperty = (object, property, value, enumerable = false) => {
      safeDefineProperty(object, property, {
        configurable: true,
        enumerable,
        writable: true,
        value,
      });
    };

    const safeDelete = (object, property) => {
      if (!object) {
        return;
      }
      try {
        delete object[property];
      } catch (error) {
        // Ignore non-configurable properties.
      }
    };

    const { navigator } = target;
    const originalPlugins = navigator && navigator.plugins ? navigator.plugins : undefined;
    const originalMimeTypes = navigator && navigator.mimeTypes ? navigator.mimeTypes : undefined;
    const pluginArrayPrototype = originalPlugins ? Object.getPrototypeOf(originalPlugins) : undefined;
    const mimeTypeArrayPrototype = originalMimeTypes ? Object.getPrototypeOf(originalMimeTypes) : undefined;
    const pluginPrototype = originalPlugins && originalPlugins.length ? Object.getPrototypeOf(originalPlugins[0]) : undefined;
    const mimeTypePrototype = originalMimeTypes && originalMimeTypes.length ? Object.getPrototypeOf(originalMimeTypes[0]) : undefined;

    const cleanupAutomationArtifacts = () => {
      const keysToClear = [
        '__webdriver_evaluate',
        '__selenium_evaluate',
        '__webdriver_script_fn',
        '__webdriver_unwrapped',
        '__driver_evaluate',
        '__driver_unwrapped',
      ];
      const patterns = [/^__.*?webdriver/i, /.*?__driver__/i, /.*?__selenium__/i, /cdc_.+_(Array|Promise|Symbol)/i];

      const scrub = (object) => {
        if (!object) {
          return;
        }
        keysToClear.forEach((key) => safeDelete(object, key));
        Object.getOwnPropertyNames(object).forEach((property) => {
          if (patterns.some((pattern) => pattern.test(property))) {
            safeDelete(object, property);
          }
        });
      };

      scrub(target);
      scrub(target.document);

      if (target.document && target.document.documentElement) {
        target.document.documentElement.removeAttribute('webdriver');
      }
    };

    const patchNavigatorCore = () => {
      if (!navigator) {
        return;
      }

      const prototype = Object.getPrototypeOf(navigator);
      if (prototype) {
        try {
          const replacement = Object.create(prototype);
          Object.getOwnPropertyNames(prototype).forEach((name) => {
            if (name === 'webdriver') {
              return;
            }
            const descriptor = Object.getOwnPropertyDescriptor(prototype, name);
            if (descriptor) {
              Object.defineProperty(replacement, name, descriptor);
            }
          });
          Object.setPrototypeOf(navigator, replacement);
        } catch (error) {
          // Ignore prototype reassignment failures.
        }
      }

      safeDelete(navigator, 'webdriver');
      safeDelete(Object.getPrototypeOf(navigator), 'webdriver');
      if ('webdriver' in navigator) {
        defineGetter(Object.getPrototypeOf(navigator), 'webdriver', () => undefined);
      }

      const userAgent = navigator.userAgent
        .replace('HeadlessChrome/', 'Chrome/')
        .replace(/\sHeadless/i, '');
      defineGetter(navigator, 'userAgent', () => userAgent);
      defineGetter(navigator, 'appVersion', () => navigator.appVersion.replace('HeadlessChrome/', 'Chrome/'));
      defineGetter(navigator, 'platform', () => 'Win32');
      defineGetter(navigator, 'vendor', () => 'Google Inc.');
      defineGetter(navigator, 'pdfViewerEnabled', () => true);
      defineGetter(navigator, 'hardwareConcurrency', () => 8);
      defineGetter(navigator, 'deviceMemory', () => 8);
      defineGetter(navigator, 'maxTouchPoints', () => 0);
      defineGetter(navigator, 'language', () => 'en-US');
      defineGetter(navigator, 'languages', () => Object.freeze(['en-US', 'en']));
      defineGetter(navigator, 'doNotTrack', () => '1');

      if (navigator.connection) {
        defineGetter(navigator.connection, 'downlink', () => 10);
        defineGetter(navigator.connection, 'effectiveType', () => '4g');
        defineGetter(navigator.connection, 'rtt', () => 50);
        defineGetter(navigator.connection, 'saveData', () => false);
      }
    };

    const ensureChromeRuntime = () => {
      if (!target.chrome) {
        defineDataProperty(target, 'chrome', {});
      }

      const { chrome } = target;
      if (!chrome.app) {
        chrome.app = {};
      }
      defineDataProperty(chrome.app, 'isInstalled', false);
      chrome.app.InstallState = chrome.app.InstallState || {
        DISABLED: 'disabled',
        INSTALLED: 'installed',
        NOT_INSTALLED: 'not_installed',
      };
      chrome.app.RunningState = chrome.app.RunningState || {
        CANNOT_RUN: 'cannot_run',
        READY_TO_RUN: 'ready_to_run',
        RUNNING: 'running',
      };
      chrome.app.getDetails = chrome.app.getDetails || (() => null);
      chrome.app.getIsInstalled = chrome.app.getIsInstalled || (() => false);

      if (!chrome.runtime) {
        chrome.runtime = {};
      }
      chrome.runtime.connect = chrome.runtime.connect || (() => ({
        name: '',
        sender: undefined,
        onDisconnect: { addListener: () => undefined, removeListener: () => undefined },
        onMessage: { addListener: () => undefined, removeListener: () => undefined },
        disconnect: () => undefined,
        postMessage: () => undefined,
      }));
      chrome.runtime.sendMessage = chrome.runtime.sendMessage || (() => undefined);
      chrome.runtime.getManifest = chrome.runtime.getManifest || (() => ({}));
      chrome.runtime.getURL = chrome.runtime.getURL || ((path) => `chrome-extension://invalid/${String(path || '').replace(/^[/]+/, '')}`);
      if (!('id' in chrome.runtime)) {
        chrome.runtime.id = undefined;
      }

      chrome.webstore = chrome.webstore || {
        onInstallStageChanged: { addListener: () => undefined, removeListener: () => undefined },
        onDownloadProgress: { addListener: () => undefined, removeListener: () => undefined },
        install: (_url, _onsuccess, onfailure) => {
          if (typeof onfailure === 'function') {
            onfailure(new Error('Chrome Web Store installation is not supported in this context.'));
          }
        },
      };

      chrome.csi = chrome.csi || (() => ({
        onloadT: 0,
        pageT: 0,
        startE: Date.now(),
        totalT: 0,
      }));

      chrome.loadTimes = chrome.loadTimes || (() => {
        const now = Date.now() / 1000;
        return {
          requestTime: now - 0.1,
          startLoadTime: now - 0.1,
          commitLoadTime: now - 0.05,
          finishDocumentLoadTime: now - 0.02,
          finishLoadTime: now,
          firstPaintAfterLoadTime: now,
          navigationType: 'Reload',
          wasFetchedViaSpdy: true,
          wasNpnNegotiated: true,
          wasAlternateProtocolAvailable: true,
          connectionInfo: 'h2',
        };
      });
    };

    const createPermissionStatus = (state) => {
      const status = { state, onchange: null };
      safeDefineProperty(status, Symbol.toStringTag, { value: 'PermissionStatus' });
      return status;
    };

    const patchPermissions = () => {
      if (!navigator || !navigator.permissions || typeof navigator.permissions.query !== 'function') {
        return;
      }
      const originalQuery = navigator.permissions.query.bind(navigator.permissions);
      navigator.permissions.query = (parameters) => {
        const name = parameters && parameters.name ? parameters.name : parameters;
        const normalized = typeof name === 'string' ? name.toLowerCase() : name;
        if (normalized === 'notifications') {
          const permission = target.Notification && typeof target.Notification.permission === 'string'
            ? target.Notification.permission
            : 'default';
          return Promise.resolve(createPermissionStatus(permission));
        }
        const promptLike = new Set([
          'background-fetch',
          'background-sync',
          'camera',
          'clipboard',
          'clipboard-read',
          'clipboard-write',
          'display-capture',
          'geolocation',
          'midi',
          'midi-sysex',
          'microphone',
          'nfc',
          'notifications',
          'payment-handler',
          'periodic-background-sync',
          'push',
          'speaker',
          'window-placement',
        ]);
        if (promptLike.has(normalized)) {
          return Promise.resolve(createPermissionStatus('prompt'));
        }
        return originalQuery(parameters).catch(() => createPermissionStatus('prompt'));
      };
    };

    const patchNotification = () => {
      if (!target.Notification) {
        return;
      }
      const { Notification } = target;
      const descriptor = Object.getOwnPropertyDescriptor(Notification, 'permission');
      if (descriptor && descriptor.configurable) {
        defineGetter(Notification, 'permission', () => (descriptor.get ? descriptor.get.call(Notification) : 'default'));
      }
      if (!('permission' in Notification)) {
        defineGetter(Notification, 'permission', () => 'default');
      }
      if (typeof Notification.requestPermission === 'function') {
        const original = Notification.requestPermission.bind(Notification);
        Notification.requestPermission = (callback) => {
          const result = original();
          if (typeof callback === 'function') {
            return result.then((value) => {
              callback(value);
              return value;
            });
          }
          return result;
        };
      }
    };

    const patchClipboard = () => {
      if (!navigator) {
        return;
      }
      if (navigator.clipboard && typeof navigator.clipboard.readText === 'function' && typeof navigator.clipboard.writeText === 'function') {
        return;
      }
      let clipboardText = '';
      const clipboard = navigator.clipboard || {};
      defineDataProperty(clipboard, 'readText', () => Promise.resolve(clipboardText));
      defineDataProperty(clipboard, 'writeText', (value) => {
        clipboardText = String(value ?? '');
        return Promise.resolve();
      });
      if (!navigator.clipboard) {
        safeDefineProperty(clipboard, Symbol.toStringTag, { value: 'Clipboard' });
        defineGetter(navigator, 'clipboard', () => clipboard);
      }
    };

    const patchBattery = () => {
      if (!navigator || typeof navigator.getBattery !== 'function') {
        return;
      }
      const battery = {
        charging: true,
        chargingTime: 0,
        dischargingTime: Infinity,
        level: 1,
        addEventListener: () => undefined,
        removeEventListener: () => undefined,
        dispatchEvent: () => false,
        onchargingchange: null,
        onchargingtimechange: null,
        ondischargingtimechange: null,
        onlevelchange: null,
      };
      navigator.getBattery = () => Promise.resolve(battery);
    };

    const patchPlugins = () => {
      if (!navigator) {
        return;
      }

      const createMimeType = (plugin, definition) => {
        const mimeType = {};
        defineDataProperty(mimeType, 'type', definition.type, true);
        defineDataProperty(mimeType, 'suffixes', definition.suffixes, true);
        defineDataProperty(mimeType, 'description', definition.description, true);
        defineGetter(mimeType, 'enabledPlugin', () => plugin);
        safeDefineProperty(mimeType, Symbol.toStringTag, { value: 'MimeType' });
        if (mimeTypePrototype) {
          Object.setPrototypeOf(mimeType, mimeTypePrototype);
        }
        return mimeType;
      };

      const createPlugin = (definition) => {
        const plugin = {};
        defineDataProperty(plugin, 'name', definition.name, true);
        defineDataProperty(plugin, 'filename', definition.filename, true);
        defineDataProperty(plugin, 'description', definition.description, true);
        safeDefineProperty(plugin, Symbol.toStringTag, { value: 'Plugin' });
        const mimeTypes = definition.mimeTypes.map((mime) => createMimeType(plugin, mime));
        defineGetter(plugin, 'length', () => mimeTypes.length);
        plugin.item = (index) => mimeTypes[index] || null;
        plugin.namedItem = (name) => mimeTypes.find((mime) => mime.type === name) || null;
        plugin[Symbol.iterator] = function* iterator() {
          for (const mimeType of mimeTypes) {
            yield mimeType;
          }
        };
        mimeTypes.forEach((mimeType, index) => {
          defineDataProperty(plugin, index, mimeType, true);
          if (mimeType.type) {
            defineDataProperty(plugin, mimeType.type, mimeType);
          }
        });
        if (pluginPrototype) {
          Object.setPrototypeOf(plugin, pluginPrototype);
        }
        return plugin;
      };

      const definitions = [
        {
          name: 'Chrome PDF Plugin',
          filename: 'internal-pdf-viewer',
          description: 'Portable Document Format',
          mimeTypes: [
            { type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format' },
            { type: 'text/pdf', suffixes: 'pdf', description: 'Portable Document Format' },
          ],
        },
        {
          name: 'Chrome PDF Viewer',
          filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
          description: '',
          mimeTypes: [
            { type: 'application/pdf', suffixes: 'pdf', description: '' },
          ],
        },
        {
          name: 'Native Client',
          filename: 'internal-nacl-plugin',
          description: '',
          mimeTypes: [],
        },
      ];

      const plugins = definitions.map(createPlugin);
      const pluginArray = {};
      safeDefineProperty(pluginArray, Symbol.toStringTag, { value: 'PluginArray' });
      defineGetter(pluginArray, 'length', () => plugins.length);
      pluginArray.item = (index) => plugins[index] || null;
      pluginArray.namedItem = (name) => plugins.find((plugin) => plugin.name === name) || null;
      pluginArray.refresh = () => undefined;
      pluginArray[Symbol.iterator] = function* iterator() {
        for (const plugin of plugins) {
          yield plugin;
        }
      };
      plugins.forEach((plugin, index) => {
        defineDataProperty(pluginArray, index, plugin, true);
        if (plugin.name) {
          defineDataProperty(pluginArray, plugin.name, plugin);
        }
      });
      if (pluginArrayPrototype) {
        Object.setPrototypeOf(pluginArray, pluginArrayPrototype);
      }

      const mimeTypes = [];
      plugins.forEach((plugin) => {
        for (const mimeType of plugin) {
          mimeTypes.push(mimeType);
        }
      });
      const mimeTypeArray = {};
      safeDefineProperty(mimeTypeArray, Symbol.toStringTag, { value: 'MimeTypeArray' });
      defineGetter(mimeTypeArray, 'length', () => mimeTypes.length);
      mimeTypeArray.item = (index) => mimeTypes[index] || null;
      mimeTypeArray.namedItem = (name) => mimeTypes.find((mime) => mime.type === name) || null;
      mimeTypeArray[Symbol.iterator] = function* iterator() {
        for (const mimeType of mimeTypes) {
          yield mimeType;
        }
      };
      mimeTypes.forEach((mimeType, index) => {
        defineDataProperty(mimeTypeArray, index, mimeType, true);
        if (mimeType.type) {
          defineDataProperty(mimeTypeArray, mimeType.type, mimeType);
        }
      });
      if (mimeTypeArrayPrototype) {
        Object.setPrototypeOf(mimeTypeArray, mimeTypeArrayPrototype);
      }

      defineGetter(navigator, 'plugins', () => pluginArray);
      defineGetter(navigator, 'mimeTypes', () => mimeTypeArray);
    };

    const patchUserAgentData = () => {
      if (!navigator || !navigator.userAgentData) {
        return;
      }
      const uaData = navigator.userAgentData;
      const match = navigator.userAgent.match(/Chrome\/([0-9.]+)/);
      const version = match ? match[1] : '123.0.0.0';
      const major = version.split('.')[0];
      const brands = [
        { brand: 'Chromium', version: major },
        { brand: 'Google Chrome', version: major },
        { brand: 'Not:A-Brand', version: '24' },
      ];
      defineGetter(uaData, 'brands', () => brands);
      defineGetter(uaData, 'mobile', () => false);
      defineGetter(uaData, 'platform', () => 'Windows');
      defineDataProperty(uaData, 'getHighEntropyValues', (hints) => Promise.resolve({
        architecture: 'x86',
        bitness: '64',
        brands,
        mobile: false,
        model: '',
        platform: 'Windows',
        platformVersion: '10.0.0',
        uaFullVersion: version,
        fullVersionList: brands,
      }));
      defineDataProperty(uaData, 'toJSON', () => ({
        brands,
        mobile: false,
        platform: 'Windows',
      }));
    };

    const patchScreen = () => {
      if (!target.screen) {
        return;
      }
      const width = 1920;
      const height = 1080;
      const availHeight = 1040;
      defineGetter(target.screen, 'width', () => width);
      defineGetter(target.screen, 'height', () => height);
      defineGetter(target.screen, 'availWidth', () => width);
      defineGetter(target.screen, 'availHeight', () => availHeight);
      defineGetter(target.screen, 'colorDepth', () => 24);
      defineGetter(target.screen, 'pixelDepth', () => 24);
      if (!('orientation' in target.screen)) {
        defineDataProperty(target.screen, 'orientation', { type: 'landscape-primary', angle: 0 });
      }
      if (!('availLeft' in target.screen)) {
        defineGetter(target.screen, 'availLeft', () => 0);
        defineGetter(target.screen, 'availTop', () => 0);
      }
      if (!('devicePixelRatio' in target) || !target.devicePixelRatio) {
        defineGetter(target, 'devicePixelRatio', () => 1);
      }
    };

    const patchStorageEstimate = () => {
      if (!navigator || !navigator.storage || typeof navigator.storage.estimate !== 'function') {
        return;
      }
      const originalEstimate = navigator.storage.estimate.bind(navigator.storage);
      navigator.storage.estimate = () => originalEstimate()
        .then((estimate) => ({
          quota: estimate && typeof estimate.quota === 'number' && estimate.quota > 0 ? estimate.quota : 120 * 1024 * 1024,
          usage: estimate && typeof estimate.usage === 'number' && estimate.usage > 0 ? estimate.usage : 30 * 1024 * 1024,
        }))
        .catch(() => ({ quota: 120 * 1024 * 1024, usage: 30 * 1024 * 1024 }));
    };

    const patchWebGl = () => {
      const vendor = 'Intel Inc.';
      const renderer = 'Intel Iris OpenGL Engine';
      const override = (contextName) => {
        const context = target[contextName];
        if (!context || !context.prototype || typeof context.prototype.getParameter !== 'function') {
          return;
        }
        const original = context.prototype.getParameter;
        defineDataProperty(context.prototype, 'getParameter', function(...args) {
          const [parameter] = args;
          if (parameter === 37445) {
            return vendor;
          }
          if (parameter === 37446) {
            return renderer;
          }
          return original.apply(this, args);
        });
      };
      override('WebGLRenderingContext');
      override('WebGL2RenderingContext');
    };

    const patchEval = () => {
      if (!target.eval || typeof target.eval !== 'function') {
        return;
      }
      const originalEval = target.eval;
      target.eval = new Proxy(originalEval, {
        apply: (fn, thisArg, args) => Reflect.apply(fn, thisArg, args),
      });
    };

    const patchOuterDimensions = () => {
      if (target.outerWidth === 0 && target.innerWidth > 0) {
        defineGetter(target, 'outerWidth', () => target.innerWidth);
      }
      if (target.outerHeight === 0 && target.innerHeight > 0) {
        defineGetter(target, 'outerHeight', () => target.innerHeight);
      }
    };

    const patchMediaDevices = () => {
      if (!navigator || !navigator.mediaDevices || typeof navigator.mediaDevices.enumerateDevices !== 'function') {
        return;
      }
      const originalEnumerate = navigator.mediaDevices.enumerateDevices.bind(navigator.mediaDevices);
      navigator.mediaDevices.enumerateDevices = () => originalEnumerate()
        .then((devices) => {
          if (Array.isArray(devices) && devices.length) {
            return devices;
          }
          return [
            { deviceId: 'default', groupId: 'default', kind: 'audioinput', label: 'Default - Microphone' },
            { deviceId: 'default', groupId: 'default', kind: 'audiooutput', label: 'Default - Speakers' },
            { deviceId: 'default', groupId: 'default', kind: 'videoinput', label: 'Integrated Camera' },
          ];
        })
        .catch(() => [
          { deviceId: 'default', groupId: 'default', kind: 'audioinput', label: 'Default - Microphone' },
          { deviceId: 'default', groupId: 'default', kind: 'audiooutput', label: 'Default - Speakers' },
          { deviceId: 'default', groupId: 'default', kind: 'videoinput', label: 'Integrated Camera' },
        ]);
    };

    const patchConsole = () => {
      if (!target.console) {
        return;
      }
      if (typeof target.console.debug !== 'function') {
        target.console.debug = (...args) => target.console.log.apply(target.console, args);
      }
    };

    const patchIntl = () => {
      if (!target.Intl || !target.Intl.DateTimeFormat) {
        return;
      }
      const original = target.Intl.DateTimeFormat.prototype.resolvedOptions;
      defineDataProperty(target.Intl.DateTimeFormat.prototype, 'resolvedOptions', function(...args) {
        const options = original.apply(this, args);
        if (!options.timeZone) {
          options.timeZone = 'America/New_York';
        }
        return options;
      });
    };

    patchNavigatorCore();
    ensureChromeRuntime();
    patchPermissions();
    patchNotification();
    patchClipboard();
    patchBattery();
    patchPlugins();
    patchUserAgentData();
    patchScreen();
    patchStorageEstimate();
    patchWebGl();
    patchEval();
    patchOuterDimensions();
    patchMediaDevices();
    patchConsole();
    patchIntl();
    cleanupAutomationArtifacts();
  };

  install(window);

  const patchFrameAccess = (constructorName) => {
    const constructor = window[constructorName];
    if (!constructor || !constructor.prototype) {
      return;
    }
    const descriptor = Object.getOwnPropertyDescriptor(constructor.prototype, 'contentWindow');
    if (!descriptor || typeof descriptor.get !== 'function') {
      return;
    }
    Object.defineProperty(constructor.prototype, 'contentWindow', {
      configurable: true,
      enumerable: descriptor.enumerable,
      get: function patchedContentWindow() {
        const frameWindow = descriptor.get.call(this);
        if (frameWindow) {
          try {
            install(frameWindow);
          } catch (error) {
            // Ignore cross-origin frame access issues.
          }
        }
        return frameWindow;
      },
    });
  };

  patchFrameAccess('HTMLIFrameElement');
  patchFrameAccess('HTMLFrameElement');

  if (typeof window.open === 'function') {
    const originalOpen = window.open;
    window.open = function patchedWindowOpen(...args) {
      const opened = originalOpen.apply(this, args);
      if (opened) {
        try {
          install(opened);
        } catch (error) {
          // Ignore cross-origin access errors.
        }
      }
      return opened;
    };
  }
})();
"""


def _apply_to_page(page: Page) -> None:
    """Ensure ``page`` evaluates the stealth script immediately and later."""

    if page.is_closed():
        return
    page.add_init_script(_STEALTH_INIT_SCRIPT)

    def _evaluate_frame(frame: Frame) -> None:
        if frame.is_detached():
            return
        try:
            frame.evaluate(_STEALTH_INIT_SCRIPT)
        except Exception:
            # Cross-origin frames may reject evaluation.
            pass

    def _safe_eval(*_: Any) -> None:
        if page.is_closed():
            return
        try:
            page.evaluate(_STEALTH_INIT_SCRIPT)
        except Exception:
            # Evaluation may fail for privileged pages (e.g. about:blank).
            pass
        for frame in page.frames:
            if frame is page.main_frame or frame.is_detached():
                continue
            _evaluate_frame(frame)

    _safe_eval()
    page.on("domcontentloaded", _safe_eval)
    page.on("load", _safe_eval)
    page.on("frameattached", _evaluate_frame)
    page.on("framenavigated", _evaluate_frame)


def apply_stealth_sync(context: BrowserContext) -> None:
    """Inject stealth JavaScript for each page created in ``context``."""

    context.add_init_script(_STEALTH_INIT_SCRIPT)
    for page in context.pages:
        _apply_to_page(page)

    def _handle_page(page: Page) -> None:
        _apply_to_page(page)

    context.on("page", _handle_page)
