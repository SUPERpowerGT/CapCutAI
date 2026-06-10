import {useEffect, useMemo, useRef, useState} from "react";
import {
  createConversation,
  deleteConversation,
  listConversations,
  listMessages,
  sendMessage
} from "../api/im-client";
import {
  inspectWorkspaceAnalysisProgress,
  type WorkspaceAnalysisProgress
} from "../api/workflow-progress";
import {buildPendingUserMessage, extractPreviewHeadline} from "../lib/formatters";
import type {
  AgentActivityItem,
  AgentArtifacts,
  AgentWorkspaceContext,
  Conversation,
  Message
} from "../types/contracts";

type ActiveWorkflow =
  | "ANALYZE_REFERENCE"
  | "CREATE_STYLED_VIDEO"
  | "ANALYZE_AND_CREATE_STYLED_VIDEO";

export function useImWorkspace(
  workspaceId: string | null,
  workspaceContext?: AgentWorkspaceContext | null
) {
  const [activeWorkflow, setActiveWorkflow] = useState<ActiveWorkflow | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [messageArtifacts, setMessageArtifacts] = useState<Record<string, AgentArtifacts>>({});
  const [prompt, setPrompt] = useState("");
  const [isBooting, setIsBooting] = useState(true);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [isStreamingAssistant, setIsStreamingAssistant] = useState(false);
  const [agentStatus, setAgentStatus] = useState("IDLE");
  const [error, setError] = useState<string | null>(null);
  const [streamingAssistantMessage, setStreamingAssistantMessage] = useState<Message | null>(null);
  const [workflowRunStartedAt, setWorkflowRunStartedAt] = useState<number | null>(null);
  const [workflowProgressTick, setWorkflowProgressTick] = useState(0);
  const [analysisProgress, setAnalysisProgress] = useState<WorkspaceAnalysisProgress | null>(null);
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

    if (isSending && activeWorkflow) {
      const elapsedSeconds = workflowRunStartedAt
        ? Math.max(0, Math.floor((Date.now() - workflowRunStartedAt) / 1000))
        : 0;
      if (
        (activeWorkflow === "ANALYZE_REFERENCE" ||
          activeWorkflow === "ANALYZE_AND_CREATE_STYLED_VIDEO") &&
        analysisProgress
      ) {
        const progress = describeWorkflowProgress(
          activeWorkflow,
          elapsedSeconds,
          workspaceContext,
          analysisProgress
        );
        return {
          id: `activity-${activeWorkflow.toLowerCase()}-${analysisProgress.stage}`,
          kind: "TOOL",
          state: analysisProgress.completed ? "COMPLETED" : "THINKING",
          title: progress.title,
          detail: `${progress.detail}\n${formatAnalysisProgressChecklist(analysisProgress)}`,
          source: progress.source
        };
      }

      const progress = describeWorkflowProgress(activeWorkflow, elapsedSeconds, workspaceContext);

      return {
        id: `activity-${activeWorkflow.toLowerCase()}`,
        kind: "TOOL",
        state: "THINKING",
        title: progress.title,
        detail: progress.detail,
        source: progress.source
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
  }, [
    activeWorkflow,
    analysisProgress,
    error,
    isSending,
    isStreamingAssistant,
    taskSummary,
    workflowProgressTick,
    workflowRunStartedAt
  ]);

  const loadMessages = async (conversationId: string) => {
    setIsLoadingMessages(true);
    try {
      const data = await listMessages(conversationId);
      setMessages(data);
      setMessageArtifacts({});
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
      setMessageArtifacts({});
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

  useEffect(() => {
    if (!isSending || !activeWorkflow) {
      return;
    }

    const timer = window.setInterval(() => {
      setWorkflowProgressTick((tick) => tick + 1);
    }, 1000);

    return () => window.clearInterval(timer);
  }, [activeWorkflow, isSending]);

  useEffect(() => {
    if (
      !isSending ||
      (activeWorkflow !== "ANALYZE_REFERENCE" &&
        activeWorkflow !== "ANALYZE_AND_CREATE_STYLED_VIDEO") ||
      !workspaceId
    ) {
      setAnalysisProgress(null);
      return;
    }

    let cancelled = false;
    const poll = async () => {
      try {
        const progress = await inspectWorkspaceAnalysisProgress(workspaceId);
        if (!cancelled && progress) {
          setAnalysisProgress(progress);
        }
      } catch {
        if (!cancelled) {
          setAnalysisProgress(null);
        }
      }
    };

    void poll();
    const timer = window.setInterval(() => {
      void poll();
    }, 2000);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [activeWorkflow, isSending, workspaceId]);

  const stopStreaming = () => {
    if (streamTimerRef.current) {
      clearTimeout(streamTimerRef.current);
      streamTimerRef.current = null;
    }
    setIsStreamingAssistant(false);
    setStreamingAssistantMessage(null);
    setAgentStatus("IDLE");
    setActiveWorkflow(null);
    setWorkflowRunStartedAt(null);
    setAnalysisProgress(null);
  };

  function classifyWorkflowFromPrompt(content: string, previousMessages: Message[]) {
    const normalized = content.toLowerCase();
    if (isLooseConfirmation(normalized)) {
      const pendingWorkflow = inferPendingWorkflowFromMessages(previousMessages);
      if (pendingWorkflow) {
        return pendingWorkflow;
      }
    }

    if (
      [
        "确认开始分析并剪辑",
        "开始分析并剪辑",
        "确认分析并剪辑",
        "确认开始分析并制作",
        "开始分析并制作",
        "确认分析并制作"
      ].some((keyword) =>
        normalized.includes(keyword)
      )
    ) {
      return "ANALYZE_AND_CREATE_STYLED_VIDEO" as const;
    }

    if (
      ["确认开始分析", "开始分析", "执行分析"].some((keyword) =>
        normalized.includes(keyword)
      )
    ) {
      return "ANALYZE_REFERENCE" as const;
    }

    if (
      [
        "确认开始剪辑",
        "开始剪辑",
        "执行剪辑",
        "确认开始生成",
        "确认开始制作",
        "开始制作",
        "执行制作",
        "确认制作",
        "去吧制作",
        "制作吧"
      ].some((keyword) =>
        normalized.includes(keyword)
      )
    ) {
      return "CREATE_STYLED_VIDEO" as const;
    }

    return null;
  }

  const streamAssistantReply = async (assistantMessage: Message) => {
    stopStreaming();
    setIsStreamingAssistant(true);
    setAgentStatus("STREAMING");

    const fullContent = assistantMessage.content;
    const chunks = Array.from(fullContent);

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

        streamTimerRef.current = setTimeout(tick, 58);
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
    const nextWorkflow = classifyWorkflowFromPrompt(normalized, messages);

    const optimisticMessage = buildPendingUserMessage(activeConversationId, normalized);

    setIsSending(true);
    setAgentStatus("THINKING");
    setActiveWorkflow(nextWorkflow);
    setWorkflowRunStartedAt(nextWorkflow ? Date.now() : null);
    setAnalysisProgress(null);
    setError(null);
    setPrompt("");
    setMessages((prev) => [...prev, optimisticMessage]);

    try {
      const response = await sendMessage(
        activeConversationId,
        normalized,
        workspaceContext
      );
      setMessages((prev) => [
        ...prev.filter((message) => message.messageId !== optimisticMessage.messageId),
        response.userMessage
      ]);
      const refreshed = await listConversations(workspaceId ?? undefined);
      setConversations(refreshed);
      setAgentStatus(response.agentStatus || "COMPLETED");
      setWorkflowRunStartedAt(null);
      setAnalysisProgress(null);
      setMessageArtifacts((current) =>
        response.artifacts
          ? {
              ...current,
              [response.assistantMessage.messageId]: response.artifacts
            }
          : current
      );
      await streamAssistantReply(response.assistantMessage);
    } catch (exception) {
      setMessages((prev) =>
        prev.filter((message) => message.messageId !== optimisticMessage.messageId)
      );
      setPrompt(normalized);
      setAgentStatus("FAILED");
      setActiveWorkflow(null);
      setWorkflowRunStartedAt(null);
      setAnalysisProgress(null);
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
          setMessageArtifacts({});
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
    messageArtifacts,
    prompt,
    setPrompt,
    isBooting,
    isLoadingMessages,
    isSending,
    isStreamingAssistant,
    activeWorkflow,
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

function describeWorkflowProgress(
  workflow: ActiveWorkflow,
  elapsedSeconds: number,
  workspaceContext?: AgentWorkspaceContext | null,
  analysisProgress?: WorkspaceAnalysisProgress | null
) {
  const elapsed = formatElapsed(elapsedSeconds);
  const referenceName = workspaceContext?.referenceVideo?.name ?? "参考视频";
  const sourceCount = workspaceContext?.sourceVideos?.length ?? (workspaceContext?.hasSourceVideo ? 1 : 0);

  if (workflow === "ANALYZE_AND_CREATE_STYLED_VIDEO") {
    const analysisStage = analysisProgress?.completed
      ? "参考分析已完成，正在进入 source 分析、剪辑规划和渲染"
      : analysisProgress?.detail ?? "准备参考视频、source 素材和输出目录";
    const phase =
      elapsedSeconds < 20
        ? `准备 ${referenceName} 和 ${sourceCount} 个 source 素材`
        : elapsedSeconds < 120
          ? `正在分析 ${referenceName}：${analysisStage}`
          : elapsedSeconds < 240
            ? `正在分析 ${sourceCount} 个 source 素材，并生成剪辑规划`
            : "正在生成剪辑包并渲染 demo 成片";

    return {
      title: "Analyzing and creating draft",
      source: "AI4Video + Planner",
      detail: `正在先分析参考视频，再剪辑 source demo。\n当前步骤：${phase}\n已运行 ${elapsed}，完成后会自动出现成片结果卡片。`
    };
  }

  if (workflow === "ANALYZE_REFERENCE") {
    const phase = analysisProgress?.detail ?? (
      elapsedSeconds < 12
        ? "准备参考视频和输出目录"
        : elapsedSeconds < 45
          ? "提取音频特征与节奏"
          : elapsedSeconds < 90
            ? "生成转写与语义结构"
            : elapsedSeconds < 150
              ? "分析镜头画面与字幕风格"
              : "汇总风格模板，等待模型/视频处理完成"
    );

    return {
      title: "Analyzing reference video",
      source: "AI4Video",
      detail: `正在分析：${referenceName}\n当前步骤：${phase}\n已运行 ${elapsed}，完成后会自动出现分析结果卡片。`
    };
  }

  const phase =
    elapsedSeconds < 10
      ? "读取参考经验和待剪素材"
    : elapsedSeconds < 35
        ? "调用模型规划片段顺序与节奏"
        : elapsedSeconds < 90
          ? "生成剪辑包、字幕轨道和参考音频"
          : "渲染预览成片";

  return {
    title: "Creating styled draft",
    source: "Native Render",
    detail: `正在按参考风格剪辑 ${sourceCount} 个 source 素材。\n当前步骤：${phase}\n已运行 ${elapsed}，完成后中间预览会自动切到成片。`
  };
}

function formatElapsed(totalSeconds: number) {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  if (minutes === 0) {
    return `${seconds}s`;
  }
  return `${minutes}m ${seconds.toString().padStart(2, "0")}s`;
}

function formatAnalysisProgressChecklist(progress: WorkspaceAnalysisProgress) {
  const done = "已完成";
  const pending = "等待中";
  return [
    `音频 ${progress.step1AudioExists ? done : pending}`,
    `转写 ${progress.step2TranscriptExists ? done : pending}`,
    `视觉 ${progress.step3VisualExists ? done : pending}`,
    `模板 ${progress.elasticTemplateExists ? done : pending}`
  ].join(" · ");
}

function isLooseConfirmation(normalizedContent: string) {
  const confirmationKeywords = [
    "确认",
    "可以",
    "可以的",
    "对的",
    "开始",
    "执行",
    "制作",
    "剪辑",
    "去吧",
    "ok",
    "okay",
    "yes",
    "go"
  ];
  const cancelKeywords = ["取消", "不要", "先别", "等等", "暂停", "stop", "cancel"];
  return (
    confirmationKeywords.some((keyword) => normalizedContent.includes(keyword)) &&
    !cancelKeywords.some((keyword) => normalizedContent.includes(keyword))
  );
}

function inferPendingWorkflowFromMessages(messages: Message[]): ActiveWorkflow | null {
  for (const message of [...messages].reverse()) {
    if (message.role !== "ASSISTANT") {
      continue;
    }

    if (
      message.content.includes("确认开始分析并剪辑") ||
      message.content.includes("确认开始分析并制作")
    ) {
      return "ANALYZE_AND_CREATE_STYLED_VIDEO";
    }
    if (
      message.content.includes("确认开始剪辑") ||
      message.content.includes("确认开始制作")
    ) {
      return "CREATE_STYLED_VIDEO";
    }
    if (message.content.includes("确认开始分析")) {
      return "ANALYZE_REFERENCE";
    }

    return null;
  }

  return null;
}
