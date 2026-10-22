// Minimal NextResponse for the app-router handlers.

export class NextResponse {
  status: number;
  body: any;
  constructor(body: any, init?: { status?: number }) {
    this.body = body;
    this.status = init?.status ?? 200;
  }
  static json(body: any, init?: { status?: number }) {
    return new NextResponse(body, init);
  }
}
