import dynamic from "next/dynamic";

export const dynamic = "force-dynamic";

const QuizExamClient = dynamic(() => import("./QuizExamClient"), { ssr: false });

export default function Page() {
  return <QuizExamClient />;
}
