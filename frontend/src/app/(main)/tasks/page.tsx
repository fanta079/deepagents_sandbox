"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button, Input, Label, Card, CardContent, CardHeader, CardTitle } from "@/lib/components";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { getTasks, createTask, retryTask, cancelTask, deleteTask, getUsers } from "@/lib/api";
import type { TaskResponse, TaskStatus, TaskPriority } from "@/types";

const taskSchema = z.object({
  title: z.string().min(1, "标题不能为空"),
  description: z.string().optional(),
  priority: z.enum(["low", "normal", "high", "urgent"]),
  owner_id: z.string().min(1, "请选择所属用户"),
  tags: z.string().optional(),
});

type TaskFormData = z.infer<typeof taskSchema>;

const statusColors: Record<TaskStatus, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  running: "bg-blue-100 text-blue-800",
  success: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
  cancelled: "bg-gray-100 text-gray-800",
};

const statusLabels: Record<TaskStatus, string> = {
  pending: "等待中",
  running: "运行中",
  success: "成功",
  failed: "失败",
  cancelled: "已取消",
};

const priorityLabels: Record<TaskPriority, string> = {
  low: "低",
  normal: "普通",
  high: "高",
  urgent: "紧急",
};

export default function TasksPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  React.useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 300);
    return () => clearTimeout(timer);
  }, [search]);

  const { data: tasks = [], isLoading } = useQuery({
    queryKey: ["tasks", page, statusFilter, debouncedSearch],
    queryFn: () =>
      getTasks({
        page,
        page_size: 20,
        status: statusFilter !== "all" ? statusFilter : undefined,
        search: debouncedSearch || undefined,
      }),
  });

  const { data: users = [] } = useQuery({
    queryKey: ["users-all"],
    queryFn: () => getUsers({ page_size: 1000 }),
  });

  const retryMutation = useMutation({
    mutationFn: (id: string) => retryTask(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["tasks"] }),
  });

  const cancelMutation = useMutation({
    mutationFn: (id: string) => cancelTask(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["tasks"] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteTask(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["tasks"] }),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">任务队列</h1>
          <p className="text-muted-foreground">管理系统中的所有任务</p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)}>创建任务</Button>
      </div>

      <div className="flex gap-4 flex-wrap">
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="状态筛选" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部状态</SelectItem>
            <SelectItem value="pending">等待中</SelectItem>
            <SelectItem value="running">运行中</SelectItem>
            <SelectItem value="success">成功</SelectItem>
            <SelectItem value="failed">失败</SelectItem>
            <SelectItem value="cancelled">已取消</SelectItem>
          </SelectContent>
        </Select>
        <Input
          placeholder="搜索任务..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-xs"
        />
      </div>

      {isLoading ? (
        <div className="text-center py-8 text-muted-foreground">加载中...</div>
      ) : tasks.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">暂无任务</div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {tasks.map((task) => (
            <Card key={task.id} className="flex flex-col">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="text-base font-medium line-clamp-1">{task.title}</CardTitle>
                  <Badge className={statusColors[task.status]}>{statusLabels[task.status]}</Badge>
                </div>
                <div className="flex gap-2 mt-2">
                  <Badge variant="secondary">{priorityLabels[task.priority]}</Badge>
                  {task.tags?.map((tag) => (
                    <Badge key={tag} variant="outline">{tag}</Badge>
                  ))}
                </div>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col gap-2">
                {task.description && (
                  <p className="text-sm text-muted-foreground line-clamp-2">{task.description}</p>
                )}
                <div className="text-xs text-muted-foreground space-y-1">
                  <div>进度: {task.progress}%</div>
                  <div>重试: {task.retry_count}/{task.max_retries}</div>
                </div>
                {task.error && (
                  <p className="text-xs text-destructive bg-destructive/10 rounded p-2">{task.error}</p>
                )}
                {task.result && (
                  <p className="text-xs text-muted-foreground bg-muted rounded p-2 line-clamp-2">{task.result}</p>
                )}
                <div className="flex gap-2 mt-auto pt-2">
                  {task.status === "failed" && (
                    <Button size="sm" variant="outline" onClick={() => retryMutation.mutate(task.id)} disabled={retryMutation.isPending}>重试</Button>
                  )}
                  {(task.status === "pending" || task.status === "running") && (
                    <Button size="sm" variant="outline" onClick={() => cancelMutation.mutate(task.id)} disabled={cancelMutation.isPending}>取消</Button>
                  )}
                  <Button size="sm" variant="destructive" onClick={() => deleteMutation.mutate(task.id)} disabled={deleteMutation.isPending || task.status === "running"}>删除</Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>上一页</Button>
        <span className="text-sm text-muted-foreground">第 {page} 页</span>
        <Button variant="outline" size="sm" disabled={tasks.length < 20} onClick={() => setPage((p) => p + 1)}>下一页</Button>
      </div>

      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>创建任务</DialogTitle>
            <DialogDescription>填写任务信息</DialogDescription>
          </DialogHeader>
          <TaskForm
            users={users}
            onSubmit={(data) => {
              createTask({
                ...data,
                tags: data.tags ? data.tags.split(",").map((t: string) => t.trim()) : [],
              }).then(() => {
                queryClient.invalidateQueries({ queryKey: ["tasks"] });
                setIsCreateOpen(false);
              });
            }}
            onCancel={() => setIsCreateOpen(false)}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}

function TaskForm({ users, onSubmit, onCancel }: { users: any[]; onSubmit: (data: any) => void; onCancel: () => void }) {
  const [priority, setPriority] = useState("normal");
  const [ownerId, setOwnerId] = useState("");
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<TaskFormData>({
    defaultValues: { priority: "normal" },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-2">
        <Label>任务标题 *</Label>
        <Input {...register("title")} placeholder="输入任务标题" />
        {errors.title && <p className="text-xs text-destructive">{errors.title.message}</p>}
      </div>
      <div className="space-y-2">
        <Label>描述</Label>
        <Input {...register("description")} placeholder="任务描述（可选）" />
      </div>
      <div className="space-y-2">
        <Label>优先级</Label>
        <Select value={priority} onValueChange={setPriority}>
          <SelectTrigger><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="low">低</SelectItem>
            <SelectItem value="normal">普通</SelectItem>
            <SelectItem value="high">高</SelectItem>
            <SelectItem value="urgent">紧急</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div className="space-y-2">
        <Label>所属用户 *</Label>
        <Select value={ownerId} onValueChange={setOwnerId}>
          <SelectTrigger><SelectValue placeholder="选择用户" /></SelectTrigger>
          <SelectContent>
            {users.map((u) => (
              <SelectItem key={u.id} value={u.id}>{u.username}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="space-y-2">
        <Label>标签（逗号分隔）</Label>
        <Input {...register("tags")} placeholder="tag1, tag2" />
      </div>
      <div className="flex justify-end gap-2">
        <Button type="button" variant="outline" onClick={onCancel}>取消</Button>
        <Button type="submit" disabled={isSubmitting || !ownerId}>{isSubmitting ? "创建中..." : "创建"}</Button>
      </div>
    </form>
  );
}
