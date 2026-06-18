import dynamic from "next/dynamic";

const QuizSetupClient = dynamic(() => import("./QuizSetupClient"), { ssr: false });

export default function Page() {
  return <QuizSetupClient />;
}
