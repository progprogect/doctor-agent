/** Statistics page. */

"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";

interface Stats {
  total_conversations: number;
  ai_active: number;
  needs_human: number;
  human_active: number;
  closed: number;
}

export default function StatsPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStats();
    // Refresh every 10 seconds
    const interval = setInterval(loadStats, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadStats = async () => {
    try {
      const statsData = await api.getStats();
      setStats(statsData);
      setError(null);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to load statistics");
      }
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="bg-red-50 border-l-4 border-red-500 p-4">
        <p className="text-sm text-red-700">{error || "Failed to load statistics"}</p>
      </div>
    );
  }

  const statCards = [
    { label: "Total Conversations", value: stats.total_conversations, color: "gold" },
    { label: "AI Active", value: stats.ai_active, color: "gold-light" },
    { label: "Needs Human", value: stats.needs_human, color: "amber" },
    { label: "Human Active", value: stats.human_active, color: "blue" },
    { label: "Closed", value: stats.closed, color: "gray" },
  ];

  const colorClasses = {
    gold: "bg-[#F5D76E]/10 text-[#B8860B] border-[#D4AF37]/30",
    "gold-light": "bg-[#F5D76E]/20 text-[#B8860B] border-[#D4AF37]/40",
    amber: "bg-[#F59E0B]/10 text-[#D97706] border-[#F59E0B]/30",
    blue: "bg-[#3B82F6]/10 text-[#2563EB] border-[#3B82F6]/30",
    gray: "bg-gray-50 text-gray-700 border-gray-200",
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Statistics</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {statCards.map((card) => (
          <div
            key={card.label}
            className={`p-6 rounded-sm border border-[#D4AF37]/20 bg-white shadow-sm hover:shadow-md transition-all duration-200 ${colorClasses[card.color as keyof typeof colorClasses]}`}
          >
            <p className="text-sm font-medium mb-2">{card.label}</p>
            <p className="text-3xl font-bold">{card.value}</p>
          </div>
        ))}
      </div>
    </div>
  );
}



