type MessageHandler = (data: any) => void;

export class TaskWebSocket {
  private ws: WebSocket | null = null;
  private handlers = new Map<string, MessageHandler[]>();

  connect(taskId: string | number) {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    this.ws = new WebSocket(`${protocol}//${host}/ws/tasks/${taskId}`);

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const type = data.type || "message";
        const handlers = this.handlers.get(type) || [];
        handlers.forEach((h) => h(data));
      } catch {
        /* ignore */
      }
    };

    this.ws.onclose = () => {
      setTimeout(() => this.connect(taskId), 3000);
    };
  }

  on(event: string, handler: MessageHandler) {
    if (!this.handlers.has(event)) this.handlers.set(event, []);
    this.handlers.get(event)!.push(handler);
  }

  disconnect() {
    this.ws?.close();
    this.ws = null;
  }
}
