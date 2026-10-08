/**
 * SSE (Server-Sent Events) Handler
 * Provides robust SSE connection management with automatic reconnection
 */

import { API_ENDPOINTS } from './api-config';

export interface SSEHandlerOptions {
  onMessage: (data: any) => void;
  onError?: (error: any) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  maxRetries?: number;
  retryDelay?: number;
}

export class SSEHandler {
  private eventSource: EventSource | null = null;
  private requestId: string;
  private options: SSEHandlerOptions;
  private retryCount: number = 0;
  private isIntentionallyClosed: boolean = false;
  private reconnectTimeout: NodeJS.Timeout | null = null;

  constructor(requestId: string, options: SSEHandlerOptions) {
    this.requestId = requestId;
    this.options = {
      maxRetries: 3,
      retryDelay: 2000,
      ...options
    };
  }

  connect(): void {
    if (this.eventSource) {
      console.log(`SSE already connected for request ${this.requestId}`);
      return;
    }

    this.isIntentionallyClosed = false;
    const url = API_ENDPOINTS.statusStream(this.requestId);
    console.log(`Connecting to SSE: ${url}`);

    try {
      this.eventSource = new EventSource(url);

      this.eventSource.onopen = () => {
        console.log(`SSE connection opened for request ${this.requestId}`);
        this.retryCount = 0;
        this.options.onConnect?.();
      };

      this.eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Ignore keepalive messages
          if (data.keepalive) {
            return;
          }
          
          this.options.onMessage(data);
        } catch (err) {
          console.error('Error parsing SSE data:', err, event.data);
        }
      };

      this.eventSource.onerror = (error) => {
        console.error(`SSE error for request ${this.requestId}:`, error);
        
        // Only reconnect if not intentionally closed and under retry limit
        if (!this.isIntentionallyClosed && this.retryCount < (this.options.maxRetries || 3)) {
          this.handleReconnect();
        } else {
          this.options.onError?.(error);
          this.disconnect();
        }
      };

    } catch (error) {
      console.error(`Failed to create EventSource for ${this.requestId}:`, error);
      this.options.onError?.(error);
    }
  }

  private handleReconnect(): void {
    this.retryCount++;
    console.log(`Attempting reconnect ${this.retryCount}/${this.options.maxRetries} for request ${this.requestId}`);
    
    // Clean up current connection
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }

    // Schedule reconnection
    this.reconnectTimeout = setTimeout(() => {
      if (!this.isIntentionallyClosed) {
        this.connect();
      }
    }, this.options.retryDelay);
  }

  disconnect(): void {
    this.isIntentionallyClosed = true;
    
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.eventSource) {
      console.log(`Closing SSE connection for request ${this.requestId}`);
      this.eventSource.close();
      this.eventSource = null;
      this.options.onDisconnect?.();
    }
  }

  isConnected(): boolean {
    return this.eventSource !== null && this.eventSource.readyState === EventSource.OPEN;
  }
}