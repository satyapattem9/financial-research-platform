import React, { useState } from "react";
import axios from "axios";
import {
  Send,
  FileText,
  Bot,
  User,
  BookmarkCheck,
  Loader2,
} from "lucide-react";

// Define structures matching our FastAPI JSON response schema
interface Source {
  label: string;
  document: string;
  page: number;
}

interface Message {
  id: string;
  sender: "user" | "bot";
  text: string;
  sources?: Source[];
}

export default function App() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      sender: "bot",
      text: "Hello! I have indexed your financial documents. Ask me anything about revenue figures, growth rates, or risk factors.",
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeSources, setActiveSources] = useState<Source[]>([]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      sender: "user",
      text: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      // POST request hitting our running FastAPI dev server endpoint
      const response = await axios.post("http://127.0.0.1:8000/query", {
        question: input,
      });

      if (response.data.status === "success") {
        const botMessage: Message = {
          id: (Date.now() + 1).toString(),
          sender: "bot",
          text: response.data.answer,
          sources: response.data.sources_used,
        };

        setMessages((prev) => [...prev, botMessage]);
        // Automatically pop the source metadata into the right-hand panel view
        if (
          response.data.sources_used &&
          response.data.sources_used.length > 0
        ) {
          setActiveSources(response.data.sources_used);
        }
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: "bot",
          text: "Error: Could not connect to the backend server. Make sure FastAPI is running on port 8000.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-screen bg-slate-950 text-slate-100 font-sans overflow-hidden">
      {/* LEFT PANEL: Chat Interface */}
      <div className="flex flex-col flex-1 border-r border-slate-800 h-full">
        {/* Header bar */}
        <div className="px-6 py-4 border-b border-slate-800 bg-slate-900/50 flex items-center gap-3">
          <Bot className="text-teal-400 w-6 h-6" />
          <div>
            <h1 className="font-semibold text-lg tracking-wide">
              Financial Copilot
            </h1>
            <p className="text-xs text-slate-400">
              Grounded RAG Research Engine
            </p>
          </div>
        </div>

        {/* Message Feed Stream */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-4 max-w-3xl ${
                msg.sender === "user" ? "ml-auto flex-row-reverse" : "mr-auto"
              }`}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                  msg.sender === "user"
                    ? "bg-teal-600"
                    : "bg-slate-800 border border-slate-700"
                }`}
              >
                {msg.sender === "user" ? (
                  <User size={16} />
                ) : (
                  <Bot size={16} className="text-teal-400" />
                )}
              </div>
              <div
                className={`rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap shadow-lg ${
                  msg.sender === "user"
                    ? "bg-teal-900/40 border border-teal-700 text-teal-50"
                    : "bg-slate-900 border border-slate-800 text-slate-200"
                }`}
              >
                {msg.text}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex gap-4 items-center text-slate-400 text-sm">
              <Loader2 className="animate-spin text-teal-400 w-5 h-5" />
              <span>Scanning pgvector store & executing synthesis...</span>
            </div>
          )}
        </div>

        {/* Bottom Chat Input Bar */}
        <form
          onSubmit={handleSendMessage}
          className="p-4 border-t border-slate-800 bg-slate-900/20"
        >
          <div className="flex gap-2 max-w-4xl mx-auto bg-slate-900 border border-slate-800 rounded-xl p-2 focus-within:border-teal-500 transition-colors">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about revenue trends, segment updates, or financial risk variables..."
              className="flex-1 bg-transparent border-none outline-none px-3 py-2 text-sm text-slate-200 placeholder-slate-500"
            />
            <button
              type="submit"
              disabled={isLoading}
              className="bg-teal-600 hover:bg-teal-500 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded-lg px-4 flex items-center justify-center transition-colors cursor-pointer"
            >
              <Send size={16} />
            </button>
          </div>
        </form>
      </div>

      {/* RIGHT PANEL: Live Source Citation Sidebar */}
      <div className="w-80 bg-slate-900/40 h-full flex flex-col">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center gap-2">
          <BookmarkCheck className="text-teal-400 w-5 h-5" />
          <h2 className="font-medium text-sm tracking-wider uppercase text-slate-400">
            Inspection & Sources
          </h2>
        </div>
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {activeSources.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-600">
              <FileText size={32} className="mb-2 opacity-40" />
              <p className="text-xs">No active citations loaded.</p>
              <p className="text-[10px] mt-1 text-slate-700">
                Submit a query to verify background context.
              </p>
            </div>
          ) : (
            activeSources.map((src, index) => (
              <div
                key={index}
                className="bg-slate-900 border border-slate-800 hover:border-slate-700 transition-colors p-3 rounded-xl flex items-start gap-3"
              >
                <div className="bg-teal-950/60 border border-teal-800 text-teal-400 font-mono text-xs w-6 h-6 rounded flex items-center justify-center shrink-0">
                  {index + 1}
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-medium text-slate-200 truncate">
                    {src.document}
                  </p>
                  <p className="text-[11px] text-teal-400 mt-0.5 font-mono">
                    Page Row Location: {src.page}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
