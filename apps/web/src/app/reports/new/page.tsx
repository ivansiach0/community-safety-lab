import type { Metadata } from "next";

import { ReportSubmissionForm } from "../../../features/report-submission/ReportSubmissionForm";
import { submitReport } from "./actions";

export const metadata: Metadata = {
  title: "Submit a report | Community Safety Lab",
};

export default function NewReportPage() {
  return <ReportSubmissionForm action={submitReport} />;
}
