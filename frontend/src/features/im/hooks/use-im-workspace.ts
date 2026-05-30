import {useEffect, useMemo, useRef, useState} from "react";
import {
  createConversation,
  deleteConversation,
  listConversations,
  listMessages,
  sendMessage
} from "../api/im-client";
import {buildPendingUserMessage, extractPreviewHeadline} from "../lib/formatters";
import type {AgentActivityItem, Conversation, Message} from "../types/contracts";

export function useImWorkspace(workspaceId: string | null) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [prompt, setPrompt] = useState("");
  const [isBooting, setIsBooting] = useState(true);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [isStreamingAssistant, setIsStreamingAssistant] = useState(false);
  const [agentStatus, setAgentStatus] = useState("IDLE");
  const [error, setError] = useState<string | null>(null);
  const [streamingAssistantMessage, setStreamingAssistantMessage] = useState<Message | null>(null);
  const messageEndRef = useRef<HTMLDivElement>(null);
  const streamTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const activeConversation = useMemo(
    () =>
      conversations.find(
        (conversation) => conversation.conversationId === activeConversationId
      ) ?? null,
    [activeConversationId, conversations]
  );

  const previewHeadline = useMemo(() => extractPreviewHeadline(messages), [messages]);

  const taskSummary = useMemo(() => {
    if (error) {
      return "当前任务遇到问题，可以重试或补充新的指令。";
    }

    if (isSending) {
      return "Agent 正在理解当前指令并组织下一步。";
    }

    if (isStreamingAssistant) {
      return "Agent 正在返回当前阶段的结果。";
    }

    if (messages.length === 0) {
      return "准备接收新的分析、生成或修订指令。";
    }

    return "继续补充指令，Agent 会基于当前上下文工作。";
  }, [error, isSending, isStreamingAssistant, messages.length]);

  const currentActivity = useMemo<AgentActivityItem | null>(() => {
    if (error) {
      return {
        id: "activity-error",
        kind: "STATUS",
        state: "FAILED",
        title: "Request failed",
        detail: error
      };
    }

    if (isStreamingAssistant) {
      return {
        id: "activity-streaming",
        kind: "STATUS",
        state: "STREAMING",
        title: "Agent responding",
        detail: taskSummary
      };
    }

    if (isSending) {
      return {
        id: "activity-thinking",
        kind: "STATUS",
        state: "THINKING",
        title: "Agent thinking",
        detail: taskSummary
      };
    }

    return null;
  }, [error, isSending, isStreamingAssistant, taskSummary]);

  const loadMessages = async (conversationId: string) => {
    setIsLoadingMessages(true);
    try {
      const data = await listMessages(conversationId);
      setMessages(data);
      setAgentStatus(data.length === 0 ? "IDLE" : "COMPLETED");
    } finally {
      setIsLoadingMessages(false);
    }
  };

  const boot = async () => {
    if (!workspaceId) {
      setIsBooting(false);
      setConversations([]);
      setActiveConversationId(null);
      setMessages([]);
      setAgentStatus("IDLE");
      return;
    }

    setIsBooting(true);
    setError(null);

    try {
      const loaded = await listConversations(workspaceId);
      if (loaded.length === 0) {
        const created = await createConversation({
          title: "New Conversation",
          workspaceId
        });
        setConversations([created]);
        setActiveConversationId(created.conversationId);
        await loadMessages(created.conversationId);
      } else {
        setConversations(loaded);
        setActiveConversationId(loaded[0].conversationId);
        await loadMessages(loaded[0].conversationId);
      }
    } catch (exception) {
      setError(
        exception instanceof Error ? exception.message : "Failed to initialize IM workspace."
      );
    } finally {
      setIsBooting(false);
    }
  };

  useEffect(() => {
    void boot();
  }, [workspaceId]);

  useEffect(() => {
    messageEndRef.current?.scrollIntoView({behavior: "smooth", block: "end"});
  }, [messages, isSending, isStreamingAssistant, streamingAssistantMessage]);

  useEffect(() => {
    return () => {
      if (streamTimerRef.current) {
        clearTimeout(streamTimerRef.current);
      }
    };
  }, []);

  const stopStreaming = () => {
    if (streamTimerRef.current) {
      clearTimeout(streamTimerRef.current);
      streamTimerRef.current = null;
    }
    setIsStreamingAssistant(false);
    setStreamingAssistantMessage(null);
    setAgentStatus("IDLE");
  };

  const streamAssistantReply = async (assistantMessage: Message) => {
    stopStreaming();
    setIsStreamingAssistant(true);
    setAgentStatus("STREAMING");

    const fullContent = assistantMessage.content;
    const words = fullContent.split(/(\s+)/).filter(Boolean);
    const chunks = words.length > 1 ? words : Array.from(fullContent);

    return new Promise<void>((resolve) => {
      let cursor = 0;
      let currentContent = "";

      const tick = () => {
        if (cursor >= chunks.length) {
          setStreamingAssistantMessage(null);
          setMessages((prev) => [...prev, assistantMessage]);
          setIsStreamingAssistant(false);
          setAgentStatus("COMPLETED");
          streamTimerRef.current = null;
          resolve();
          return;
        }

        currentContent += chunks[cursor];
        cursor += 1;

        setStreamingAssistantMessage({
          ...assistantMessage,
          content: currentContent
        });

        streamTimerRef.current = setTimeout(tick, words.length > 1 ? 48 : 24);
      };

      tick();
    });
  };

  const createConversationAction = async () => {
    if (!workspaceId) {
      return;
    }

    try {
      stopStreaming();
      const created = await createConversation({
        title: "New Conversation",
        workspaceId
      });
      setConversations((prev) => [created, ...prev]);
      setActiveConversationId(created.conversationId);
      setMessages([]);
      setPrompt("");
      setAgentStatus("IDLE");
      setError(null);
    } catch (exception) {
      setError(
        exception instanceof Error ? exception.message : "Failed to create conversation."
      );
    }
  };

  const selectConversationAction = async (conversationId: string) => {
    stopStreaming();
    setActiveConversationId(conversationId);
    try {
      await loadMessages(conversationId);
      setError(null);
    } catch (exception) {
      setError(
        exception instanceof Error ? exception.message : "Failed to load messages."
      );
    }
  };

  const sendMessageAction = async () => {
    const normalized = prompt.trim();
    if (!normalized || !activeConversationId || isSending || isStreamingAssistant) return;

    const optimisticMessage = buildPendingUserMessage(activeConversationId, normalized);

    setIsSending(true);
    setAgentStatus("THINKING");
    setError(null);
    setPrompt("");
    setMessages((prev) => [...prev, optimisticMessage]);

    try {
      const response = await sendMessage(activeConversationId, normalized);
      setMessages((prev) => [
        ...prev.filter((message) => message.messageId !== optimisticMessage.messageId),
        response.userMessage
      ]);
      const refreshed = await listConversations(workspaceId ?? undefined);
      setConversations(refreshed);
      setAgentStatus(response.agentStatus || "COMPLETED");
      await streamAssistantReply(response.assistantMessage);
    } catch (exception) {
      setMessages((prev) =>
        prev.filter((message) => message.messageId !== optimisticMessage.messageId)
      );
      setPrompt(normalized);
      setAgentStatus("FAILED");
      setError(exception instanceof Error ? exception.message : "Failed to send message.");
    } finally {
      setIsSending(false);
    }
  };

  const refreshAction = async () => {
    if (!activeConversationId) return;
    try {
      stopStreaming();
      setError(null);
      const refreshedConversations = await listConversations(workspaceId ?? undefined);
      setConversations(refreshedConversations);
      await loadMessages(activeConversationId);
    } catch (exception) {
      setError(
        exception instanceof Error ? exception.message : "Failed to refresh conversation."
      );
    }
  };

  const deleteConversationAction = async (conversationId: string) => {
    try {
      stopStreaming();
      setError(null);
      await deleteConversation(conversationId);

      const remainingConversations = conversations.filter(
        (conversation) => conversation.conversationId !== conversationId
      );

      if (activeConversationId === conversationId) {
        const currentIndex = conversations.findIndex(
          (conversation) => conversation.conversationId === conversationId
        );
        const nextConversation =
          remainingConversations[currentIndex] ??
          remainingConversations[currentIndex - 1] ??
          null;
        setActiveConversationId(nextConversation?.conversationId ?? null);
        if (nextConversation) {
          await loadMessages(nextConversation.conversationId);
        } else {
          setMessages([]);
          setAgentStatus("IDLE");
        }
      }

      setConversations(remainingConversations);
    } catch (exception) {
      setError(
        exception instanceof Error ? exception.message : "Failed to delete conversation."
      );
    }
  };

  return {
    conversations,
    activeConversationId,
    activeConversation,
    messages,
    prompt,
    setPrompt,
    isBooting,
    isLoadingMessages,
    isSending,
    isStreamingAssistant,
    agentStatus,
    error,
    previewHeadline,
    taskSummary,
    currentActivity,
    streamingAssistantMessage,
    messageEndRef,
    createConversationAction,
    selectConversationAction,
    sendMessageAction,
    refreshAction,
    deleteConversationAction
  };
}
