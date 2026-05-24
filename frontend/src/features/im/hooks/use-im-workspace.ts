import {useEffect, useMemo, useRef, useState} from "react";
import {
  createConversation,
  deleteConversation,
  listConversations,
  listMessages,
  sendMessage
} from "../api/im-client";
import {buildPendingUserMessage, extractPreviewHeadline} from "../lib/formatters";
import type {Conversation, Message} from "../types/contracts";

export function useImWorkspace() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [prompt, setPrompt] = useState("");
  const [isBooting, setIsBooting] = useState(true);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messageEndRef = useRef<HTMLDivElement>(null);

  const activeConversation = useMemo(
    () =>
      conversations.find(
        (conversation) => conversation.conversationId === activeConversationId
      ) ?? null,
    [activeConversationId, conversations]
  );

  const previewHeadline = useMemo(() => extractPreviewHeadline(messages), [messages]);

  const loadMessages = async (conversationId: string) => {
    setIsLoadingMessages(true);
    try {
      const data = await listMessages(conversationId);
      setMessages(data);
    } finally {
      setIsLoadingMessages(false);
    }
  };

  const boot = async () => {
    setIsBooting(true);
    setError(null);

    try {
      const loaded = await listConversations();
      if (loaded.length === 0) {
        const created = await createConversation("New Conversation");
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
  }, []);

  useEffect(() => {
    messageEndRef.current?.scrollIntoView({behavior: "smooth", block: "end"});
  }, [messages, isSending]);

  const createConversationAction = async () => {
    try {
      const created = await createConversation("New Conversation");
      setConversations((prev) => [created, ...prev]);
      setActiveConversationId(created.conversationId);
      setMessages([]);
      setError(null);
    } catch (exception) {
      setError(
        exception instanceof Error ? exception.message : "Failed to create conversation."
      );
    }
  };

  const selectConversationAction = async (conversationId: string) => {
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
    if (!normalized || !activeConversationId || isSending) return;

    const optimisticMessage = buildPendingUserMessage(activeConversationId, normalized);

    setIsSending(true);
    setError(null);
    setPrompt("");
    setMessages((prev) => [...prev, optimisticMessage]);

    try {
      const response = await sendMessage(activeConversationId, normalized);
      setMessages((prev) => [
        ...prev.filter((message) => message.messageId !== optimisticMessage.messageId),
        response.userMessage,
        response.assistantMessage
      ]);
      const refreshed = await listConversations();
      setConversations(refreshed);
    } catch (exception) {
      setMessages((prev) =>
        prev.filter((message) => message.messageId !== optimisticMessage.messageId)
      );
      setPrompt(normalized);
      setError(exception instanceof Error ? exception.message : "Failed to send message.");
    } finally {
      setIsSending(false);
    }
  };

  const refreshAction = async () => {
    if (!activeConversationId) return;
    try {
      setError(null);
      const refreshedConversations = await listConversations();
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
      setError(null);
      await deleteConversation(conversationId);

      const remainingConversations = conversations.filter(
        (conversation) => conversation.conversationId !== conversationId
      );

      if (activeConversationId === conversationId) {
        const nextConversation = remainingConversations[0] ?? null;
        setActiveConversationId(nextConversation?.conversationId ?? null);
        if (nextConversation) {
          await loadMessages(nextConversation.conversationId);
        } else {
          setMessages([]);
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
    error,
    previewHeadline,
    messageEndRef,
    createConversationAction,
    selectConversationAction,
    sendMessageAction,
    refreshAction,
    deleteConversationAction
  };
}
