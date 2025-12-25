/** Main page - Agent selection and chat entry point. */

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import type { Agent } from "@/lib/types/agent";

export default function Home() {
  const router = useRouter();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadAgents = async () => {
      try {
        setIsLoading(true);
        const loadedAgents = await api.listAgents(true);
        setAgents(loadedAgents);
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError("Failed to load agents");
        }
      } finally {
        setIsLoading(false);
      }
    };

    loadAgents();
  }, []);

  const handleStartChat = (agentId: string) => {
    router.push(`/chat/${agentId}`);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-white">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-white p-4">
        <div className="text-center max-w-md">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Error</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-[#D4AF37] text-white rounded-sm hover:bg-[#B8860B] transition-all duration-200 shadow-sm hover:shadow-md"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-white via-[#F5D76E]/5 to-[#D4AF37]/10">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            <span className="text-[#D4AF37]">Doctor</span> Agent
          </h1>
          <p className="text-xl text-gray-600">
            Выберите врача для начала консультации
          </p>
        </div>

        {agents.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-600 mb-4">Нет доступных агентов</p>
            <a
              href="/admin/agents"
              className="text-[#D4AF37] hover:text-[#B8860B] underline transition-colors duration-200"
            >
              Перейти в админ панель
            </a>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
            {agents.map((agent) => (
              <div
                key={agent.agent_id}
                className="bg-white rounded-sm shadow-md border border-[#D4AF37]/20 p-6 hover:shadow-lg hover:border-[#D4AF37]/40 transition-all duration-200 cursor-pointer"
                onClick={() => handleStartChat(agent.agent_id)}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-xl font-semibold text-gray-900 mb-1">
                      {agent.config?.profile?.clinic_display_name ||
                        agent.agent_id}
                    </h3>
                    {agent.config?.profile?.doctor_display_name && (
                      <p className="text-sm text-gray-600">
                        {agent.config.profile.doctor_display_name}
                      </p>
                    )}
                  </div>
                  <div className="text-3xl">👨‍⚕️</div>
                </div>


                <div className="flex items-center justify-between">
                  <span
                    className={`px-3 py-1 rounded-sm text-xs font-medium ${
                      agent.is_active
                        ? "bg-[#F5D76E]/20 text-[#B8860B] border border-[#D4AF37]/30"
                        : "bg-gray-100 text-gray-800"
                    }`}
                  >
                    {agent.is_active ? "Активен" : "Неактивен"}
                  </span>
                  <button className="px-4 py-2 bg-[#D4AF37] text-white rounded-sm hover:bg-[#B8860B] text-sm font-medium transition-all duration-200 shadow-sm hover:shadow-md">
                    Начать чат →
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="text-center mt-12">
          <a
            href="/admin/agents"
            className="text-gray-600 hover:text-[#D4AF37] underline text-sm transition-colors duration-200"
          >
            Админ панель
          </a>
        </div>
      </div>
    </div>
  );
}
