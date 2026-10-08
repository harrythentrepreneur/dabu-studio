import { Filter, FilterParameter, TimeBucket } from "@rybbit/shared";
import { DateTime } from "luxon";
import { create } from "zustand";
import { Time } from "../components/DateSelector/types";

export type StatType =
  | "pageviews"
  | "sessions"
  | "users"
  | "pages_per_session"
  | "bounce_rate"
  | "session_duration";

export const SESSION_PAGE_FILTERS: FilterParameter[] = [
  "hostname",
  "browser",
  "browser_version",
  "operating_system",
  "operating_system_version",
  "language",
  "country",
  "region",
  "city",
  "device_type",
  "referrer",
  "event_name",
  "channel",
  "entry_page",
  "exit_page",
  "utm_source",
  "utm_medium",
  "utm_campaign",
  "utm_term",
  "utm_content",
];

export const SESSION_REPLAY_PAGE_FILTERS: FilterParameter[] = [
  "hostname",
  "browser",
  "browser_version",
  "operating_system",
  "operating_system_version",
  "language",
  "country",
  "region",
  "city",
  "device_type",
  "referrer",
  "channel",
];

export const EVENT_FILTERS: FilterParameter[] = [
  // "event_name",
  // "browser",
  // "operating_system",
  // "country",
  // "device_type",
  // "referrer",
  "hostname",
  "browser",
  "browser_version",
  "operating_system",
  "operating_system_version",
  "language",
  "country",
  "region",
  "city",
  "device_type",
  "referrer",
  "pathname",
  "page_title",
  "querystring",
  "event_name",
  "channel",
  "utm_source",
  "utm_medium",
  "utm_campaign",
  "utm_term",
  "utm_content",
  "entry_page",
  "exit_page",
  "dimensions",
];

export const GOALS_PAGE_FILTERS: FilterParameter[] = [
  "hostname",
  "browser",
  "browser_version",
  "operating_system",
  "operating_system_version",
  "language",
  "country",
  "region",
  "city",
  "device_type",
  "referrer",
  "event_name",
  "channel",
  "entry_page",
  "exit_page",
];

export const USER_PAGE_FILTERS: FilterParameter[] = [
  "hostname",
  "browser",
  "browser_version",
  "operating_system",
  "operating_system_version",
  "language",
  "country",
  "region",
  "city",
  "device_type",
  "referrer",
];

export type VideoResult = {
  videoUrl?: string;
  scriptUrl?: string;
  timestampsUrl?: string;
  mergedFullUrl?: string;
  captionedVideoUrl?: string;
  projectBundleUrl?: string;
  segments?: any[];
  error?: string;
  createdAt: number;
  id: string;
  archived?: boolean;
  status?: 'processing' | 'complete' | 'error';
  currentStep?: number;
  progress?: number;
  statusMessage?: string;
  processingStartTime?: number;
  requestId?: string; // For reconnecting to SSE
};

type Store = {
  site: string;
  setSite: (site: string) => void;
  time: Time;
  previousTime: Time;
  setTime: (time: Time, changeBucket?: boolean) => void;
  bucket: TimeBucket;
  setBucket: (bucket: TimeBucket) => void;
  selectedStat: StatType;
  setSelectedStat: (stat: StatType) => void;
  filters: Filter[];
  setFilters: (filters: Filter[]) => void;
  
  // Video processing state
  processingStatus: 'idle' | 'processing' | 'completed' | 'error';
  setProcessingStatus: (status: 'idle' | 'processing' | 'completed' | 'error') => void;
  
  // Video cache management
  videoCache: VideoResult[];
  currentVideoIndex: number;
  addVideoToCache: (video: VideoResult) => void;
  updateVideoInCache: (videoId: string, updates: Partial<VideoResult>) => void;
  archiveCurrentVideo: () => void;
  navigateToVideo: (index: number) => void;
  navigateToPreviousVideo: () => void;
  navigateToNextVideo: () => void;
  getCurrentVideo: () => VideoResult | null;
  getNonArchivedVideos: () => VideoResult[];
  resetStore: () => void;
};

