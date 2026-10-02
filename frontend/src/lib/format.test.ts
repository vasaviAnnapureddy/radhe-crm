import { describe, expect, it } from "vitest";
import { area, changePct, dateText, dateTimeText, days, formatValue, inr, num, percent } from "./format";

describe("inr", () => {
  it("uses crore and lakh", () => {
    expect(inr(42500000)).toBe("₹4.25 Cr");
    expect(inr(68000000)).toBe("₹6.8 Cr");
    expect(inr(140000000)).toBe("₹14 Cr");
    expect(inr(5965200000)).toBe("₹596.5 Cr");
    expect(inr(28505700000)).toBe("₹2,851 Cr");
    expect(inr(3860000)).toBe("₹38.6 L");
    expect(inr(100000)).toBe("₹1 L");
  });
  it("uses Indian grouping below one lakh", () => {
    expect(inr(12500)).toBe("₹12,500");
    expect(inr(0)).toBe("₹0");
  });
  it("handles negatives and missing values", () => {
    expect(inr(-25000000)).toBe("-₹2.5 Cr");
    expect(inr(null)).toBe("–");
    expect(inr(undefined)).toBe("–");
  });
});

describe("numbers", () => {
  it("groups the Indian way", () => {
    expect(num(1234567)).toBe("12,34,567");
    expect(num(1600)).toBe("1,600");
  });
  it("formats percent, days and area", () => {
    expect(percent(45)).toBe("45%");
    expect(percent(11.44)).toBe("11.4%");
    expect(days(23)).toBe("23 days");
    expect(days(1)).toBe("1 day");
    expect(area(2400)).toBe("2,400 sq ft");
    expect(area(300, "sqyd")).toBe("300 sq yd");
  });
});

describe("dates", () => {
  it("formats a plain date", () => {
    expect(dateText("2026-10-01")).toBe("01 Oct 2026");
    expect(dateText("2026-09-05")).toBe("05 Sep 2026");
  });
  it("converts a UTC time to India time", () => {
    // 8:00 pm UTC on 30 Sep is 1:30 am on 01 Oct in India.
    expect(dateText("2026-09-30T20:00:00+00:00")).toBe("01 Oct 2026");
    expect(dateTimeText("2026-10-01T09:15:00Z")).toBe("01 Oct 2026, 2:45 pm");
  });
  it("treats a time without a zone as India time", () => {
    expect(dateTimeText("2026-10-01T00:05:00")).toBe("01 Oct 2026, 12:05 am");
  });
  it("returns a dash for missing or bad values", () => {
    expect(dateText(null)).toBe("–");
    expect(dateText("not a date")).toBe("–");
  });
});

describe("helpers", () => {
  it("works out the change against the previous period", () => {
    expect(changePct(120, 100)).toBe(20);
    expect(changePct(80, 100)).toBe(-20);
    expect(changePct(50, 0)).toBeNull();
    expect(changePct(50, null)).toBeNull();
  });
  it("formats by kind", () => {
    expect(formatValue(68000000, "money")).toBe("₹6.8 Cr");
    expect(formatValue("2026-10-01", "date")).toBe("01 Oct 2026");
    expect(formatValue(42, "score")).toBe("42");
    expect(formatValue(null, "money")).toBe("–");
    expect(formatValue("East", "text")).toBe("East");
  });
});
