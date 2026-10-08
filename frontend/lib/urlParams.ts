import { Filter, TimeBucket } from "@rybbit/shared";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import React, { useEffect } from "react";
import { DateTime } from "luxon";
import { Time } from "../components/DateSelector/types";
import { StatType, useStore } from "./store";

// Serialize store state to URL parameters
const serializeStateToUrl = (
  time: Time,
  bucket: TimeBucket,
  selectedStat: StatType,
  filters: Filter[]
): URLSearchParams => {
  const params = new URLSearchParams();

  // Serialize time
  params.set("timeMode", time.mode);
  if (time.mode === "day" && "day" in time) {
    params.set("day", time.day);
  } else if (time.mode === "range" && "startDate" in time && "endDate" in time) {
    params.set("startDate", time.startDate);
    params.set("endDate", time.endDate);
    if ((time as any).wellKnown) {
      params.set("wellKnown", (time as any).wellKnown);
    }
  } else if (time.mode === "week" && "week" in time) {
    params.set("week", time.week);
  } else if (time.mode === "month" && "month" in time) {
    params.set("month", time.month);
  } else if (time.mode === "year" && "year" in time) {
    params.set("year", time.year);
  } else if (time.mode === "past-minutes" && "pastMinutesEnd" in time) {
    params.set("pastMinutesStart", time.pastMinutesStart.toString());
    params.set("pastMinutesEnd", time.pastMinutesEnd.toString());
  }

  // Serialize bucket
  params.set("bucket", bucket);

  // Serialize selectedStat
  params.set("stat", selectedStat);

  // Serialize filters
  if (filters.length > 0) {
    params.set("filters", JSON.stringify(filters));
  }

  return params;
};

// Deserialize URL parameters to store state
const deserializeUrlToState = (
  searchParams: URLSearchParams
): {
  time: Time | null;
  bucket: TimeBucket | null;
  selectedStat: StatType | null;
  filters: Filter[] | null;
} => {
  const result = {
    time: null as Time | null,
    bucket: null as TimeBucket | null,
    selectedStat: null as StatType | null,
    filters: null as Filter[] | null,
  };

  // Deserialize time
  const timeMode = searchParams.get("timeMode") as Time["mode"] | null;
  if (timeMode) {
    if (timeMode === "past-minutes") {
      const pastMinutesStart = searchParams.get("pastMinutesStart");
      const pastMinutesEnd = searchParams.get("pastMinutesEnd");
      if (pastMinutesStart && pastMinutesEnd) {
        result.time = {
          mode: "past-minutes",
          pastMinutesStart: Number(pastMinutesStart),
          pastMinutesEnd: Number(pastMinutesEnd),
          start: DateTime.now().minus({ minutes: Number(pastMinutesStart) }).toJSDate(),
          end: DateTime.now().minus({ minutes: Number(pastMinutesEnd) }).toJSDate(),
        };
      }
    } else if (timeMode === "day") {
      const day = searchParams.get("day");
      if (day) {
        const dayDate = DateTime.fromISO(day);
        result.time = { 
          mode: "day", 
          day,
          start: dayDate.startOf("day").toJSDate(),
          end: dayDate.endOf("day").toJSDate(),
          pastMinutesStart: 0,
        };
      }
    } else if (timeMode === "range") {
      const startDate = searchParams.get("startDate");
      const endDate = searchParams.get("endDate");
      if (startDate && endDate) {
        const wellKnown = searchParams.get("wellKnown") as
          | "Last 3 days"
          | "Last 7 days"
          | "Last 14 days"
          | "Last 30 days"
          | "Last 60 days"
          | undefined;
        result.time = {
          mode: "range",
          startDate,
          endDate,
          start: DateTime.fromISO(startDate).startOf("day").toJSDate(),
          end: DateTime.fromISO(endDate).endOf("day").toJSDate(),
          pastMinutesStart: 0,
        } as Time;
        // Add wellKnown if it exists
        if (wellKnown) {
          (result.time as any).wellKnown = wellKnown;
        }
      }
    } else if (timeMode === "week") {
      const week = searchParams.get("week");
      if (week) {
        const weekDate = DateTime.fromISO(week);
        result.time = { 
          mode: "week", 
          week,
          start: weekDate.startOf("week").toJSDate(),
          end: weekDate.endOf("week").toJSDate(),
          pastMinutesStart: 0,
        };
      }
    } else if (timeMode === "month") {
      const month = searchParams.get("month");
      if (month) {
        const monthDate = DateTime.fromISO(month);
        result.time = { 
          mode: "month", 
          month,
          start: monthDate.startOf("month").toJSDate(),
          end: monthDate.endOf("month").toJSDate(),
          pastMinutesStart: 0,
        };
      }
    } else if (timeMode === "year") {
      const year = searchParams.get("year");
      if (year) {
        const yearDate = DateTime.fromISO(year);
        result.time = { 
          mode: "year", 
          year,
          start: yearDate.startOf("year").toJSDate(),
          end: yearDate.endOf("year").toJSDate(),
          pastMinutesStart: 0,
        };
      }
    } else if (timeMode === "all-time") {
      result.time = { 
        mode: "all-time",
        start: new Date(0),
        end: new Date(),
        pastMinutesStart: 0,
      };
    }
  }

  // Deserialize bucket with validation
  const bucketParam = searchParams.get("bucket");
  if (bucketParam) {
    // Validate that it's a valid TimeBucket value
    const validBuckets: TimeBucket[] = [
      "minute",
      "five_minutes",
      "ten_minutes",
      "fifteen_minutes",
      "hour",
      "day",
      "week",
      "month",
      "year",
    ];

    if (validBuckets.includes(bucketParam as TimeBucket)) {
      result.bucket = bucketParam as TimeBucket;
    }
  }

  // Deserialize selectedStat
  const stat = searchParams.get("stat") as StatType | null;
  if (stat) {
    result.selectedStat = stat;
  }

  // Deserialize filters
  const filtersStr = searchParams.get("filters");
  if (filtersStr) {
    try {
      result.filters = JSON.parse(filtersStr);
    } catch (e) {
      console.error("Failed to parse filters from URL", e);
    }
  }

  return result;
};