export const useStore = create<Store>((set, get) => ({
  site: "",
  setSite: (site) => {
    // Get current URL search params to check for stored state
    let urlParams: URLSearchParams | null = null;
    if (typeof window !== "undefined") {
      urlParams = new URLSearchParams(globalThis.location.search);
    }

    // Check if we have state stored in the URL
    const hasTimeInUrl = urlParams?.has("timeMode");
    const hasBucketInUrl = urlParams?.has("bucket");
    const hasStatInUrl = urlParams?.has("stat");

    // Only set defaults if not present in URL
    set((state) => ({
      site,
      time: hasTimeInUrl
        ? state.time
        : {
            mode: "day",
            day: DateTime.now().toISODate() ?? "",
            start: DateTime.now().startOf("day").toJSDate(),
            end: DateTime.now().endOf("day").toJSDate(),
            pastMinutesStart: 0,
          },
      previousTime: hasTimeInUrl
        ? state.previousTime
        : {
            mode: "day",
            day: DateTime.now().minus({ days: 1 }).toISODate() ?? "",
            start: DateTime.now().minus({ days: 1 }).startOf("day").toJSDate(),
            end: DateTime.now().minus({ days: 1 }).endOf("day").toJSDate(),
            pastMinutesStart: 0,
          },
      bucket: hasBucketInUrl ? state.bucket : "hour",
      selectedStat: hasStatInUrl ? state.selectedStat : "users",
    }));
  },
  
  // Video processing state
  processingStatus: 'idle',
  setProcessingStatus: (status) => set({ processingStatus: status }),
  
  // Video cache management
  videoCache: [],
  currentVideoIndex: -1,
  
  addVideoToCache: (video) => set((state) => ({
    videoCache: [...state.videoCache, video],
    currentVideoIndex: state.videoCache.length, // Point to the newly added video
    processingStatus: 'completed'
  })),
  
  updateVideoInCache: (videoId, updates) => set((state) => ({
    videoCache: state.videoCache.map(v => 
      v.id === videoId ? { ...v, ...updates } : v
    )
  })),
  
  archiveCurrentVideo: () => set((state) => {
    const currentVideo = state.videoCache[state.currentVideoIndex];
    if (!currentVideo) return state;
    
    const updatedCache = [...state.videoCache];
    updatedCache[state.currentVideoIndex] = { ...currentVideo, archived: true };
    
    // Find next non-archived video
    const nonArchivedVideos = updatedCache.filter(v => !v.archived);
    let newIndex = state.currentVideoIndex;
    
    if (nonArchivedVideos.length > 0) {
      // Find the next non-archived video index
      for (let i = 0; i < updatedCache.length; i++) {
        if (!updatedCache[i].archived) {
          newIndex = i;
          break;
        }
      }
    }
    
    return {
      videoCache: updatedCache,
      currentVideoIndex: newIndex
    };
  }),
  
  navigateToVideo: (index) => set((state) => ({
    currentVideoIndex: index === -1 ? -1 : Math.max(0, Math.min(index, state.videoCache.length - 1))
  })),
  
  navigateToPreviousVideo: () => set((state) => {
    const nonArchivedVideos = state.videoCache
      .map((v, i) => ({ video: v, index: i }))
      .filter(item => !item.video.archived);
    
    if (nonArchivedVideos.length === 0) return state;
    
    // If only one video exists, toggle between -1 (new/main page) and the video
    if (nonArchivedVideos.length === 1) {
      if (state.currentVideoIndex === -1) {
        return { currentVideoIndex: nonArchivedVideos[0].index };
      } else {
        return { currentVideoIndex: -1 };
      }
    }
    
    const currentNonArchivedIndex = nonArchivedVideos.findIndex(
      item => item.index === state.currentVideoIndex
    );
    
    // If on main page (-1), go to last video
    if (state.currentVideoIndex === -1) {
      return { currentVideoIndex: nonArchivedVideos[nonArchivedVideos.length - 1].index };
    }
    
    // Cycle through videos: if at beginning or not found, go to last
    if (currentNonArchivedIndex <= 0) {
      return { currentVideoIndex: nonArchivedVideos[nonArchivedVideos.length - 1].index };
    }
    
    return { currentVideoIndex: nonArchivedVideos[currentNonArchivedIndex - 1].index };
  }),
  
  navigateToNextVideo: () => set((state) => {
    const nonArchivedVideos = state.videoCache
      .map((v, i) => ({ video: v, index: i }))
      .filter(item => !item.video.archived);
    
    if (nonArchivedVideos.length === 0) return state;
    
    // If only one video exists, toggle between -1 (new/main page) and the video
    if (nonArchivedVideos.length === 1) {
      if (state.currentVideoIndex === -1) {
        return { currentVideoIndex: nonArchivedVideos[0].index };
      } else {
        return { currentVideoIndex: -1 };
      }
    }
    
    const currentNonArchivedIndex = nonArchivedVideos.findIndex(
      item => item.index === state.currentVideoIndex
    );
    
    // If on main page (-1), go to first video
    if (state.currentVideoIndex === -1) {
      return { currentVideoIndex: nonArchivedVideos[0].index };
    }
    
    // Cycle through videos: if at end or not found, go to first
    if (currentNonArchivedIndex === -1 || currentNonArchivedIndex >= nonArchivedVideos.length - 1) {
      return { currentVideoIndex: nonArchivedVideos[0].index };
    }
    
    return { currentVideoIndex: nonArchivedVideos[currentNonArchivedIndex + 1].index };
  }),
  
  getCurrentVideo: () => {
    const state = get();
    return state.videoCache[state.currentVideoIndex] || null;
  },
  
  getNonArchivedVideos: () => {
    const state = get();
    return state.videoCache.filter(v => !v.archived);
  },
  
  resetStore: () => set({
    processingStatus: 'idle',
    videoCache: [],
    currentVideoIndex: -1
  }),
  time: {
    mode: "day",
    day: DateTime.now().toISODate() ?? "",
    start: DateTime.now().startOf("day").toJSDate(),
    end: DateTime.now().endOf("day").toJSDate(),
    pastMinutesStart: 0,
  },
  previousTime: {
    mode: "day",
    day: DateTime.now().minus({ days: 1 }).toISODate() ?? "",
    start: DateTime.now().minus({ days: 1 }).startOf("day").toJSDate(),
    end: DateTime.now().minus({ days: 1 }).endOf("day").toJSDate(),
    pastMinutesStart: 0,
  },
  setTime: (time, changeBucket = true) => {
    let bucketToUse: TimeBucket = "hour";
    let previousTime: Time;

    if (time.mode === "day" && "day" in time) {
      bucketToUse = "hour";
      const previousDay = DateTime.fromISO(time.day).minus({ days: 1 });
      previousTime = {
        mode: "day",
        day: previousDay.toISODate() ?? "",
        start: previousDay.startOf("day").toJSDate(),
        end: previousDay.endOf("day").toJSDate(),
        pastMinutesStart: 0,
      };
    } else if (time.mode === "past-minutes" && "pastMinutesEnd" in time) {
      const timeDiff = time.pastMinutesStart - time.pastMinutesEnd;

      if (timeDiff <= 120) {
        bucketToUse = "minute";
      }

      previousTime = {
        mode: "past-minutes",
        pastMinutesStart: time.pastMinutesStart + timeDiff,
        pastMinutesEnd: time.pastMinutesEnd + timeDiff,
        start: DateTime.now().minus({ minutes: time.pastMinutesStart + timeDiff }).toJSDate(),
        end: DateTime.now().minus({ minutes: time.pastMinutesEnd + timeDiff }).toJSDate(),
      };
    } else if (time.mode === "range" && "startDate" in time && "endDate" in time) {
      const timeRangeLength =
        DateTime.fromISO(time.endDate).diff(
          DateTime.fromISO(time.startDate),
          "days"
        ).days + 1;

      if (timeRangeLength > 180) {
        bucketToUse = "month";
      } else if (timeRangeLength > 31) {
        bucketToUse = "week";
      } else {
        bucketToUse = "day";
      }

      const previousStartDate = DateTime.fromISO(time.startDate).minus({ days: timeRangeLength });
      const previousEndDate = DateTime.fromISO(time.startDate).minus({ days: 1 });
      previousTime = {
        mode: "range",
        startDate: previousStartDate.toISODate() ?? "",
        endDate: previousEndDate.toISODate() ?? "",
        start: previousStartDate.startOf("day").toJSDate(),
        end: previousEndDate.endOf("day").toJSDate(),
        pastMinutesStart: 0,
      };
    } else if (time.mode === "week" && "week" in time) {
      bucketToUse = "day";
      const previousWeek = DateTime.fromISO(time.week).minus({ weeks: 1 });
      previousTime = {
        mode: "week",
        week: previousWeek.toISODate() ?? "",
        start: previousWeek.startOf("week").toJSDate(),
        end: previousWeek.endOf("week").toJSDate(),
        pastMinutesStart: 0,
      };
    } else if (time.mode === "month" && "month" in time) {
      bucketToUse = "day";
      const previousMonth = DateTime.fromISO(time.month).minus({ months: 1 });
      previousTime = {
        mode: "month",
        month: previousMonth.toISODate() ?? "",
        start: previousMonth.startOf("month").toJSDate(),
        end: previousMonth.endOf("month").toJSDate(),
        pastMinutesStart: 0,
      };
    } else if (time.mode === "year" && "year" in time) {
      bucketToUse = "month";
      const previousYear = DateTime.fromISO(time.year).minus({ years: 1 });
      previousTime = {
        mode: "year",
        year: previousYear.toISODate() ?? "",
        start: previousYear.startOf("year").toJSDate(),
        end: previousYear.endOf("year").toJSDate(),
        pastMinutesStart: 0,
      };
    } else if (time.mode === "all-time") {
      bucketToUse = "day";
      previousTime = {
        mode: "all-time",
        start: new Date(0), // Beginning of time
        end: new Date(), // Current date
        pastMinutesStart: 0,
      };
    } else {
      previousTime = time; // fallback case
    }

    if (changeBucket) {
      set({ time, previousTime, bucket: bucketToUse });
    } else {
      set({ time, previousTime });
    }
  },
  bucket: "hour",
  setBucket: (bucket) => set({ bucket }),
  selectedStat: "users",
  setSelectedStat: (stat) => set({ selectedStat: stat }),
  filters: [],
  setFilters: (filters) => set({ filters }),
}));

