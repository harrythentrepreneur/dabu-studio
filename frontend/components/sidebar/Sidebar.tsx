"use client";
import Link from "next/link";
import { cn } from "../../lib/utils";

function Root({ children }: { children: React.ReactNode }) {
  return <div className="w-56 bg-neutral-900 border-r border-neutral-850 flex flex-col">{children}</div>;
}

function Title({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col p-3 pt-4 border-b border-neutral-800">
      <div className="text-base text-neutral-100 mx-1 font-medium">{children}</div>
    </div>
  );
}

function SectionHeader({ children }: { children: React.ReactNode }) {
  return <div className="text-xs text-neutral-400 mt-3 mb-1 mx-3 font-medium">{children}</div>;
}

function Items({ children }: { children: React.ReactNode }) {
  return <div className="flex flex-col p-3">{children}</div>;
}

// Sidebar Link component
function Item({
  label,
  active = false,
  href,
  icon,
  badge,
  subtitle,
  disabled = false,
}: {
  label: string;
  active?: boolean;
  href: string;
  icon?: React.ReactNode;
  badge?: string;
  subtitle?: string;
  disabled?: boolean;
}) {
  if (disabled) {
    return (
      <div className="relative group">
        <div
          className={cn(
            "px-3 py-2 rounded-lg transition-all duration-200 w-full opacity-60 cursor-not-allowed",
            "text-neutral-400 group-hover:blur-[1px]"
          )}
        >
          <div className="flex items-center gap-2">
            {icon}
            <div className="flex flex-col">
              <div className="flex items-center gap-1.5">
                <span className="text-sm">{label}</span>
                {badge && (
                  <span className="text-[10px] px-1 py-0.5 bg-blue-500/20 text-blue-400 rounded font-medium">
                    {badge}
                  </span>
                )}
              </div>
              {subtitle && (
                <span className="text-[10px] text-neutral-500">{subtitle}</span>
              )}
            </div>
          </div>
        </div>
        <div className="absolute inset-y-0 right-2 flex items-center opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
          <span className="text-[10px] text-neutral-400 bg-neutral-800/90 px-2 py-1 rounded backdrop-blur-sm">
            Coming Soon
          </span>
        </div>
      </div>
    );
  }

  return (
    <Link href={href} className="focus:outline-none">
      <div
        className={cn(
          "px-3 py-2 rounded-lg transition-colors w-full",
          active ? "bg-neutral-800 text-white" : "text-neutral-200 hover:text-white hover:bg-neutral-800/50"
        )}
      >
        <div className="flex items-center gap-2">
          {icon}
          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span className="text-sm">{label}</span>
              {badge && (
                <span className="text-[10px] px-1 py-0.5 bg-blue-500/20 text-blue-400 rounded font-medium">
                  {badge}
                </span>
              )}
            </div>
            {subtitle && (
              <span className="text-[10px] text-neutral-500">{subtitle}</span>
            )}
          </div>
        </div>
      </div>
    </Link>
  );
}

export const Sidebar = { Root, Title, Item, Items, SectionHeader };
