"use server";

import type {
  ReportSubmissionFieldError,
  ReportSubmissionFormAction,
  ReportSubmissionValues,
} from "../../../features/report-submission/ReportSubmissionForm";

const apiFieldToFormField = {
  category: "category",
  description: "description",
  location: "location",
  occurred_at: "occurredAt",
} as const;

function value(formData: FormData, name: string) {
  const candidate = formData.get(name);
  return typeof candidate === "string" ? candidate : "";
}

function formValues(formData: FormData): ReportSubmissionValues {
  return {
    category: value(formData, "category"),
    description: value(formData, "description"),
    occurredAt: value(formData, "occurred_at"),
    location: value(formData, "location"),
  };
}

function offsetAwareIso(localDateTime: string, offsetText: string) {
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})$/.exec(localDateTime);
  const offsetMinutes = Number(offsetText);
  if (!match || !Number.isFinite(offsetMinutes)) {
    throw new Error("The local date and timezone offset are required.");
  }

  const [, year, month, day, hour, minute] = match;
  const numericYear = Number(year);
  const numericMonth = Number(month) - 1;
  const numericDay = Number(day);
  const numericHour = Number(hour);
  const numericMinute = Number(minute);
  const localMilliseconds = Date.UTC(
    numericYear,
    numericMonth,
    numericDay,
    numericHour,
    numericMinute,
  );
  const normalizedLocalDate = new Date(localMilliseconds);
  if (
    normalizedLocalDate.getUTCFullYear() !== numericYear ||
    normalizedLocalDate.getUTCMonth() !== numericMonth ||
    normalizedLocalDate.getUTCDate() !== numericDay ||
    normalizedLocalDate.getUTCHours() !== numericHour ||
    normalizedLocalDate.getUTCMinutes() !== numericMinute
  ) {
    throw new Error("The occurrence date must be valid.");
  }

  const utcMilliseconds = localMilliseconds + offsetMinutes * 60_000;
  return new Date(utcMilliseconds).toISOString();
}

export const submitReport: ReportSubmissionFormAction = async (_previousState, formData) => {
  const values = formValues(formData);
  const apiUrl = process.env.COMMUNITY_SAFETY_API_URL;
  if (!apiUrl) {
    return { status: "unavailable", values };
  }

  const timezoneOffset = value(formData, "timezone_offset");
  const normalizedTimezoneOffset = timezoneOffset.trim();
  if (!/^-?\d+$/.test(normalizedTimezoneOffset)) {
    return {
      status: "invalid",
      fieldErrors: {
        occurredAt: [{ code: "timezone_required", message: "Include a timezone." }],
      },
      values,
    };
  }

  let occurredAt: string;
  try {
    occurredAt = offsetAwareIso(values.occurredAt, normalizedTimezoneOffset);
  } catch {
    return {
      status: "invalid",
      fieldErrors: {
        occurredAt: [{ code: "invalid_format", message: "Enter a valid date and time." }],
      },
      values,
    };
  }

  let response: Response;
  try {
    response = await fetch(`${apiUrl.replace(/\/$/, "")}/reports`, {
      body: JSON.stringify({
        category: values.category,
        description: values.description,
        occurred_at: occurredAt,
        location: values.location,
      }),
      cache: "no-store",
      headers: { "Content-Type": "application/json" },
      method: "POST",
    });
  } catch {
    return { status: "unavailable", values };
  }

  if (response.status === 422) {
    const payload = (await response.json()) as {
      error?: { fields?: Record<string, ReportSubmissionFieldError[]> };
    };
    const fieldErrors: Partial<Record<keyof ReportSubmissionValues, ReportSubmissionFieldError[]>> =
      {};
    for (const [apiField, errors] of Object.entries(payload.error?.fields ?? {})) {
      const formField = apiFieldToFormField[apiField as keyof typeof apiFieldToFormField];
      if (formField) {
        fieldErrors[formField] = errors;
      }
    }
    return { status: "invalid", fieldErrors, values };
  }

  if (response.status !== 201) {
    return { status: "unavailable", values };
  }

  const payload = (await response.json()) as {
    report_id: string;
    status: "received";
    submitted_at: string;
  };

  return {
    status: "success",
    receipt: {
      reportId: payload.report_id,
      status: payload.status,
      submittedAt: payload.submitted_at,
    },
  };
};
