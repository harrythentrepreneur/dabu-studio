"use client";

import { useStore } from "@/lib/store";
import { Expand } from "lucide-react";
import { useState } from "react";
import { useGetSite } from "../../../../../api/admin/sites";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../../../../../components/ui/basic-tabs";
import { Button } from "../../../../../components/ui/button";
import { Card, CardContent } from "../../../../../components/ui/card";
import { truncateString } from "../../../../../lib/utils";
// import { StandardSection } from "../../../../../components/shared/StandardSection";

type Tab = "pages" | "page_title" | "entry_pages" | "exit_pages" | "hostname";

const MAX_LABEL_LENGTH = 70;

export function Pages() {
  const { data: siteMetadata } = useGetSite();
  const [tab, setTab] = useState<Tab>("pages");
  const [expanded, setExpanded] = useState(false);
  const close = () => {
    setExpanded(false);
  };

  return (
    <Card className="h-[405px]">
      <CardContent className="mt-2">
        <Tabs
          defaultValue="pages"
          value={tab}
          onValueChange={(value) => setTab(value as Tab)}
        >
          <div className="flex flex-row gap-2 justify-between items-center">
            <div className="overflow-x-auto">
              <TabsList>
                <TabsTrigger value="pages">Pages</TabsTrigger>
                <TabsTrigger value="page_title">Page Titles</TabsTrigger>
                <TabsTrigger value="entry_pages">Entry Pages</TabsTrigger>
                <TabsTrigger value="exit_pages">Exit Pages</TabsTrigger>
                <TabsTrigger value="hostname">Hostnames</TabsTrigger>
              </TabsList>
            </div>
            <Button size="smIcon" onClick={() => setExpanded(!expanded)}>
              <Expand className="w-4 h-4" />
            </Button>
          </div>
          <TabsContent value="pages">
            {/* TODO: Fix StandardSection props mismatch */}
            <Card>
              <CardContent className="p-4">
                <div className="text-center text-neutral-400 py-8">
                  Pages section temporarily disabled - needs refactoring
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="page_title">
            {/* TODO: Fix StandardSection props mismatch */}
            <Card>
              <CardContent className="p-4">
                <div className="text-center text-neutral-400 py-8">
                  Page Title section temporarily disabled - needs refactoring
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="entry_pages">
            {/* TODO: Fix StandardSection props mismatch */}
            <Card>
              <CardContent className="p-4">
                <div className="text-center text-neutral-400 py-8">
                  Entry Pages section temporarily disabled - needs refactoring
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="exit_pages">
            {/* TODO: Fix StandardSection props mismatch */}
            <Card>
              <CardContent className="p-4">
                <div className="text-center text-neutral-400 py-8">
                  Exit Pages section temporarily disabled - needs refactoring
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="hostname">
            {/* TODO: Fix StandardSection props mismatch */}
            <Card>
              <CardContent className="p-4">
                <div className="text-center text-neutral-400 py-8">
                  Hostname section temporarily disabled - needs refactoring
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