// Export resetStore as a standalone function for backward compatibility
export const resetStore = () => {
  const state = useStore.getState();
  state.resetStore();
};

export const goBack = () => {
  const { time, setTime } = useStore.getState();

  if (time.mode === "day" && "day" in time) {
    setTime(
      {
        mode: "day",
        day: DateTime.fromISO(time.day).minus({ days: 1 }).toISODate() ?? "",
        start: DateTime.fromISO(time.day).minus({ days: 1 }).startOf("day").toJSDate(),
        end: DateTime.fromISO(time.day).minus({ days: 1 }).endOf("day").toJSDate(),
        pastMinutesStart: 0,
      },
      false
    );
  } else if (time.mode === "range" && "startDate" in time && "endDate" in time) {
    const startDate = DateTime.fromISO(time.startDate);
    const endDate = DateTime.fromISO(time.endDate);

    const daysBetweenStartAndEnd = endDate.diff(startDate, "days").days;

    const newStartDate = startDate.minus({ days: daysBetweenStartAndEnd });
    const newEndDate = startDate;
    setTime(
      {
        mode: "range",
        startDate: newStartDate.toISODate() ?? "",
        endDate: newEndDate.toISODate() ?? "",
        start: newStartDate.startOf("day").toJSDate(),
        end: newEndDate.endOf("day").toJSDate(),
        pastMinutesStart: 0,
      },
      false
    );
  } else if (time.mode === "week" && "week" in time) {
    setTime(
      {
        mode: "week",
        week: DateTime.fromISO(time.week).minus({ weeks: 1 }).toISODate() ?? "",
        start: DateTime.fromISO(time.week).minus({ weeks: 1 }).startOf("week").toJSDate(),
        end: DateTime.fromISO(time.week).minus({ weeks: 1 }).endOf("week").toJSDate(),
        pastMinutesStart: 0,
      },
      false
    );
  } else if (time.mode === "month" && "month" in time) {
    setTime(
      {
        mode: "month",
        month:
          DateTime.fromISO(time.month).minus({ months: 1 }).toISODate() ?? "",
        start: DateTime.fromISO(time.month).minus({ months: 1 }).startOf("month").toJSDate(),
        end: DateTime.fromISO(time.month).minus({ months: 1 }).endOf("month").toJSDate(),
        pastMinutesStart: 0,
      },
      false
    );
  } else if (time.mode === "year" && "year" in time) {
    setTime(
      {
        mode: "year",
        year: DateTime.fromISO(time.year).minus({ years: 1 }).toISODate() ?? "",
        start: DateTime.fromISO(time.year).minus({ years: 1 }).startOf("year").toJSDate(),
        end: DateTime.fromISO(time.year).minus({ years: 1 }).endOf("year").toJSDate(),
        pastMinutesStart: 0,
      },
      false
    );
  }
};

