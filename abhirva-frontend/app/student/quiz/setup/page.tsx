import { Suspense } from "react";
import QuizSetupClient from "./QuizSetupClient";

export const dynamic = "force-dynamic";

export default function Page() {
  return (
    <Suspense fallback={null}>
      <QuizSetupClient />
    </Suspense>
  );
}
