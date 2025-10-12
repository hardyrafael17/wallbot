// ==UserScript==
// @name        New script wallapop.com
// @namespace   Violentmonkey Scripts
// @match       https://es.wallapop.com/*
// @match       https://*.wallapop.com/*
// @grant       none
// @version     1.2
// @author      -
// @description 3/10/2025, 12:00:00 p. m. - Send data to WebSocket
// ==/UserScript==

class NetworkCapture {
  constructor() {
    this.requests = [];
    this.ws = null;
    this.originalOpen = XMLHttpRequest.prototype.open;
    this.originalSend = XMLHttpRequest.prototype.send;
    this.originalFetch = window.fetch;
    this.originalSetRequestHeader = XMLHttpRequest.prototype.setRequestHeader;
    this.connect();
    this.setupInterceptors();
  }

  connect() {
    this.ws = new WebSocket('ws://localhost:8765');
    this.ws.onopen = () => {
      console.log('WebSocket connection established.');
    };
    this.ws.onclose = () => {
      console.log('WebSocket connection closed. Reconnecting in 5 seconds...');
      setTimeout(() => this.connect(), 5000);
    };
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  setupInterceptors() {
    const self = this;

    // --- Intercept XMLHttpRequest ---

    // Store headers in a WeakMap associated with the XHR instance for better isolation
    const xhrHeadersMap = new WeakMap();

    // Intercept setRequestHeader to capture headers as they are set
    XMLHttpRequest.prototype.setRequestHeader = function(header, value) {
      if (!xhrHeadersMap.has(this)) {
        xhrHeadersMap.set(this, {});
      }
      const headers = xhrHeadersMap.get(this);
      headers[header] = value;
      // Call the original setRequestHeader
      return self.originalSetRequestHeader.apply(this, arguments);
    };

    // Intercept open to initialize the headers map for this instance
    XMLHttpRequest.prototype.open = function(method, url) {
      // Initialize headers map for this specific XHR instance
      xhrHeadersMap.set(this, {});
      this.__requestUrl = url;
      this.__requestMethod = method;
      return self.originalOpen.apply(this, arguments);
    };

    // Intercept send to capture request data and finalize headers before the request is made
    XMLHttpRequest.prototype.send = function(data) {
      this.__requestData = data; // Capture request payload
      const startTime = Date.now();
      // Finalize headers snapshot just before sending
      this.__finalHeaders = { ...xhrHeadersMap.get(this) } || {};

      const originalOnReadyStateChange = this.onreadystatechange;

      this.onreadystatechange = function() {
        if (this.readyState === 4) {
          const endTime = Date.now();
          if (this.__requestUrl && this.__requestUrl.startsWith('https://api.wallapop.com/api/v3')) {
            const customHeaders = [];
            if (this.__finalHeaders) {
              for (const [headerName, value] of Object.entries(this.__finalHeaders)) {
                customHeaders.push({ "headerName": headerName, "value": value });
              }
            }

            let parsedResponse = this.response;
            if (this.response && typeof this.response === 'string') {
              try {
                parsedResponse = JSON.parse(this.response);
              } catch (e) {
                parsedResponse = this.response;
              }
            }

            const sendToWebSocket = {
              url: this.__requestUrl,
              method: this.__requestMethod,
              status: this.status,
              headers: customHeaders,
              response: parsedResponse,
            };

            if (self.ws && self.ws.readyState === WebSocket.OPEN) {
              self.ws.send(JSON.stringify(sendToWebSocket));
            }

            self.requests.push(sendToWebSocket);

            console.log('XHR Captured:', sendToWebSocket);
            console.log('Total requests:', self.requests.length);
          }
        }
        if (originalOnReadyStateChange) {
          originalOnReadyStateChange.apply(this, arguments);
        }
      };

      return self.originalSend.apply(this, arguments);
    };

    // --- Intercept Fetch API ---
    window.fetch = function(resource, options = {}) {
      const url = resource instanceof Request ? resource.url : resource;

      if (url && url.startsWith('https://api.wallapop.com/api/v3')) {
        const customHeaders = [];
        if (options.headers) {
          if (options.headers instanceof Headers) {
            for (const [headerName, value] of options.headers.entries()) {
              customHeaders.push({ "headerName": headerName, "value": value });
            }
          } else if (typeof options.headers === 'object') {
            for (const [headerName, value] of Object.entries(options.headers)) {
              if (typeof headerName === 'string') {
                customHeaders.push({ "headerName": headerName, "value": value });
              }
            }
          }
        }

        return self.originalFetch.apply(this, arguments)
          .then(response => {
            const responseClone = response.clone();
            return responseClone.text().then(text => {
              let parsedResponse = text;
              try {
                parsedResponse = JSON.parse(text);
              } catch (e) {
                parsedResponse = text;
              }

              const sendToWebSocket = {
                url: url,
                method: options.method || 'GET',
                status: response.status,
                headers: customHeaders,
                response: parsedResponse,
              };

              if (self.ws && self.ws.readyState === WebSocket.OPEN) {
                self.ws.send(JSON.stringify(sendToWebSocket));
              }

              self.requests.push(sendToWebSocket);

              console.log('Fetch Captured:', sendToWebSocket);
              console.log('Total requests:', self.requests.length);

              return response;
            });
          })
          .catch(error => {
            const sendToWebSocket = {
              url: url,
              method: options.method || 'GET',
              status: 0,
              headers: customHeaders,
              response: error.message,
            };

            if (self.ws && self.ws.readyState === WebSocket.OPEN) {
              self.ws.send(JSON.stringify(sendToWebSocket));
            }
            self.requests.push(sendToWebSocket);

            console.log('Fetch Error Captured:', sendToWebSocket);
            console.log('Total requests:', self.requests.length);

            return Promise.reject(error);
          });
      }

      return self.originalFetch.apply(this, arguments);
    };
  }

  parsePayload(data) {
    if (!data) {
      return null;
    }

    try {
      if (typeof data === 'string') {
        if (data.startsWith('{') || data.startsWith('[')) {
          return JSON.parse(data);
        }
        if (data.includes('&')) {
          const formData = {};
          data.split('&').forEach(pair => {
            const [key, value] = pair.split('=');
            if (key && value) {
              formData[decodeURIComponent(key)] = decodeURIComponent(value.replace(/\+/g, ' '));
            }
          });
          return formData;
        }
        return data;
      } else if (data instanceof FormData) {
        const formData = {};
        for (const [key, value] of data.entries()) {
          formData[key] = value;
        }
        return formData;
      } else if (data instanceof URLSearchParams) {
        const params = {};
        for (const [key, value] of data.entries()) {
          params[key] = value;
        }
        return params;
      } else if (typeof data === 'object') {
        return data;
      }
      return data.toString();
    } catch (e) {
      return data;
    }
  }

  get capturedRequests() {
    return this.requests;
  }

  get wallapopApiV3Requests() {
    return this.requests.filter(req => req.url.startsWith('https://api.wallapop.com/api/v3'));
  }

  get requestCount() {
    return this.requests.length;
  }

  get wallapopApiV3RequestCount() {
    return this.wallapopApiV3Requests.length;
  }

  clear() {
    this.requests = [];
  }

  printRequests() {
    console.log('Captured Network Requests:', this.capturedRequests);
    console.log('Wallapop API v3 Requests:', this.wallapopApiV3Requests);
  }
}

const networkCapture = new NetworkCapture();
window.networkCapture = networkCapture;

console.log('Network capture initialized (v1.2 - WebSocket). Use window.networkCapture to access captured requests.');
console.log('Available methods: capturedRequests, wallapopApiV3Requests, requestCount, wallapopApiV3RequestCount');