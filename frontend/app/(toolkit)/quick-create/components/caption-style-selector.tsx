"use client";

import { cn } from "@/lib/utils";
import { Flame } from "lucide-react";

interface CaptionStyle {
  id: string;
  name: string;
  preview: string;
  className: string;
  hasIcon?: boolean;
}

const captionStyles: CaptionStyle[] = [
  {
    id: "1",
    name: "Yellow Bold",
    preview: "QUICK",
    className: "font-bold text-yellow-400"
  },
  {
    id: "2", 
    name: "White Bold",
    preview: "QUICK",
    className: "font-bold text-white"
  },
  {
    id: "3",
    name: "Yellow Small",
    preview: "THE QUICK", 
    className: "font-bold text-yellow-400 text-[10px]"
  },
  {
    id: "4",
    name: "Green Style",
    preview: "The",
    className: "font-normal text-green-400"
  },
  {
    id: "5",
    name: "White Regular",
    preview: "brown fox",
    className: "font-medium text-white text-[10px]"
  },
  {
    id: "6", 
    name: "White Heavy",
    preview: "BROWN",
    className: "font-black text-white"
  },
  {
    id: "7",
    name: "Fire Style",
    preview: "TURN YOUR\nTEXT",
    className: "font-bold text-white text-[9px] leading-tight",
    hasIcon: true
  },
  {
    id: "8",
    name: "Underline", 
    preview: "QUICK\nBROWN",
    className: "font-bold text-white text-[10px] leading-tight border-b border-purple-500"
  },
  {
    id: "9",
    name: "Gradient",
    preview: "POMEROY'S",
    className: "font-bold bg-gradient-to-r from-pink-500 to-purple-500 bg-clip-text text-transparent text-[10px]"
  }
];

interface CaptionStyleSelectorProps {
  selected: string;
  onChange: (style: string) => void;
}

export function CaptionStyleSelector({ selected, onChange }: CaptionStyleSelectorProps) {
  return (
    <div className="grid grid-cols-3 gap-2">
      {captionStyles.map((style) => (
        <button
          key={style.id}
          onClick={() => onChange(style.id)}
          className={cn(
            "relative group p-3 rounded-lg border transition-all h-16",
            "bg-neutral-900 hover:bg-neutral-800",
            selected === style.id
              ? "border-white"
              : "border-neutral-800 hover:border-neutral-700"
          )}
        >
          {/* Preview Text */}
          <div className="flex items-center justify-center h-full relative">
            {style.hasIcon && (
              <Flame className="absolute -top-2 left-1/2 transform -translate-x-1/2 h-3 w-3 text-orange-500" />
            )}
            <span className={cn("text-center whitespace-pre-line text-xs", style.className)}>
              {style.preview}
            </span>
          </div>
        </button>
      ))}
    </div>
  );
}