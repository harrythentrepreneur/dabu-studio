"use client";

import { ShieldUser, User, Clapperboard, Image as ImageIcon } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { useAdminPermission } from "../app/admin/hooks/useAdminPermission";
import { cn } from "../lib/utils";
import UserButton from "./user-button";

export function AppSidebar() {
  const pathname = usePathname();
  const { isAdmin } = useAdminPermission();
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div
      className={cn(
        "flex flex-col items-start justify-between h-dvh p-2 py-3 bg-neutral-900 border-r border-neutral-850 gap-3 transition-all duration-1s00",
        isExpanded ? "w-44" : "w-[45px]"
      )}
      onMouseEnter={() => setIsExpanded(true)}
      onMouseLeave={() => setIsExpanded(false)}
    >
      <div className="flex flex-col items-start gap-2">
        <Link href="/" className="mb-3 mt-1 ml-0.5 flex items-center justify-center">
          <Image src="/Vector.svg" alt="Logo" width={24} height={18} />
        </Link>
        <SidebarLink
          href="/"
          icon={<Clapperboard className="w-5 h-5" />}
          label="Toolkit"
          active={true}
          expanded={isExpanded}
        />
        {isAdmin && (
          <SidebarLink
            href="/admin"
            icon={<ShieldUser className="w-5 h-5" />}
            label="Admin"
            active={pathname.startsWith("/admin")}
            expanded={isExpanded}
          />
        )}
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
  expanded = false,
}: {
  active?: boolean;
  href: string;
  icon?: React.ReactNode;
  label?: string;
  expanded?: boolean;
}) {
  return (
    <Link href={href} className="focus:outline-none">
      <div
        className={cn(
          "p-1 rounded-md transition-all duration-200 flex items-center gap-2",
          active ? "bg-neutral-800 text-white" : "text-neutral-400 hover:text-white hover:bg-neutral-800/80"
          // expanded ? "w-40" : "w-12"
        )}
      >
        <div className="flex items-center justify-center w-5 h-5 flex-shrink-0">{icon}</div>
        {expanded && label && (
          <span className="text-sm font-medium whitespace-nowrap overflow-hidden w-[120px]">{label}</span>
        )}
      </div>
    </Link>
  );
}
