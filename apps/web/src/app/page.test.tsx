import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Home from "./page";

describe("Home", () => {
  it("identifies the application", () => {
    render(<Home />);

    expect(screen.getByRole("heading", { name: "Community Safety Lab" })).toBeInTheDocument();
  });
});
