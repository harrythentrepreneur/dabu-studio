"use client";
import {
  Settings,
  Sparkles,
  Zap,
  Image as ImageIcon,
  Gauge,
  Video,
  Music,
  Copy,
} from "lucide-react";
import { usePathname } from "next/navigation";
import { Sidebar as SidebarComponents } from "./sidebar/Sidebar";

export function MainSidebar() {
  const pathname = usePathname();

  // Check which tab is active based on the current path
  const getTabPath = (tabName: string) => {
    return `/${tabName.toLowerCase()}`;
  };

  const isActiveTab = (tabName: string) => {
    const route = pathname.substring(1).split('/')[0];
    return route === tabName.toLowerCase();
  };

  return (
    <div className="w-56 bg-neutral-900 border-r border-neutral-850 flex flex-col h-dvh">
      <div className="flex flex-col p-4 border-b border-neutral-800">
        <div className="text-base font-medium text-white opacity-85">Dabu.ai Ad Assistant</div>
      </div>
      <div className="flex flex-col p-3 pt-1">
        <SidebarComponents.SectionHeader>Campaign Factory</SidebarComponents.SectionHeader>
        <SidebarComponents.Item
          label="3:2:2 Engine"
          active={isActiveTab("322-engine")}
          href={getTabPath("322-engine")}
          icon={<Gauge className="w-4 h-4" />}
          disabled={true}
        />
        <SidebarComponents.Item
          label="Hook Optimizer"
          subtitle="w/ VEO3 options"
          active={isActiveTab("hook-optimizer")}
          href={getTabPath("hook-optimizer")}
          icon={<Video className="w-4 h-4" />}
          disabled={true}
        />
        
        <SidebarComponents.SectionHeader>Ad Workshop</SidebarComponents.SectionHeader>
        <SidebarComponents.Item
          label="Express Builder"
          active={isActiveTab("express-builder")}
          href={getTabPath("express-builder")}
          icon={<Sparkles className="w-4 h-4" />}
        />
        <SidebarComponents.Item
          label="Quick Create"
          badge="beta"
          active={isActiveTab("quick-create")}
          href={getTabPath("quick-create")}
          icon={<Zap className="w-4 h-4" />}
        />
        <SidebarComponents.Item
          label="Ad Replica"
          active={isActiveTab("ad-replica")}
          href={getTabPath("ad-replica")}
          icon={<Copy className="w-4 h-4" />}
          disabled={true}
        />
        
        <SidebarComponents.SectionHeader>Creative Assets</SidebarComponents.SectionHeader>
        <SidebarComponents.Item
          label="GIF Matcher"
          active={isActiveTab("gif-studio")}
          href={getTabPath("gif-studio")}
          icon={<ImageIcon className="w-4 h-4" />}
        />
        <SidebarComponents.Item
          label="Trending Audio"
          active={isActiveTab("trending-audio")}
          href={getTabPath("trending-audio")}
          icon={<Music className="w-4 h-4" />}
        />
        <SidebarComponents.Item
          label="Clip Matcher"
          active={isActiveTab("clip-studio")}
          href={getTabPath("clip-studio")}
          icon={<Video className="w-4 h-4" />}
        />
      </div>
    </div>
  );
}