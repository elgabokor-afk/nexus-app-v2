import { redirect } from "next/navigation";

export default function Home() {
  redirect("/dashboard");
  return null; // Never reached, but TypeScript needs a return
}
