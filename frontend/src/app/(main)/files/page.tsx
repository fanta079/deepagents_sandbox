"use client";

import React, { useState, useRef } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Button, Card, CardContent } from "@/lib/components";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Upload, Download, Trash2, FileIcon, FileText, Image } from "lucide-react";
import { api, uploadFile, deleteFile, downloadFile } from "@/lib/api";

interface FileInfo {
  filename: string;
  original_filename: string;
  size: number;
  url: string;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function getFileIcon(filename: string) {
  const ext = filename.split(".").pop()?.toLowerCase();
  if (["jpg", "jpeg", "png", "gif", "bmp", "webp"].includes(ext || "")) {
    return <Image className="h-8 w-8 text-blue-500" />;
  }
  if (["pdf", "doc", "docx", "txt", "csv", "json", "xml"].includes(ext || "")) {
    return <FileText className="h-8 w-8 text-green-500" />;
  }
  return <FileIcon className="h-8 w-8 text-gray-500" />;
}

export default function FilesPage() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});
  const [deleteFileName, setDeleteFileName] = useState<string | null>(null);
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const loadFiles = async () => {
    setIsLoading(true);
    try {
      const res = await api.get<any[]>("/api/v1/files/");
      setFiles(res.data);
    } catch {
      setFiles([]);
    }
    setIsLoading(false);
  };

  React.useEffect(() => {
    loadFiles();
  }, []);

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      setUploadProgress((p) => ({ ...p, [file.name]: 0 }));
      const res = await api.post<FileInfo>("/api/v1/files/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (e) => {
          if (e.total) {
            setUploadProgress((p) => ({ ...p, [file.name]: Math.round((e.loaded * 100) / (e.total ?? 1)) }));
          }
        },
      });
      return res.data;
    },
    onSuccess: () => {
      setUploadProgress({});
      loadFiles();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (filename: string) => deleteFile(filename),
    onSuccess: () => {
      setDeleteFileName(null);
      loadFiles();
    },
  });

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = e.target.files;
    if (!selectedFiles) return;
    Array.from(selectedFiles).forEach((file) => {
      uploadMutation.mutate(file);
    });
    e.target.value = "";
  };

  const handleDownload = (filename: string, originalFilename: string) => {
    const url = downloadFile(filename);
    const a = document.createElement("a");
    a.href = url;
    a.download = originalFilename;
    a.click();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">文件管理</h1>
          <p className="text-muted-foreground">上传和管理文件资源</p>
        </div>
        <div>
          <input ref={fileInputRef} type="file" multiple className="hidden" onChange={handleFileSelect} />
          <Button onClick={() => fileInputRef.current?.click()} disabled={uploadMutation.isPending}>
            <Upload className="h-4 w-4 mr-2" />
            {uploadMutation.isPending ? "上传中..." : "上传文件"}
          </Button>
        </div>
      </div>

      {Object.keys(uploadProgress).length > 0 && (
        <Card>
          <CardContent className="space-y-2 pt-4">
            {Object.entries(uploadProgress).map(([name, progress]) => (
              <div key={name} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span>{name}</span>
                  <span>{progress}%</span>
                </div>
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <div className="h-full bg-primary transition-all" style={{ width: `${progress}%` }} />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-8 text-center text-muted-foreground">加载中...</div>
          ) : files.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              <FileIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>暂无文件</p>
              <p className="text-sm mt-1">点击上传按钮添加文件</p>
            </div>
          ) : (
            <div className="divide-y">
              {files.map((file) => (
                <div key={file.filename} className="flex items-center gap-4 p-4 hover:bg-muted/30">
                  {getFileIcon(file.original_filename || file.filename)}
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate">{file.original_filename || file.filename}</div>
                    <div className="text-xs text-muted-foreground">{formatSize(file.size)}</div>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => handleDownload(file.filename, file.original_filename)}>
                      <Download className="h-4 w-4" />
                    </Button>
                    <Button size="sm" variant="destructive" onClick={() => setDeleteFileName(file.filename)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={!!deleteFileName} onOpenChange={() => setDeleteFileName(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认删除</DialogTitle>
            <DialogDescription>确定要删除此文件吗？此操作无法撤销。</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteFileName(null)}>取消</Button>
            <Button variant="destructive" onClick={() => deleteFileName && deleteMutation.mutate(deleteFileName)} disabled={deleteMutation.isPending}>
              {deleteMutation.isPending ? "删除中..." : "确认删除"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
