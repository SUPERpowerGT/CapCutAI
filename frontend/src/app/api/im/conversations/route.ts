import {NextRequest} from "next/server";
import {forwardToBackend} from "../../../../server/backend-proxy";

export async function GET() {
  return forwardToBackend("/api/conversations");
}

export async function POST(request: NextRequest) {
  const body = await request.text();
  return forwardToBackend("/api/conversations", {
    method: "POST",
    body
  });
}
