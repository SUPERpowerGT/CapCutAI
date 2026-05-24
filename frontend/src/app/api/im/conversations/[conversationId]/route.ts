import {NextRequest} from "next/server";
import {forwardToBackend} from "../../../../../server/backend-proxy";

type RouteContext = {
  params: Promise<{
    conversationId: string;
  }>;
};

export async function DELETE(_: NextRequest, context: RouteContext) {
  const {conversationId} = await context.params;
  return forwardToBackend(`/api/conversations/${conversationId}`, {
    method: "DELETE"
  });
}
