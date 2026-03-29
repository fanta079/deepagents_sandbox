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
import { useTranslation } from "@/i18n/I18nProvider";

export default function DashboardPage() {
  const { t } = useTranslation();
  const { data: stats, isLoading } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: getDashboardStats,
    refetchInterval: 30000,
  });

  const cards = [
    {
      titleKey: "dashboard.totalUsers" as const,
      value: stats?.user_count ?? "-",
      icon: Users,
      color: "text-blue-600",
      bg: "bg-blue-50",
    },
    {
      titleKey: "dashboard.totalTasks" as const,
      value: stats?.task_count ?? "-",
      icon: ListChecks,
      color: "text-green-600",
      bg: "bg-green-50",
    },
    {
      titleKey: "dashboard.agentStatus" as const,
      value: stats?.agent_status === "ok" ? t("common.online") : t("common.offline"),
      icon: BotMessageSquare,
      color: stats?.agent_status === "ok" ? "text-green-600" : "text-red-600",
      bg: stats?.agent_status === "ok" ? "bg-green-50" : "bg-red-50",
    },
  ];

  const shortcuts = [
    { labelKey: "nav.users" as const, href: "/users", icon: Users, descKey: "dashboard.manageUsers" as const },
    { labelKey: "nav.tasks" as const, href: "/tasks", icon: ListChecks, descKey: "dashboard.manageTasks" as const },
    { labelKey: "nav.agent" as const, href: "/agent", icon: BotMessageSquare, descKey: "dashboard.chatWithAgent" as const },
    { labelKey: "nav.files" as const, href: "/files", icon: LayoutDashboard, descKey: "dashboard.manageFiles" as const },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">{t("dashboard.title")}</h1>
        <p className="text-muted-foreground mt-1 text-sm sm:text-base">{t("dashboard.welcome")}</p>
      </div>

      <div className="grid gap-3 sm:gap-4 grid-cols-1 sm:grid-cols-2 md:grid-cols-3">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <Card key={card.titleKey}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{t(card.titleKey)}</CardTitle>
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
        <h2 className="text-lg font-semibold mb-3">{t("dashboard.shortcuts")}</h2>
        <div className="grid gap-3 sm:gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
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
                        <div className="font-medium">{t(s.labelKey)}</div>
                        <div className="text-xs text-muted-foreground">{t(s.descKey)}</div>
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
