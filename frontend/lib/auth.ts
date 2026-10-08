// Stub auth client for now
export const authClient = {
  useSession: () => ({ data: null, isLoading: false }),
  useActiveOrganization: () => ({ data: null, isLoading: false }),
  signIn: {
    social: (provider: string) => console.log('Sign in with', provider)
  },
  signOut: () => console.log('Sign out'),
  getSession: () => Promise.resolve(null),
  admin: {},
  organization: {
    useActiveOrganization: () => ({ data: null, isLoading: false })
  },
  emailOTP: {}
};
