import { Suspense } from "react";
import QuizExamClient from "./QuizExamClient";

export const dynamic = "force-dynamic";

export default function Page() {
  return (
    <Suspense fallback={null}>
      <QuizExamClient />
    </Suspense>
  );
}
