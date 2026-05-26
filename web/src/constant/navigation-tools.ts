import { FileText, ImagePlus, Images, Maximize2, Video } from "lucide-react";

export const navigationTools = [
    {
        slug: "canvas",
        label: "项目画布",
        icon: Maximize2,
    },
    {
        slug: "image",
        label: "AI生图",
        icon: ImagePlus,
    },
    {
        slug: "video",
        label: "AI视频",
        icon: Video,
    },
    {
        slug: "prompts",
        label: "案例提示词",
        icon: FileText,
    },
    {
        slug: "assets",
        label: "项目素材",
        icon: Images,
    },
] as const;

export type NavigationToolSlug = (typeof navigationTools)[number]["slug"];
