"use client";

import { useWindowSize } from "@uidotdev/usehooks";
import { usePathname } from "next/navigation";
import { AppSidebar } from "../../components/AppSidebar";
import { TopBar } from "../../components/TopBar";
import { SubHeader } from "../../components/SubHeader";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { width } = useWindowSize();

  if (width && width < 768) {
    return (
      <div>
        <TopBar />
        <div className="px-4 py-2">
          <SubHeader />
        </div>
        <div className="px-4">{children}</div>
      </div>
    );
  }

  return (
    <div className="flex flex-row h-dvh">
      <AppSidebar />
      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 overflow-auto">
          <div className="px-4 py-2 max-w-[1400px] mx-auto w-full">
            <SubHeader />
            <div className="mt-4">{children}</div>
          </div>
        </div>
      </div>
    </div>
  );
}