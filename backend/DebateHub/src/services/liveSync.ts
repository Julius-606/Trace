
type LiveHandler = (event: { type: string; payload: any; timestamp: string }) => void;

class LiveSyncService {
  private eventSource: EventSource | null = null;
  private handlers: Set<LiveHandler> = new Set();
  private isConnected = false;

  connect() {
    if (this.eventSource) return;

    try {
      this.eventSource = new EventSource('/api/live/stream');

      this.eventSource.onopen = () => {
        this.isConnected = true;
      };

      this.eventSource.onmessage = (e) => {
        try {
          const parsed = JSON.parse(e.data);
          this.handlers.forEach((h) => {
            try {
              h(parsed);
            } catch (err) {
              console.warn('Handler error:', err);
            }
          });
        } catch (err) {
          // Heartbeat or non-json message
        }
      };

      this.eventSource.onerror = () => {
        this.isConnected = false;
        // EventSource automatically retries connection
      };
    } catch (e) {
      console.warn('Live EventSource not supported in this environment');
    }
  }

  subscribe(handler: LiveHandler): () => void {
    this.handlers.add(handler);
    this.connect();

    return () => {
      this.handlers.delete(handler);
      if (this.handlers.size === 0 && this.eventSource) {
        this.eventSource.close();
        this.eventSource = null;
      }
    };
  }

  get connected(): boolean {
    return this.isConnected;
  }
}

export const liveSync = new LiveSyncService();


