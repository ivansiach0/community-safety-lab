import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { initialReportSubmissionFormState, ReportSubmissionForm } from "./ReportSubmissionForm";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("ReportSubmissionForm", () => {
  it("presents an accessible anonymous report form", () => {
    const { container } = render(
      <ReportSubmissionForm action={async () => initialReportSubmissionFormState} />,
    );

    expect(
      screen.getByRole("heading", { name: "Submit a community safety report" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "Category" })).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Description" })).toBeInTheDocument();
    expect(screen.getByLabelText("When did it occur?")).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Location (optional)" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Submit report" })).toBeInTheDocument();
    expect(screen.getByText(/not an emergency channel/i)).toBeInTheDocument();
    expect(container.querySelector('input[name="timezone_offset"]')).toHaveValue(
      String(new Date().getTimezoneOffset()),
    );
  });

  it("uses the timezone offset for the selected occurrence date", () => {
    vi.spyOn(Date.prototype, "getTimezoneOffset").mockReturnValueOnce(240).mockReturnValue(300);
    const { container } = render(
      <ReportSubmissionForm action={async () => initialReportSubmissionFormState} />,
    );
    const timezoneOffset = container.querySelector('input[name="timezone_offset"]');

    expect(timezoneOffset).toHaveValue("240");

    fireEvent.change(screen.getByLabelText("When did it occur?"), {
      target: { value: "2027-01-08T19:30" },
    });

    expect(timezoneOffset).toHaveValue("300");
  });

  it("focuses a validation summary and preserves submitted values", async () => {
    render(
      <ReportSubmissionForm
        action={async () => ({
          status: "invalid",
          fieldErrors: {
            description: [{ code: "too_short", message: "Enter at least 20 characters." }],
          },
          values: {
            category: "other",
            description: "Too short",
            occurredAt: "2026-10-08T19:30",
            location: "West entrance",
          },
        })}
      />,
    );
    const description = screen.getByRole("textbox", { name: "Description" });
    fireEvent.change(description, { target: { value: "Too short" } });

    fireEvent.submit(screen.getByRole("button", { name: "Submit report" }).closest("form")!);

    const summary = await screen.findByRole("alert");
    await waitFor(() => expect(summary).toHaveFocus());
    expect(description).toHaveAttribute("aria-invalid", "true");
    expect(description).toHaveValue("Too short");
    expect(screen.getByRole("link", { name: "Enter at least 20 characters." })).toHaveAttribute(
      "href",
      "#description",
    );
  });

  it("associates each field violation with its form control", async () => {
    render(
      <ReportSubmissionForm
        action={async () => ({
          status: "invalid",
          fieldErrors: {
            category: [{ code: "invalid_category", message: "Select a valid category." }],
            occurredAt: [{ code: "in_future", message: "Enter a time that is not in the future." }],
            location: [{ code: "too_long", message: "Enter no more than 200 characters." }],
          },
          values: {
            category: "",
            description: "Standing water is blocking the west entrance.",
            occurredAt: "2027-01-08T19:30",
            location: "West entrance",
          },
        })}
      />,
    );

    fireEvent.submit(screen.getByRole("form", { name: "Community safety report" }));
    await screen.findByRole("alert");

    expect(screen.getByRole("combobox", { name: "Category" })).toHaveAttribute(
      "aria-describedby",
      "category-error",
    );
    expect(screen.getByLabelText("When did it occur?")).toHaveAttribute(
      "aria-describedby",
      "occurred-at-error",
    );
    expect(screen.getByRole("textbox", { name: "Location (optional)" })).toHaveAttribute(
      "aria-describedby",
      "location-error",
    );
    expect(document.getElementById("category-error")).toHaveTextContent("Select a valid category.");
    expect(document.getElementById("occurred-at-error")).toHaveTextContent(
      "Enter a time that is not in the future.",
    );
    expect(document.getElementById("location-error")).toHaveTextContent(
      "Enter no more than 200 characters.",
    );
  });

  it("focuses the receipt after a successful submission", async () => {
    render(
      <ReportSubmissionForm
        action={async () => ({
          status: "success",
          receipt: {
            reportId: "0199c5c0-7d70-7000-8000-000000000030",
            status: "received",
            submittedAt: "2026-10-08T23:34:12Z",
          },
        })}
      />,
    );

    fireEvent.submit(screen.getByRole("form", { name: "Community safety report" }));

    const confirmation = await screen.findByRole("heading", { name: "Report received" });
    expect(confirmation).toHaveFocus();
    expect(screen.getByText("0199c5c0-7d70-7000-8000-000000000030")).toBeInTheDocument();
  });

  it("keeps the form values when submission is temporarily unavailable", async () => {
    render(
      <ReportSubmissionForm
        action={async () => ({
          status: "unavailable",
          values: {
            category: "environmental_hazard",
            description: "Standing water is blocking the west entrance.",
            occurredAt: "2026-10-08T19:30",
            location: "West entrance",
          },
        })}
      />,
    );
    const description = screen.getByRole("textbox", { name: "Description" });
    fireEvent.change(description, {
      target: { value: "Standing water is blocking the west entrance." },
    });

    fireEvent.submit(screen.getByRole("form", { name: "Community safety report" }));

    const alert = await screen.findByRole("alert");
    await waitFor(() => expect(alert).toHaveFocus());
    expect(alert).toHaveTextContent("The report could not be submitted. Try again.");
    expect(description).toHaveValue("Standing water is blocking the west entrance.");
    expect(screen.getByRole("button", { name: "Submit report" })).toBeInTheDocument();
  });
});
