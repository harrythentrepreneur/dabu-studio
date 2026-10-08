"use client";
import { useWindowSize } from "@uidotdev/usehooks";
import { usePathname } from "next/navigation";
import { AppSidebar } from "./RybbitAppSidebar";
import { TopBar } from "./TopBar";
import { Footer } from "../app/components/Footer";
import { MainSidebar } from "./MainSidebar";

export function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { width } = useWindowSize();

  if (width && width < 768) {
    return (
      <div>
        <TopBar />
        <div>{children}</div>
      </div>
    );
  }

  return (
    <div className="flex flex-row h-dvh">
      <AppSidebar />
      <div className="flex flex-1 overflow-hidden">
        <div className="hidden md:flex">
          <MainSidebar />
        </div>
        <div className="flex-1 overflow-auto">
          <div>
            <TopBar />
            <div>{children}</div>
            {!pathname.includes("/map") && !pathname.includes("/realtime") && !pathname.includes("/replay") && (
              <Footer />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}