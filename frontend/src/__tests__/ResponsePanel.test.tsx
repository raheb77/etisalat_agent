import { render, screen } from "@testing-library/react";

import { ResponsePanel } from "../components/ResponsePanel";
import { responseNoCitations, responseWithCitations } from "./fixtures";

describe("ResponsePanel", () => {
  it("renders answer text", () => {
    render(<ResponsePanel data={responseWithCitations} uiLocale="en-US" />);
    expect(
      screen.getByText(responseWithCitations.answer)
    ).toBeInTheDocument();
  });

  it("renders citations list when present", () => {
    render(<ResponsePanel data={responseWithCitations} uiLocale="en-US" />);
    expect(
      screen.getByText(responseWithCitations.citations[0].source)
    ).toBeInTheDocument();
  });

  it("renders a no citations state without crashing", () => {
    render(<ResponsePanel data={responseNoCitations} uiLocale="en-US" />);
    expect(
      screen.getByText(/No direct supporting sources/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/No citations returned/i)).toBeInTheDocument();
  });
});
