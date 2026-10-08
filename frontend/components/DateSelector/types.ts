export type Time = 
  | {
      mode: "day";
      day: string;
      start: Date;
      end: Date;
      pastMinutesStart: number;
    }
  | {
      mode: "past-minutes";
      pastMinutesStart: number;
      pastMinutesEnd: number;
      start: Date;
      end: Date;
    }
  | {
      mode: "range";
      startDate: string;
      endDate: string;
      start: Date;
      end: Date;
      pastMinutesStart: number;
    }
  | {
      mode: "week";
      week: string;
      start: Date;
      end: Date;
      pastMinutesStart: number;
    }
  | {
      mode: "month";
      month: string;
      start: Date;
      end: Date;
      pastMinutesStart: number;
    }
  | {
      mode: "year";
      year: string;
      start: Date;
      end: Date;
      pastMinutesStart: number;
    }
  | {
      mode: "all-time";
      start: Date;
      end: Date;
      pastMinutesStart: number;
    }
  | {
      mode: string;
      start: Date;
      end: Date;
      pastMinutesStart: number;
    };