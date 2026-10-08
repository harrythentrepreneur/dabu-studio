"use client";
import { useState } from "react";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../../../../../components/ui/basic-tabs";
import { Card, CardContent } from "../../../../../components/ui/card";
// import { StandardSection } from "../../../components/shared/StandardSection/StandardSection";
import { Button } from "../../../../../components/ui/button";
import { Expand } from "lucide-react";
import { Favicon } from "../../../../../components/Favicon";

type Tab =
  | "referrers"
  | "channels"
  | "utm_source"
  | "utm_medium"
  | "utm_campaign"
  | "utm_term"
  | "utm_content";

export function Referrers() {
  const [tab, setTab] = useState<Tab>("referrers");
  const [expanded, setExpanded] = useState(false);
  const close = () => {
    setExpanded(false);
  };

  return (
    <Card>
      <CardContent className="pb-4">
        <Tabs value={tab} onValueChange={(v) => setTab(v as Tab)}>
          <div className="flex items-center justify-between mb-2">
            <div className="flex-1">
              <TabsList>
                <TabsTrigger value="referrers">Referrers</TabsTrigger>
                <TabsTrigger value="channels">Channels</TabsTrigger>
                <TabsTrigger value="utm_source">UTM Source</TabsTrigger>
                <TabsTrigger value="utm_medium">UTM Medium</TabsTrigger>
                <TabsTrigger value="utm_campaign">UTM Campaign</TabsTrigger>
                <TabsTrigger value="utm_content">UTM Content</TabsTrigger>
                <TabsTrigger value="utm_term">UTM Term</TabsTrigger>
              </TabsList>
            </div>
            <Button size="smIcon" onClick={() => setExpanded(!expanded)}>
              <Expand className="w-4 h-4" />
            </Button>
          </div>
          <TabsContent value="referrers">
            {/* TODO: Fix StandardSection props mismatch */}
            <Card>
              <CardContent className="p-4">
                <div className="text-center text-neutral-400 py-8">
                  Referrers section temporarily disabled - needs refactoring
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="channels">
            {/* TODO: Fix StandardSection props mismatch */}
            <Card>
              <CardContent className="p-4">
                <div className="text-center text-neutral-400 py-8">
                  Channels section temporarily disabled - needs refactoring
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="utm_source">
            {/* TODO: Fix StandardSection props mismatch */}
            <Card>
              <CardContent className="p-4">
                <div className="text-center text-neutral-400 py-8">
                  UTM Source section temporarily disabled - needs refactoring
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="utm_medium">
            {/* TODO: Fix StandardSection props mismatch */}
            <Card>
              <CardContent className="p-4">
                <div className="text-center text-neutral-400 py-8">
                  UTM Medium section temporarily disabled - needs refactoring
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="utm_campaign">
            {/* TODO: Fix StandardSection props mismatch */}
            <Card>
              <CardContent className="p-4">
                <div className="text-center text-neutral-400 py-8">
                  UTM Campaign section temporarily disabled - needs refactoring
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="utm_content">
            {/* TODO: Fix StandardSection props mismatch */}
            <Card>
              <CardContent className="p-4">
                <div className="text-center text-neutral-400 py-8">
                  UTM Content section temporarily disabled - needs refactoring
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="utm_term">
            {/* TODO: Fix StandardSection props mismatch */}
            <Card>
              <CardContent className="p-4">
                <div className="text-center text-neutral-400 py-8">
                  UTM Term section temporarily disabled - needs refactoring
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}