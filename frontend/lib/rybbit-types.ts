// Stub types for @rybbit/shared
export type FilterType = 
  | "is" 
  | "is_not" 
  | "contains" 
  | "does_not_contain"
  | "starts_with"
  | "ends_with"
  | "greater_than"
  | "less_than"
  | "between";

export type FilterParameter = 
  | "pathname"
  | "page_title"
  | "querystring"
  | "hostname"
  | "referrer"
  | "utm_source"
  | "utm_medium"
  | "utm_campaign"
  | "utm_term"
  | "utm_content"
  | "browser"
  | "os"
  | "device"
  | "country"
  | "region"
  | "city"
  | "language"
  | "screen_size"
  | "is_bot"
  | "is_entry"
  | "is_exit"
  | "event_name"
  | "event_data"
  | string;

export interface Filter {
  id: string;
  parameter: FilterParameter;
  type: FilterType;
  value: any;
}