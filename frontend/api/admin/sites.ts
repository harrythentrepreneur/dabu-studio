export function useGetSite() {
  return {
    data: null,
    isLoading: false,
    error: null
  };
}

export function useSiteHasData() {
  return {
    data: true,
    isLoading: false,
    error: null
  };
}

export function useCurrentSite() {
  return {
    data: null,
    isLoading: false,
    error: null
  };
}

export function useGetSitesFromOrg() {
  return {
    data: [],
    isLoading: false,
    error: null
  };
}