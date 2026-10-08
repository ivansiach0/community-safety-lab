import { afterEach, describe, expect, it, vi } from "vitest";

import { initialReportSubmissionFormState } from "../../../features/report-submission/ReportSubmissionForm";
import { submitReport } from "./actions";

const originalApiUrl = process.env.COMMUNITY_SAFETY_API_URL;

afterEach(() => {
  vi.unstubAllGlobals();
  if (originalApiUrl === undefined) {
    delete process.env.COMMUNITY_SAFETY_API_URL;
  } else {
    process.env.COMMUNITY_SAFETY_API_URL = originalApiUrl;
  }
});

function validFormData() {
  const formData = new FormData();
  formData.set("category", "environmental_hazard");
  formData.set("description", "Standing water is blocking the west entrance.");
  formData.set("occurred_at", "2026-10-08T19:30");
  formData.set("timezone_offset", "240");
  formData.set("location", "West entrance");
  return formData;
}

describe("submitReport", () => {
  it("submits an offset-aware report and returns its receipt", async () => {
    process.env.COMMUNITY_SAFETY_API_URL = "http://api.test";
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          report_id: "0199c5c0-7d70-7000-8000-000000000030",
          status: "received",
          submitted_at: "2026-10-08T23:34:12Z",
        }),
        { headers: { "Content-Type": "application/json" }, status: 201 },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    const result = await submitReport(initialReportSubmissionFormState, validFormData());

    expect(fetchMock).toHaveBeenCalledWith("http://api.test/reports", {
      body: JSON.stringify({
        category: "environmental_hazard",
        description: "Standing water is blocking the west entrance.",
        occurred_at: "2026-10-08T23:30:00.000Z",
        location: "West entrance",
      }),
      cache: "no-store",
      headers: { "Content-Type": "application/json" },
      method: "POST",
    });
    expect(result).toEqual({
      status: "success",
      receipt: {
        reportId: "0199c5c0-7d70-7000-8000-000000000030",
        status: "received",
        submittedAt: "2026-10-08T23:34:12Z",
      },
    });
  });

  it("maps API field violations back to the form", async () => {
    process.env.COMMUNITY_SAFETY_API_URL = "http://api.test";
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            error: {
              code: "validation_failed",
              message: "Correct the highlighted fields.",
              fields: {
                description: [{ code: "too_short", message: "Enter at least 20 characters." }],
                occurred_at: [
                  {
                    code: "in_future",
                    message: "Enter a time that is not in the future.",
                  },
                ],
              },
            },
          }),
          { headers: { "Content-Type": "application/json" }, status: 422 },
        ),
      ),
    );

    const result = await submitReport(initialReportSubmissionFormState, validFormData());

    expect(result).toEqual({
      status: "invalid",
      fieldErrors: {
        description: [{ code: "too_short", message: "Enter at least 20 characters." }],
        occurredAt: [
          {
            code: "in_future",
            message: "Enter a time that is not in the future.",
          },
        ],
      },
      values: {
        category: "environmental_hazard",
        description: "Standing water is blocking the west entrance.",
        occurredAt: "2026-10-08T19:30",
        location: "West entrance",
      },
    });
  });

  it("preserves values when the API reports a temporary failure", async () => {
    process.env.COMMUNITY_SAFETY_API_URL = "http://api.test";
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            error: {
              code: "submission_unavailable",
              message: "The report could not be submitted. Try again.",
            },
          }),
          { headers: { "Content-Type": "application/json" }, status: 503 },
        ),
      ),
    );

    const result = await submitReport(initialReportSubmissionFormState, validFormData());

    expect(result).toEqual({
      status: "unavailable",
      values: {
        category: "environmental_hazard",
        description: "Standing water is blocking the west entrance.",
        occurredAt: "2026-10-08T19:30",
        location: "West entrance",
      },
    });
  });

  it("preserves values when the API cannot be reached", async () => {
    process.env.COMMUNITY_SAFETY_API_URL = "http://api.test";
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("fetch failed")));

    const result = await submitReport(initialReportSubmissionFormState, validFormData());

    expect(result).toMatchObject({
      status: "unavailable",
      values: {
        category: "environmental_hazard",
        description: "Standing water is blocking the west entrance.",
        occurredAt: "2026-10-08T19:30",
        location: "West entrance",
      },
    });
  });

  it("returns a field error when the browser does not provide a timezone", async () => {
    process.env.COMMUNITY_SAFETY_API_URL = "http://api.test";
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    const formData = validFormData();
    formData.delete("timezone_offset");

    const result = await submitReport(initialReportSubmissionFormState, formData);

    expect(fetchMock).not.toHaveBeenCalled();
    expect(result).toEqual({
      status: "invalid",
      fieldErrors: {
        occurredAt: [{ code: "timezone_required", message: "Include a timezone." }],
      },
      values: {
        category: "environmental_hazard",
        description: "Standing water is blocking the west entrance.",
        occurredAt: "2026-10-08T19:30",
        location: "West entrance",
      },
    });
  });

  it("returns a field error when the timezone contains only whitespace", async () => {
    process.env.COMMUNITY_SAFETY_API_URL = "http://api.test";
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    const formData = validFormData();
    formData.set("timezone_offset", "   ");

    const result = await submitReport(initialReportSubmissionFormState, formData);

    expect(fetchMock).not.toHaveBeenCalled();
    expect(result).toEqual({
      status: "invalid",
      fieldErrors: {
        occurredAt: [{ code: "timezone_required", message: "Include a timezone." }],
      },
      values: {
        category: "environmental_hazard",
        description: "Standing water is blocking the west entrance.",
        occurredAt: "2026-10-08T19:30",
        location: "West entrance",
      },
    });
  });

  it("returns a field error when the timezone offset is not an integer", async () => {
    process.env.COMMUNITY_SAFETY_API_URL = "http://api.test";
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    const formData = validFormData();
    formData.set("timezone_offset", "12.5");

    const result = await submitReport(initialReportSubmissionFormState, formData);

    expect(fetchMock).not.toHaveBeenCalled();
    expect(result).toEqual({
      status: "invalid",
      fieldErrors: {
        occurredAt: [{ code: "timezone_required", message: "Include a timezone." }],
      },
      values: {
        category: "environmental_hazard",
        description: "Standing water is blocking the west entrance.",
        occurredAt: "2026-10-08T19:30",
        location: "West entrance",
      },
    });
  });

  it("returns a field error when the occurrence date is malformed", async () => {
    process.env.COMMUNITY_SAFETY_API_URL = "http://api.test";
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    const formData = validFormData();
    formData.set("occurred_at", "not-a-date");

    const result = await submitReport(initialReportSubmissionFormState, formData);

    expect(fetchMock).not.toHaveBeenCalled();
    expect(result).toEqual({
      status: "invalid",
      fieldErrors: {
        occurredAt: [{ code: "invalid_format", message: "Enter a valid date and time." }],
      },
      values: {
        category: "environmental_hazard",
        description: "Standing water is blocking the west entrance.",
        occurredAt: "not-a-date",
        location: "West entrance",
      },
    });
  });

  it("returns a field error when the occurrence date is impossible", async () => {
    process.env.COMMUNITY_SAFETY_API_URL = "http://api.test";
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    const formData = validFormData();
    formData.set("occurred_at", "2026-02-31T19:30");

    const result = await submitReport(initialReportSubmissionFormState, formData);

    expect(fetchMock).not.toHaveBeenCalled();
    expect(result).toEqual({
      status: "invalid",
      fieldErrors: {
        occurredAt: [{ code: "invalid_format", message: "Enter a valid date and time." }],
      },
      values: {
        category: "environmental_hazard",
        description: "Standing water is blocking the west entrance.",
        occurredAt: "2026-02-31T19:30",
        location: "West entrance",
      },
    });
  });
});
