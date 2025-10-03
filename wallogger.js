// ==UserScript==
// @name        New script wallapop.com
// @namespace   Violentmonkey Scripts
// @match       https://es.wallapop.com/*
// @match       https://*.wallapop.com/*
// @grant       none
// @version     1.1
// @author      -
// @description 29/9/2025, 7:16:41 p. m. - Captures headers too
// ==/UserScript==

class NetworkCapture {
  constructor() {
    this.requests = [];
    this.originalOpen = XMLHttpRequest.prototype.open;
    this.originalSend = XMLHttpRequest.prototype.send;
    this.originalFetch = window.fetch;
    this.originalSetRequestHeader = XMLHttpRequest.prototype.setRequestHeader;
    this.setupInterceptors();
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
        if (this.readyState === 4) { // Request completed
          const endTime = Date.now();
          if (this.__requestUrl && this.__requestUrl.startsWith('https://api.wallapop.com/api/v3')) {
            const url = new URL(this.__requestUrl);
            const urlParams = {};
            for (const [key, value] of url.searchParams) {
              urlParams[key] = value;
            }

            // Prepare headers array from the captured headers
            const customHeaders = [];
            if (this.__finalHeaders) {
              for (const [headerName, value] of Object.entries(this.__finalHeaders)) {
                customHeaders.push({ "headerName": headerName, "value": value });
              }
            }

            let parsedResponse = this.response;
            // Try to parse response as JSON
            if (this.response && typeof this.response === 'string') {
              try {
                parsedResponse = JSON.parse(this.response);
              } catch (e) {
                // If JSON parsing fails, keep original response
                parsedResponse = this.response;
              }
            }
            // This should be sent to WebSocket
            const sendToWebSocket = {
              urlEndPoint: this.__requestUrl,
              method: this.__requestMethod,
              status: this.status,
              response: parsedResponse,
              payload: self.parsePayload(this.__requestData),
              urlParams: urlParams,
              startTime: startTime,
              endTime: endTime,
              duration: endTime - startTime,
            };
            // The object above should be sent to WebSocket 
            self.requests.push({
              urlEndPoint: this.__requestUrl,
              method: this.__requestMethod,
              status: this.status,
              response: parsedResponse,
              payload: self.parsePayload(this.__requestData),
              urlParams: urlParams,
              startTime: startTime,
              endTime: endTime,
              duration: endTime - startTime,
              "custom_headers": customHeaders // Add the captured headers
            });

            console.log('XHR Captured:', {
              url: this.__requestUrl,
              method: this.__requestMethod,
              status: this.status,
              headers: customHeaders, // Log headers too
              response: parsedResponse
            });
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
        const startTime = Date.now();
        const payload = self.parsePayload(options.body);

        // Parse URL parameters
        const urlObj = new URL(url);
        const urlParams = {};
        for (const [key, value] of urlObj.searchParams) {
          urlParams[key] = value;
        }

        // Prepare headers array for fetch
        const customHeaders = [];
        if (options.headers) {
          // Handle Headers object or plain object
          if (options.headers instanceof Headers) {
            for (const [headerName, value] of options.headers.entries()) {
              customHeaders.push({ "headerName": headerName, "value": value });
            }
          } else if (typeof options.headers === 'object') {
            for (const [headerName, value] of Object.entries(options.headers)) {
              // Ensure headerName is a string
              if (typeof headerName === 'string') {
                customHeaders.push({ "headerName": headerName, "value": value });
              }
            }
          }
        }

        return self.originalFetch.apply(this, arguments)
          .then(response => {
            const endTime = Date.now();
            // Clone response to read it without consuming it
            const responseClone = response.clone();
            return responseClone.text().then(text => {
              let parsedResponse = text;
              // Try to parse response as JSON
              try {
                parsedResponse = JSON.parse(text);
              } catch (e) {
                // If JSON parsing fails, keep original text
                parsedResponse = text;
              }

              self.requests.push({
                urlEndPoint: url,
                method: options.method || 'GET',
                status: response.status,
                response: parsedResponse,
                payload: payload,
                urlParams: urlParams,
                startTime: startTime,
                endTime: endTime,
                duration: endTime - startTime,
                "custom_headers": customHeaders // Add the captured headers
              });

              console.log('Fetch Captured:', {
                url: url,
                method: options.method || 'GET',
                status: response.status,
                headers: customHeaders, // Log headers too
                response: parsedResponse
              });
              console.log('Total requests:', self.requests.length);

              return response;
            });
          })
          .catch(error => {
            // Handle network errors
            const endTime = Date.now();
            self.requests.push({
              urlEndPoint: url,
              method: options.method || 'GET',
              status: 0,
              response: error.message,
              payload: payload,
              urlParams: urlParams,
              startTime: startTime,
              endTime: endTime,
              duration: endTime - startTime,
              "custom_headers": customHeaders // Add the captured headers
            });

            console.log('Fetch Error Captured:', {
              url: url,
              method: options.method || 'GET',
              status: 0,
              headers: customHeaders, // Log headers too
              error: error.message
            });
            console.log('Total requests:', self.requests.length);

            return Promise.reject(error);
          });
      }

      return self.originalFetch.apply(this, arguments);
    };
  }

  // Helper method to parse different types of payloads
  parsePayload(data) {
    if (!data) {
      return null;
    }

    try {
      if (typeof data === 'string') {
        // Try to parse as JSON
        if (data.startsWith('{') || data.startsWith('[')) {
          return JSON.parse(data);
        }
        // Try to parse as form data
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
      // If parsing fails, return the original data
      return data;
    }
  }

  // Getter for all captured requests
  get capturedRequests() {
    return this.requests;
  }

  // Getter for Wallapop API v3 requests only
  get wallapopApiV3Requests() {
    return this.requests.filter(req => req.urlEndPoint.startsWith('https://api.wallapop.com/api/v3'));
  }

  // Getter for request count
  get requestCount() {
    return this.requests.length;
  }

  // Getter for Wallapop API v3 request count
  get wallapopApiV3RequestCount() {
    return this.wallapopApiV3Requests.length;
  }

  // Method to clear captured requests
  clear() {
    this.requests = [];
  }

  // Method to print captured requests to console
  printRequests() {
    console.log('Captured Network Requests:', this.capturedRequests);
    console.log('Wallapop API v3 Requests:', this.wallapopApiV3Requests);
  }
}

// Initialize the network capture
const networkCapture = new NetworkCapture();

// Make it globally accessible
window.networkCapture = networkCapture;

console.log('Network capture initialized (v1.1 - Headers). Use window.networkCapture to access captured requests.');
console.log('Available methods: capturedRequests, wallapopApiV3Requests, requestCount, wallapopApiV3RequestCount');