export const goForward = () => {
  const { time, setTime } = useStore.getState();

  if (time.mode === "day" && "day" in time) {
    const nextDay = DateTime.fromISO(time.day).plus({ days: 1 });
    setTime({
      mode: "day",
      day: nextDay.toISODate() ?? "",
      start: nextDay.startOf("day").toJSDate(),
      end: nextDay.endOf("day").toJSDate(),
      pastMinutesStart: 0,
    });
  } else if (time.mode === "range" && "startDate" in time && "endDate" in time) {
    const startDate = DateTime.fromISO(time.startDate);
    const endDate = DateTime.fromISO(time.endDate);
    const now = DateTime.now();

    const daysBetweenStartAndEnd = endDate.diff(startDate, "days").days;
    const proposedEndDate = endDate.plus({ days: daysBetweenStartAndEnd });

    // Don't allow moving forward if it would put the entire range in the future
    if (startDate.plus({ days: daysBetweenStartAndEnd }) > now) {
      return;
    }

    const newStartDate = startDate.plus({ days: daysBetweenStartAndEnd });
    setTime(
      {
        mode: "range",
        startDate: newStartDate.toISODate() ?? "",
        // Cap the end date at today
        endDate: proposedEndDate.toISODate() ?? "",
        start: newStartDate.startOf("day").toJSDate(),
        end: proposedEndDate.endOf("day").toJSDate(),
        pastMinutesStart: 0,
      },
      false
    );
  } else if (time.mode === "week" && "week" in time) {
    setTime(
      {
        mode: "week",
        week: DateTime.fromISO(time.week).plus({ weeks: 1 }).toISODate() ?? "",
        start: DateTime.fromISO(time.week).plus({ weeks: 1 }).startOf("week").toJSDate(),
        end: DateTime.fromISO(time.week).plus({ weeks: 1 }).endOf("week").toJSDate(),
        pastMinutesStart: 0,
      },
      false
    );
  } else if (time.mode === "month" && "month" in time) {
    setTime(
      {
        mode: "month",
        month:
          DateTime.fromISO(time.month).plus({ months: 1 }).toISODate() ?? "",
        start: DateTime.fromISO(time.month).plus({ months: 1 }).startOf("month").toJSDate(),
        end: DateTime.fromISO(time.month).plus({ months: 1 }).endOf("month").toJSDate(),
        pastMinutesStart: 0,
      },
      false
    );
  } else if (time.mode === "year" && "year" in time) {
    setTime(
      {
        mode: "year",
        year: DateTime.fromISO(time.year).plus({ years: 1 }).toISODate() ?? "",
        start: DateTime.fromISO(time.year).plus({ years: 1 }).startOf("year").toJSDate(),
        end: DateTime.fromISO(time.year).plus({ years: 1 }).endOf("year").toJSDate(),
        pastMinutesStart: 0,
      },
      false
    );
  }
};

export const addFilter = (filter: Filter) => {
  const { filters, setFilters } = useStore.getState();
  const filterExists = filters.some(
    (f) =>
      f.parameter === filter.parameter &&
      f.type === filter.type &&
      JSON.stringify(f.value) === JSON.stringify(filter.value)
  );
  if (!filterExists) {
    setFilters([...filters, filter]);
  }
};

export const removeFilter = (filter: Filter) => {
  const { filters, setFilters } = useStore.getState();
  setFilters(filters.filter((f) => f !== filter));
};

export const updateFilter = (filter: Filter, index: number) => {
  const { filters, setFilters } = useStore.getState();
  setFilters(filters.map((f, i) => (i === index ? filter : f)));
};

export const getFilteredFilters = (parameters: FilterParameter[]) => {
  const { filters } = useStore.getState();
  return filters.filter((f) => parameters.includes(f.parameter));
};
