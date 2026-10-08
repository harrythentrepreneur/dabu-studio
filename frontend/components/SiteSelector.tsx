import { ChevronDown } from "lucide-react";
import { useState } from "react";
import { Favicon } from "./Favicon";
import { Popover, PopoverContent, PopoverTrigger } from "./ui/popover";
import { cn } from "../lib/utils";

// Mock site data for now
const mockSites = [
  { siteId: 1, domain: "example.com", sessionsLast24Hours: 1234 },
  { siteId: 2, domain: "demo.site", sessionsLast24Hours: 567 },
];

function SiteSelectorContent({ onSiteSelect }: { onSiteSelect: () => void }) {
  const [selectedSite, setSelectedSite] = useState(mockSites[0]);

  return (
    <PopoverContent align="start" className="w-80 p-2">
      <div className="max-h-96 overflow-y-auto">
        {mockSites.map((site) => {
          const isSelected = site.siteId === selectedSite.siteId;
          return (
            <div
              key={site.siteId}
              onClick={() => {
                setSelectedSite(site);
                onSiteSelect();
              }}
              className={cn(
                "flex items-center justify-between p-2 cursor-pointer hover:bg-neutral-800/50 transition-colors rounded-md border-b border-neutral-800 last:border-b-0",
                isSelected && "bg-neutral-800"
              )}
            >
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <Favicon domain={site.domain} className="w-4 h-4 flex-shrink-0" />
                <div className="text-sm text-white truncate">{site.domain}</div>
              </div>
              <div className="flex items-center gap-3">
                <div className="text-xs text-neutral-300 whitespace-nowrap">
                  {site.sessionsLast24Hours.toLocaleString()} sessions (24h)
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </PopoverContent>
  );
}

export function SiteSelector() {
  const [open, setOpen] = useState(false);
  const [selectedSite] = useState(mockSites[0]);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button className="flex gap-2 items-center border border-neutral-800 rounded-lg py-1.5 px-3 justify-start cursor-pointer hover:bg-neutral-800/50 transition-colors h-[36px] w-full">
          <Favicon domain={selectedSite.domain} className="w-5 h-5" />
          <div className="text-white truncate text-sm flex-1 text-left">
            {selectedSite.domain}
          </div>
          <ChevronDown className="w-4 h-4 text-neutral-400" />
        </button>
      </PopoverTrigger>
      <SiteSelectorContent onSiteSelect={() => setOpen(false)} />
    </Popover>
  );
}