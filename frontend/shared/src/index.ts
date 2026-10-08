// Shared types from Rybbit
export type FilterParameter = 
  | "hostname"
  | "browser"
  | "browser_version"
  | "operating_system"
  | "operating_system_version"
  | "language"
  | "country"
  | "region"
  | "city"
  | "device_type"
  | "referrer"
  | "event_name"
  | "channel"
  | "entry_page"
  | "exit_page"
  | "utm_source"
  | "utm_medium"
  | "utm_campaign"
  | "utm_term"
  | "utm_content"
  | "pathname"
  | "page_title"
  | "querystring"
  | "dimensions";

export type TimeBucket = "minute" | "five_minutes" | "ten_minutes" | "fifteen_minutes" | "hour" | "day" | "week" | "month" | "year";

export interface Filter {
  parameter: FilterParameter;
  type: "is" | "is_not" | "contains" | "does_not_contain";
  value: string | string[];
}