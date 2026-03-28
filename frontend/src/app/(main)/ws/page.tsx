"use client";

import React, { useState, useEffect, useRef } from "react";
import { io, Socket } from "socket.io-client";
import { Button, Input, Card, CardContent } from "@/lib/components";
import { Send, Users } from "lucide-react";
import type { WSMessage } from "@/types";
import { cn } from "@/lib/utils";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

export default function WsPage() {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [messages, setMessages] = useState<WSMessage[]>([]);
  const [input, setInput] = useState("");
  const [username, setUsername] = useState("");
  const [isConnected, setIsConnected] = useState(false);
  const [onlineCount, setOnlineCount] = useState(0);
  const [showLogin, setShowLogin] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const connect = (name: string) => {
    if (!name.trim()) return;
    const userName = name.trim();
    setUsername(userName);

    const newSocket = io(WS_URL, {
      path: "/ws",
      query: { user_id: userName },
      transports: ["websocket"],
    });

    newSocket.on("connect", () => setIsConnected(true));
    newSocket.on("disconnect", () => setIsConnected(false));

    newSocket.on("message", (data: string) => {
      try {
        setMessages((prev) => [...prev, JSON.parse(data)]);
      } catch {
        setMessages((prev) => [...prev, { type: "message", user_id: "unknown", content: data, timestamp: new Date().toISOString() }]);
      }
    });

    newSocket.on("system", (data: string) => {
      try {
        const msg = JSON.parse(data) as WSMessage;
        setMessages((prev) => [...prev, msg]);
        const match = msg.content.match(/(\d+) 人/);
        if (match) setOnlineCount(parseInt(match[1]));
      } catch {
        setMessages((prev) => [...prev, { type: "system", content: data, timestamp: new Date().toISOString() }]);
      }
    });

    newSocket.on("personal", (data: string) => {
      try {
        setMessages((prev) => [...prev, JSON.parse(data)]);
      } catch {}
    });

    newSocket.on("connect_error", () => setIsConnected(false));

    setSocket(newSocket);
    setShowLogin(false);
  };

  const sendMessage = () => {
    if (!input.trim() || !socket) return;
    socket.emit("message", JSON.stringify({ type: "message", content: input.trim() }));
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  useEffect(() => {
    return () => { socket?.disconnect(); };
  }, [socket]);

  if (showLogin) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-8rem)]">
        <Card className="w-full max-w-md">
          <CardContent className="space-y-4 pt-6">
            <p className="text-sm text-muted-foreground text-center">输入用户名以加入 WebSocket 聊天</p>
            <div className="flex gap-2">
              <Input
                placeholder="输入用户名..."
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && connect(username)}
              />
              <Button onClick={() => connect(username)}>加入</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">WebSocket 聊天室</h1>
          <p className="text-muted-foreground">
            用户: <strong>{username}</strong> ·{" "}
            <span className={isConnected ? "text-green-600" : "text-red-600"}>
              {isConnected ? "已连接" : "未连接"}
            </span>
          </p>
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Users className="h-4 w-4" />
          {onlineCount} 人在线
        </div>
      </div>

      <Card className="flex-1 flex flex-col overflow-hidden">
        <CardContent className="flex-1 overflow-y-auto p-4 space-y-2">
          {messages.map((msg, i) => {
            if (msg.type === "system") {
              return (
                <div key={i} className="flex justify-center">
                  <span className="text-xs text-muted-foreground bg-muted rounded px-2 py-1">{msg.content}</span>
                </div>
              );
            }
            const isOwn = msg.user_id === username || msg.from === username;
            return (
              <div key={i} className={cn("flex flex-col", isOwn ? "items-end" : "items-start")}>
                <div className="text-xs text-muted-foreground mb-1">{isOwn ? "你" : msg.user_id || msg.from}</div>
                <div className={cn("max-w-[70%] rounded-lg px-3 py-2 text-sm whitespace-pre-wrap", isOwn ? "bg-primary text-primary-foreground" : "bg-muted")}>
                  {msg.content}
                </div>
              </div>
            );
          })}
          <div ref={messagesEndRef} />
        </CardContent>

        <div className="border-t p-4">
          <div className="flex gap-2">
            <Input
              placeholder="输入消息..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={!isConnected}
            />
            <Button onClick={sendMessage} disabled={!isConnected || !input.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
