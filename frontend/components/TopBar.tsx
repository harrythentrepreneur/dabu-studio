"use client";

import UserButton from "./user-button";

export function TopBar() {
  return (
    <div className="h-12 border-b border-neutral-850 flex items-center justify-between px-4">
      <div className="text-lg font-semibold">Dabu</div>
      <UserButton />
    </div>
  );
}