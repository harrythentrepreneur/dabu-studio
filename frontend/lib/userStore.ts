import { create } from "zustand";
import { authClient } from "./auth";

interface User {
  id: string;
  email?: string;
  name?: string;
}

export const userStore = create<{
  user: User | null;
  isPending: boolean;
  setSession: (user: User) => void;
  setIsPending: (isPending: boolean) => void;
}>((set) => ({
  user: null,
  isPending: true,
  setSession: (user) => set({ user }),
  setIsPending: (isPending) => set({ isPending }),
}));

// Fix: Handle null response from getSession
authClient.getSession().then((response) => {
  if (response && (response as any).data) {
    userStore.setState({
      user: (response as any).data.user || null,
      isPending: false,
    });
  } else {
    userStore.setState({
      user: null,
      isPending: false,
    });
  }
}).catch(() => {
  userStore.setState({
    user: null,
    isPending: false,
  });
});
