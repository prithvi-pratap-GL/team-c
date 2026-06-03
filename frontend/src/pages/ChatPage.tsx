import { Department } from "../api/client";
import { ChatWindow } from "../components/ChatWindow";

interface ChatPageProps {
  token: string;
  allowedDepartments: Department[];
}

export function ChatPage({ token, allowedDepartments }: ChatPageProps) {
  return <ChatWindow token={token} allowedDepartments={allowedDepartments} />;
}
