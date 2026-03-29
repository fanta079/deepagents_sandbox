import type { MetadataRoute } from "next";

/**
 * PWA Manifest 加载
 *
 * Next.js 会自动从 `/manifest.json` 加载 PWA 配置
 * 此文件导出 manifest 以支持 TypeScript 类型检查和 IDE 提示
 */
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "DeepAgents",
    short_name: "DeepAgents",
    description: "Multi-sandbox backend AI Agent service",
    start_url: "/",
    display: "standalone",
    background_color: "#0d1117",
    theme_color: "#58a6ff",
    icons: [
      {
        src: "/icon-192.png",
        sizes: "192x192",
        type: "image/png",
      },
      {
        src: "/icon-512.png",
        sizes: "512x512",
        type: "image/png",
      },
    ],
  };
}