// Hook to sync store state with URL
export const useSyncStateWithUrl = () => {
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const router = useRouter();
  const {
    time,
    bucket,
    selectedStat,
    filters,
    setTime,
    setBucket,
    setSelectedStat,
    setFilters,
    site,
  } = useStore();

  // Use a ref to track if we've already loaded from URL
  // This prevents overriding user changes if the effect re-runs
  const initializedFromUrlRef = React.useRef(false);

  // Check if we're on a path where we should sync URL params
  const shouldSyncUrl = () => {
    if (!pathname) return false;
    const pathParts = pathname.split("/");
    if (pathParts.length < 3) return false;
    return ["main", "sessions", "users", "performance"].includes(pathParts[2]);
  };

  // Initialize from URL params after site is set
  // This fixes the issue where setSite would override URL params
  useEffect(() => {
    // Only proceed if site has been set and we haven't initialized yet
    // and we're on a path where we should sync URL params
    if (!site || initializedFromUrlRef.current || !shouldSyncUrl()) return;

    const state = deserializeUrlToState(searchParams);
    let needsUpdate = false;

    // Process time first without changing bucket
    if (state.time) {
      setTime(state.time, false); // Don't change bucket
      needsUpdate = true;
    }

    // Process bucket separately to ensure it's not overridden by setTime
    if (state.bucket) {
      setBucket(state.bucket);
      needsUpdate = true;
    }

    if (state.selectedStat) {
      setSelectedStat(state.selectedStat);
      needsUpdate = true;
    }

    if (state.filters) {
      setFilters(state.filters);
      needsUpdate = true;
    }

    // If we updated the state from URL, also update the previousTime
    // but make sure not to change the bucket again
    if (needsUpdate && state.time) {
      // Force a recalculation of the previousTime by setting the time again
      // But explicitly tell it not to change the bucket
      setTime(state.time, false);
    }

    // Mark that we've initialized from URL
    initializedFromUrlRef.current = true;
  }, [searchParams, site, setTime, setBucket, setSelectedStat, setFilters]); // Added all dependencies

  // Update URL when state changes
  useEffect(() => {
    // Don't update URL if site hasn't been set yet
    // or if we're not on a path where we should sync URL params
    if (!site || !shouldSyncUrl()) return;

    const params = serializeStateToUrl(time, bucket, selectedStat, filters);
    const newSearch = params.toString();

    // Only update if the search params have changed to avoid infinite loops
    const currentSearch = searchParams.toString();
    if (newSearch !== currentSearch) {
      // Replace the current URL with the new one to avoid adding to history
      router.replace(`${pathname}?${newSearch}`);
    }
  }, [
    time,
    bucket,
    selectedStat,
    filters,
    pathname,
    router,
    site,
    searchParams,
  ]); // Added searchParams
};
