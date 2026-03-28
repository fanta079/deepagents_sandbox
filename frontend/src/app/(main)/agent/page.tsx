"use client";

import React, { useState, useRef } from "react";
import { Button, Input, Card, CardContent } from "@/lib/components";
import { Send, Trash2, BotMessageSquare, User as UserIcon } from "lucide-react";
import { chatWithAgent } from "@/lib/api";
import type { AgentMessage } from "@/types";
import { cn } from "@/lib/utils";

export default function AgentPage() {
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const onSubmit = async (content: string) => {
    if (!content.trim()) return;

    const userMessage: AgentMessage = { role: "user", content: content.trim() };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError("");

    try {
      const res = await chatWithAgent({
        messages: [...messages, userMessage],
        backend: "opensandbox",
      });
      const assistantMessage: AgentMessage = { role: "assistant", content: res.message };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      setError(err.response?.data?.detail || "请求失败，请重试");
    } finally {
      setIsLoading(false);
    }
  };

  const clearMessages = () => setMessages([]);

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Agent 对话</h1>
          <p className="text-muted-foreground">与 AI Agent 进行对话交互</p>
        </div>
        <Button variant="outline" size="sm" onClick={clearMessages} disabled={messages.length === 0}>
          <Trash2 className="h-4 w-4 mr-2" />
          清空对话
        </Button>
      </div>

      <Card className="flex-1 flex flex-col overflow-hidden">
        <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
              <BotMessageSquare className="h-12 w-12 mb-4 opacity-50" />
              <p>开始与 Agent 对话吧</p>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={cn("flex gap-3", msg.role === "user" ? "justify-end" : "justify-start")}>
              {msg.role === "assistant" && (
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                  <BotMessageSquare className="h-4 w-4 text-primary" />
                </div>
              )}
              <div
                className={cn(
                  "max-w-[70%] rounded-lg px-4 py-2 text-sm whitespace-pre-wrap",
                  msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"
                )}
              >
                {msg.content}
              </div>
              {msg.role === "user" && (
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center">
                  <UserIcon className="h-4 w-4 text-primary-foreground" />
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                <BotMessageSquare className="h-4 w-4 text-primary animate-pulse" />
              </div>
              <div className="bg-muted rounded-lg px-4 py-2 text-sm">
                <span className="animate-pulse">Agent 正在思考...</span>
              </div>
            </div>
          )}

          {error && (
            <div className="text-sm text-destructive bg-destructive/10 rounded-lg px-4 py-2">{error}</div>
          )}

          <div ref={messagesEndRef} />
        </CardContent>

        <div className="border-t p-4">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              const fd = new FormData(e.currentTarget);
              onSubmit(fd.get("content") as string);
              e.currentTarget.reset();
            }}
            className="flex gap-2"
          >
            <Input name="content" placeholder="输入消息..." autoComplete="off" disabled={isLoading} className="flex-1" />
            <Button type="submit" disabled={isLoading}>
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </div>
      </Card>
    </div>
  );
}
