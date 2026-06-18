import dynamic from "next/dynamic";

const QuizExamClient = dynamic(() => import("./QuizExamClient"), { ssr: false });

export default function Page() {
  return <QuizExamClient />;
}
