import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import NewReportPage from "./page";

afterEach(cleanup);

describe("NewReportPage", () => {
  it("exposes the anonymous report submission form", () => {
    render(<NewReportPage />);

    expect(
      screen.getByRole("heading", { name: "Submit a community safety report" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("form", { name: "Community safety report" })).toBeInTheDocument();
  });
});
