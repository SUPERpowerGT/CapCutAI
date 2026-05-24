import {NextRequest} from "next/server";
import {forwardToBackend} from "../../../../../../server/backend-proxy";

type RouteContext = {
  params: Promise<{
    conversationId: string;
  }>;
};

export async function GET(_: NextRequest, context: RouteContext) {
  const {conversationId} = await context.params;
  return forwardToBackend(`/api/conversations/${conversationId}/messages`);
}

export async function POST(request: NextRequest, context: RouteContext) {
  const {conversationId} = await context.params;
  const body = await request.text();

  return forwardToBackend(`/api/conversations/${conversationId}/messages`, {
    method: "POST",
    body
  });
}
