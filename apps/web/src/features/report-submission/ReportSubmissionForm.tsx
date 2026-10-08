"use client";

import { useActionState, useEffect, useRef } from "react";

export type ReportSubmissionFieldError = {
  code: string;
  message: string;
};

export type ReportSubmissionValues = {
  category: string;
  description: string;
  occurredAt: string;
  location: string;
};

export type ReportSubmissionFormState = {
  status: "idle" | "invalid" | "success" | "unavailable";
  fieldErrors?: Partial<Record<keyof ReportSubmissionValues, ReportSubmissionFieldError[]>>;
  values?: ReportSubmissionValues;
  receipt?: {
    reportId: string;
    status: "received";
    submittedAt: string;
  };
};

export type ReportSubmissionFormAction = (
  previousState: ReportSubmissionFormState,
  formData: FormData,
) => Promise<ReportSubmissionFormState>;

export const initialReportSubmissionFormState: ReportSubmissionFormState = {
  status: "idle",
  fieldErrors: {},
  values: {
    category: "",
    description: "",
    occurredAt: "",
    location: "",
  },
};

type ReportSubmissionFormProps = {
  action: ReportSubmissionFormAction;
};

export function ReportSubmissionForm({ action }: ReportSubmissionFormProps) {
  const [state, formAction, pending] = useActionState(action, initialReportSubmissionFormState);
  const feedbackRef = useRef<HTMLDivElement | null>(null);
  const receiptRef = useRef<HTMLHeadingElement | null>(null);
  const timezoneOffsetRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (timezoneOffsetRef.current) {
      timezoneOffsetRef.current.value = String(new Date().getTimezoneOffset());
    }
  }, []);

  useEffect(() => {
    if (state.status === "invalid" || state.status === "unavailable") {
      feedbackRef.current?.focus();
    }

    if (state.status === "success") {
      receiptRef.current?.focus();
    }
  }, [state.status]);

  const categoryErrors = state.fieldErrors?.category ?? [];
  const descriptionErrors = state.fieldErrors?.description ?? [];
  const occurredAtErrors = state.fieldErrors?.occurredAt ?? [];
  const locationErrors = state.fieldErrors?.location ?? [];
  const values = state.values ?? initialReportSubmissionFormState.values!;

  return (
    <main>
      <h1>Submit a community safety report</h1>
      <p>This form is anonymous. It is not an emergency channel.</p>

      {state.status === "success" && state.receipt ? (
        <section aria-live="polite">
          <h2 ref={receiptRef} tabIndex={-1}>
            Report received
          </h2>
          <p>
            Your report reference is <strong>{state.receipt.reportId}</strong>.
          </p>
          <p>Status: {state.receipt.status}</p>
          <p>
            Submitted: <time dateTime={state.receipt.submittedAt}>{state.receipt.submittedAt}</time>
          </p>
        </section>
      ) : null}

      {state.status === "invalid" ? (
        <div ref={feedbackRef} role="alert" tabIndex={-1}>
          <h2>Correct the highlighted fields</h2>
          <ul>
            {Object.entries(state.fieldErrors ?? {}).flatMap(([field, errors]) =>
              (errors ?? []).map((error) => (
                <li key={`${field}-${error.code}`}>
                  <a href={`#${field === "occurredAt" ? "occurred-at" : field}`}>{error.message}</a>
                </li>
              )),
            )}
          </ul>
        </div>
      ) : null}

      {state.status === "unavailable" ? (
        <div ref={feedbackRef} role="alert" tabIndex={-1}>
          <h2>Submission temporarily unavailable</h2>
          <p>The report could not be submitted. Try again.</p>
        </div>
      ) : null}

      {state.status !== "success" ? (
        <form action={formAction} aria-label="Community safety report">
          <input ref={timezoneOffsetRef} name="timezone_offset" type="hidden" />
          <div>
            <label htmlFor="category">Category</label>
            <select
              id="category"
              name="category"
              required
              aria-describedby={categoryErrors.length > 0 ? "category-error" : undefined}
              aria-invalid={categoryErrors.length > 0 || undefined}
              defaultValue={values.category}
            >
              <option value="" disabled>
                Select a category
              </option>
              <option value="harassment">Harassment</option>
              <option value="threat_or_violence">Threat or violence</option>
              <option value="property_damage">Property damage</option>
              <option value="environmental_hazard">Environmental hazard</option>
              <option value="other">Other</option>
            </select>
            {categoryErrors.length > 0 ? (
              <p id="category-error">{categoryErrors[0].message}</p>
            ) : null}
          </div>

          <div>
            <label htmlFor="description">Description</label>
            <p id="description-help">Enter between 20 and 2,000 characters.</p>
            <textarea
              id="description"
              name="description"
              required
              minLength={20}
              maxLength={2000}
              aria-describedby={
                descriptionErrors.length > 0
                  ? "description-help description-error"
                  : "description-help"
              }
              aria-invalid={descriptionErrors.length > 0 || undefined}
              defaultValue={values.description}
            />
            {descriptionErrors.length > 0 ? (
              <p id="description-error">{descriptionErrors[0].message}</p>
            ) : null}
          </div>

          <div>
            <label htmlFor="occurred-at">When did it occur?</label>
            <input
              id="occurred-at"
              name="occurred_at"
              type="datetime-local"
              required
              aria-describedby={occurredAtErrors.length > 0 ? "occurred-at-error" : undefined}
              aria-invalid={occurredAtErrors.length > 0 || undefined}
              defaultValue={values.occurredAt}
              onChange={(event) => {
                if (timezoneOffsetRef.current) {
                  timezoneOffsetRef.current.value = String(
                    new Date(event.currentTarget.value).getTimezoneOffset(),
                  );
                }
              }}
            />
            {occurredAtErrors.length > 0 ? (
              <p id="occurred-at-error">{occurredAtErrors[0].message}</p>
            ) : null}
          </div>

          <div>
            <label htmlFor="location">Location (optional)</label>
            <input
              id="location"
              name="location"
              type="text"
              maxLength={200}
              aria-describedby={locationErrors.length > 0 ? "location-error" : undefined}
              aria-invalid={locationErrors.length > 0 || undefined}
              defaultValue={values.location}
            />
            {locationErrors.length > 0 ? (
              <p id="location-error">{locationErrors[0].message}</p>
            ) : null}
          </div>

          <button type="submit" disabled={pending}>
            {pending ? "Submitting…" : "Submit report"}
          </button>
        </form>
      ) : null}
    </main>
  );
}
