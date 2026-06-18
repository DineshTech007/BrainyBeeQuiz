import dynamic from "next/dynamic";

export const dynamic = "force-dynamic";

const QuizSetupClient = dynamic(() => import("./QuizSetupClient"), { ssr: false });

export default function Page() {
  return <QuizSetupClient />;
}
