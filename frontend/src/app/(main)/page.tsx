"use client";

import React from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  Users,
  ListChecks,
  BotMessageSquare,
  LayoutDashboard,
  ArrowRight,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/lib/components";
import { getDashboardStats } from "@/lib/api";

export default function DashboardPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: getDashboardStats,
    refetchInterval: 30000,
  });

  const cards = [
    {
      title: "用户总数",
      value: stats?.user_count ?? "-",
      icon: Users,
      color: "text-blue-600",
      bg: "bg-blue-50",
    },
    {
      title: "任务总数",
      value: stats?.task_count ?? "-",
      icon: ListChecks,
      color: "text-green-600",
      bg: "bg-green-50",
    },
    {
      title: "Agent 状态",
      value: stats?.agent_status === "ok" ? "在线" : "离线",
      icon: BotMessageSquare,
      color: stats?.agent_status === "ok" ? "text-green-600" : "text-red-600",
      bg: stats?.agent_status === "ok" ? "bg-green-50" : "bg-red-50",
    },
  ];

  const shortcuts = [
    { label: "用户管理", href: "/users", icon: Users, desc: "管理所有用户" },
    { label: "任务队列", href: "/tasks", icon: ListChecks, desc: "查看和处理任务" },
    { label: "Agent 对话", href: "/agent", icon: BotMessageSquare, desc: "与 AI Agent 对话" },
    { label: "文件管理", href: "/files", icon: LayoutDashboard, desc: "上传和下载文件" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">仪表盘</h1>
        <p className="text-muted-foreground mt-1">欢迎使用 DeepAgents 管理后台</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <Card key={card.title}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{card.title}</CardTitle>
                <div className={`rounded-full p-2 ${card.bg}`}>
                  <Icon className={`h-4 w-4 ${card.color}`} />
                </div>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <div className="h-8 w-16 animate-pulse rounded bg-muted" />
                ) : (
                  <div className="text-2xl font-bold">{card.value}</div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div>
        <h2 className="text-lg font-semibold mb-3">快捷入口</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {shortcuts.map((s) => {
            const Icon = s.icon;
            return (
              <Link key={s.href} href={s.href}>
                <Card className="hover:bg-accent/50 transition-colors cursor-pointer">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="rounded-full bg-primary/10 p-2">
                        <Icon className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <div className="font-medium">{s.label}</div>
                        <div className="text-xs text-muted-foreground">{s.desc}</div>
                      </div>
                      <ArrowRight className="ml-auto h-4 w-4 text-muted-foreground" />
                    </div>
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
