"use client";

import { AppSidebar } from "./AppSidebar";
import { TopBar } from "./TopBar";

export function StandardPage({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen bg-neutral-950">
      <AppSidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}