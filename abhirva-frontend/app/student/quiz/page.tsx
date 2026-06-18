import dynamic from "next/dynamic";

export const dynamic = "force-dynamic";

const QuizClient = dynamic(() => import("./QuizClient"), { ssr: false });

export default function Page() {
  return <QuizClient />;
}
