"use client";

import { Sparkles, Zap, Image as ImageIcon, Gauge, Video, Music, Copy } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { cn } from "../lib/utils";
import UserButton from "./user-button";

export function AppSidebar() {
  const pathname = usePathname();
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div
      className={cn(
        "flex flex-col items-start justify-between h-dvh p-2 py-3 bg-neutral-900 border-r border-neutral-850 gap-3 transition-all duration-200",
        isExpanded ? "w-56" : "w-[45px]"
      )}
      onMouseEnter={() => setIsExpanded(true)}
      onMouseLeave={() => setIsExpanded(false)}
    >
      <div className="flex flex-col items-start gap-2 w-full overflow-y-auto">
        <Link href="/" className="mb-3 mt-1 ml-0.5 flex items-center justify-center">
          <div className="w-7 h-7 flex items-center justify-center">
            <Image 
              src="/Vector.svg" 
              alt="Logo" 
              width={24} 
              height={26}
              className="w-auto h-auto"
            />
          </div>
        </Link>
        
        {/* Ad Workshop */}
        {isExpanded && (
          <div className="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-1 px-1">Ad Workshop</div>
        )}
        <SidebarLink
          href="/express-builder"
          icon={<Sparkles className="w-5 h-5" />}
          label="Express Builder"
          active={pathname === "/express-builder"}
          expanded={isExpanded}
        />
        <SidebarLink
          href="/gif-studio"
          icon={<ImageIcon className="w-5 h-5" />}
          label="GIF Studio"
          active={pathname === "/gif-studio"}
          expanded={isExpanded}
        />
        
        {/* Campaign Factory */}
        {isExpanded && (
          <div className="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-1 px-1 mt-3">Campaign Factory</div>
        )}
        <SidebarLink
          href="/322-engine"
          icon={<Gauge className="w-5 h-5" />}
          label="3:2:2 Engine"
          active={pathname === "/322-engine"}
          expanded={isExpanded}
          disabled={true}
        />
        <SidebarLink
          href="/quick-create"
          icon={<Zap className="w-5 h-5" />}
          label="Quick Create"
          beta={true}
          active={pathname === "/quick-create"}
          expanded={isExpanded}
        />
        <SidebarLink
          href="/hook-optimizer"
          icon={<Video className="w-5 h-5" />}
          label="Hook Optimizer"
          subtitle="w/ VEO3 options"
          active={pathname === "/hook-optimizer"}
          expanded={isExpanded}
          disabled={true}
        />
        
        {/* Creative Assets */}
        {isExpanded && (
          <div className="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-1 px-1 mt-3">Creative Assets</div>
        )}
        <SidebarLink
          href="/trending-audio"
          icon={<Music className="w-5 h-5" />}
          label="Trending Audio"
          active={pathname === "/trending-audio"}
          expanded={isExpanded}
        />
        <SidebarLink
          href="/ad-replica"
          icon={<Copy className="w-5 h-5" />}
          label="Ad Replica"
          active={pathname === "/ad-replica"}
          expanded={isExpanded}
          disabled={true}
        />
      </div>
      <div className="flex flex-col gap-2">
        {isExpanded ? (
          <div className="px-2">
            <UserButton />
          </div>
        ) : (
          <div className="flex justify-center p-1">
            <UserButton />
          </div>
        )}
      </div>
    </div>
  );
}

function SidebarLink({
  active = false,
  href,
  icon,
  label,
  subtitle,
  expanded = false,
  beta = false,
  disabled = false,
}: {
  active?: boolean;
  href: string;
  icon?: React.ReactNode;
  label?: string;
  subtitle?: string;
  expanded?: boolean;
  beta?: boolean;
  disabled?: boolean;
}) {
  const content = (
    <div
      className={cn(
        "p-1 rounded-md transition-all duration-200 flex items-center gap-2",
        disabled 
          ? "opacity-30 cursor-not-allowed text-neutral-600" 
          : active 
            ? "bg-neutral-800 text-white" 
            : "text-neutral-400 hover:text-white hover:bg-neutral-800/80"
      )}
    >
      <div className="flex items-center justify-center w-5 h-5 flex-shrink-0">{icon}</div>
      {expanded && label && (
        <div className="flex flex-col flex-1">
          <div className="flex items-center gap-1.5">
            <span className="text-sm font-medium whitespace-nowrap">{label}</span>
            {beta && (
              <span className="text-[10px] px-1 py-0.5 bg-blue-500/20 text-blue-400 rounded font-medium">beta</span>
            )}
          </div>
          {subtitle && (
            <span className="text-[10px] text-neutral-500 whitespace-nowrap">{subtitle}</span>
          )}
        </div>
      )}
    </div>
  );

  if (disabled) {
    return <div className="w-full">{content}</div>;
  }

  return (
    <Link href={href} className="focus:outline-none w-full">
      {content}
    </Link>
  );
}