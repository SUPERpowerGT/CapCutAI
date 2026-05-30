import {NextRequest} from "next/server";
import {forwardToBackend} from "../../../../server/backend-proxy";

export async function GET(request: NextRequest) {
  const workspaceId = request.nextUrl.searchParams.get("workspaceId");
  const path = workspaceId
    ? `/api/conversations?workspaceId=${encodeURIComponent(workspaceId)}`
    : "/api/conversations";

  return forwardToBackend(path);
}

export async function POST(request: NextRequest) {
  const body = await request.text();
  return forwardToBackend("/api/conversations", {
    method: "POST",
    body
  });
}
