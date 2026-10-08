import { useQuery } from "@tanstack/react-query";
import { authClient } from "@/lib/auth";
import { BACKEND_URL } from "../const";

interface SubscriptionData {
  id: string;
  planName: string;
  status: "expired" | "active" | "trialing" | "free";
  currentPeriodEnd: string;
  currentPeriodStart: string;
  monthlyEventCount: number;
  eventLimit: number;
  interval: string;
  cancelAtPeriodEnd: boolean;
  isTrial?: boolean;
  trialDaysRemaining?: number;
  message?: string; // For expired trial message
}

export function useStripeSubscription() {
  const { data: activeOrg } = authClient.useActiveOrganization();

  const fetchSubscription = async () => {
    if (!activeOrg) {
      return null;
    }

    // Since auth is stubbed, this won't actually run, but TypeScript needs it
    const orgId = (activeOrg as any)?.id || 'placeholder';
    
    const response = await fetch(
      `${BACKEND_URL}/stripe/subscription?organizationId=${orgId}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
      }
    );

    if (!response.ok) {
      if (response.status === 401) {
        return null;
      } else {
        const errorData = await response.json();
        throw new Error(errorData.error || `Error: ${response.status}`);
      }
    }

    return await response.json();
  };

  const { data, isLoading, error, refetch } = useQuery<SubscriptionData>({
    queryKey: ["stripe-subscription", (activeOrg as any)?.id],
    queryFn: fetchSubscription,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: false,
    enabled: !!activeOrg,
  });

  return { data, isLoading, error, refetch };
}
