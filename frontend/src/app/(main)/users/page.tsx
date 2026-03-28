"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button, Input, Label, Card, CardContent } from "@/lib/components";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { getUsers, createUser, updateUser, deleteUser } from "@/lib/api";
import type { UserResponse, UserCreate, UserUpdate } from "@/types";

function format(dateStr: string): string {
  if (!dateStr) return "-";
  try {
    const d = new Date(dateStr);
    return d.toLocaleString("zh-CN");
  } catch {
    return dateStr;
  }
}

const userSchema = z.object({
  username: z.string().min(3),
  email: z.string().email(),
  full_name: z.string().optional(),
  password: z.string().min(6).optional(),
  is_active: z.boolean().optional(),
});

type UserFormData = z.infer<typeof userSchema>;

export default function UsersPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<UserResponse | null>(null);

  React.useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 300);
    return () => clearTimeout(timer);
  }, [search]);

  const { data: users = [], isLoading } = useQuery({
    queryKey: ["users", page, debouncedSearch],
    queryFn: () => getUsers({ page, page_size: 20, search: debouncedSearch }),
  });

  const createMutation = useMutation({
    mutationFn: (data: UserCreate) => createUser(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      setIsCreateOpen(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: UserUpdate }) => updateUser(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      setIsEditOpen(false);
      setSelectedUser(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteUser(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      setIsDeleteOpen(false);
      setSelectedUser(null);
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">用户管理</h1>
          <p className="text-muted-foreground">管理系统中的所有用户</p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)}>创建用户</Button>
      </div>

      <div className="flex gap-4">
        <Input
          placeholder="搜索用户名..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-xs"
        />
      </div>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-8 text-center text-muted-foreground">加载中...</div>
          ) : users.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">暂无用户</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="px-4 py-3 text-left font-medium">用户名</th>
                    <th className="px-4 py-3 text-left font-medium">邮箱</th>
                    <th className="px-4 py-3 text-left font-medium">姓名</th>
                    <th className="px-4 py-3 text-left font-medium">状态</th>
                    <th className="px-4 py-3 text-left font-medium">创建时间</th>
                    <th className="px-4 py-3 text-right font-medium">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => (
                    <tr key={user.id} className="border-b hover:bg-muted/30">
                      <td className="px-4 py-3 font-medium">{user.username}</td>
                      <td className="px-4 py-3 text-muted-foreground">{user.email}</td>
                      <td className="px-4 py-3">{user.full_name || "-"}</td>
                      <td className="px-4 py-3">
                        <Badge variant={user.is_active ? "success" : "destructive"}>
                          {user.is_active ? "激活" : "禁用"}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">{format(user.created_at)}</td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex justify-end gap-2">
                          <Button size="sm" variant="outline" onClick={() => { setSelectedUser(user); setIsEditOpen(true); }}>
                            编辑
                          </Button>
                          <Button size="sm" variant="destructive" onClick={() => { setSelectedUser(user); setIsDeleteOpen(true); }}>
                            删除
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>上一页</Button>
        <span className="text-sm text-muted-foreground">第 {page} 页</span>
        <Button variant="outline" size="sm" disabled={users.length < 20} onClick={() => setPage((p) => p + 1)}>下一页</Button>
      </div>

      {/* Create Dialog */}
      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>创建用户</DialogTitle>
            <DialogDescription>填写用户信息创建新账号</DialogDescription>
          </DialogHeader>
          <UserForm
            onSubmit={(data) => createMutation.mutate({ ...data, password: data.password! })}
            onCancel={() => setIsCreateOpen(false)}
            isLoading={createMutation.isPending}
          />
        </DialogContent>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>编辑用户</DialogTitle>
            <DialogDescription>修改用户信息</DialogDescription>
          </DialogHeader>
          {selectedUser && (
            <UserForm
              initialData={selectedUser}
              onSubmit={(data) => updateMutation.mutate({ id: selectedUser.id, data })}
              onCancel={() => { setIsEditOpen(false); setSelectedUser(null); }}
              isLoading={updateMutation.isPending}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Delete Dialog */}
      <Dialog open={isDeleteOpen} onOpenChange={setIsDeleteOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认删除</DialogTitle>
            <DialogDescription>
              确定要删除用户 <strong>{selectedUser?.username}</strong> 吗？此操作无法撤销。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDeleteOpen(false)}>取消</Button>
            <Button variant="destructive" onClick={() => selectedUser && deleteMutation.mutate(selectedUser.id)} disabled={deleteMutation.isPending}>
              {deleteMutation.isPending ? "删除中..." : "确认删除"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function UserForm({
  initialData,
  onSubmit,
  onCancel,
  isLoading,
}: {
  initialData?: UserResponse;
  onSubmit: (data: any) => void;
  onCancel: () => void;
  isLoading: boolean;
}) {
  const { register, handleSubmit, formState: { errors } } = useForm<UserFormData>({
    defaultValues: {
      username: initialData?.username || "",
      email: initialData?.email || "",
      full_name: initialData?.full_name || "",
      password: "",
      is_active: initialData?.is_active ?? true,
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-2">
        <Label>用户名</Label>
        <Input {...register("username")} placeholder="用户名" disabled={!!initialData} />
        {errors.username && <p className="text-xs text-destructive">{errors.username.message}</p>}
      </div>
      <div className="space-y-2">
        <Label>邮箱</Label>
        <Input {...register("email")} type="email" placeholder="邮箱" />
        {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
      </div>
      <div className="space-y-2">
        <Label>姓名</Label>
        <Input {...register("full_name")} placeholder="姓名（可选）" />
      </div>
      <div className="space-y-2">
        <Label>{initialData ? "新密码（留空不修改）" : "密码"}</Label>
        <Input {...register("password")} type="password" placeholder="密码" />
        {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
      </div>
      <div className="flex justify-end gap-2">
        <Button type="button" variant="outline" onClick={onCancel}>取消</Button>
        <Button type="submit" disabled={isLoading}>{isLoading ? "保存中..." : "保存"}</Button>
      </div>
    </form>
  );
}
