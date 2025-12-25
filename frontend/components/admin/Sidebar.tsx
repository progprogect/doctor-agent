/** Sidebar navigation component. */

"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const navigation = [
  { name: "Agents", href: "/admin/agents", icon: "🤖" },
  { name: "Conversations", href: "/admin/conversations", icon: "💬" },
  { name: "Audit", href: "/admin/audit", icon: "📋" },
  { name: "Stats", href: "/admin/stats", icon: "📊" },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();

  return (
    <div className="w-64 bg-white border-r border-[#D4AF37]/20 flex flex-col">
      <div className="p-6 border-b border-[#D4AF37]/20">
        <h1 className="text-xl font-bold text-[#D4AF37]">Doctor Agent</h1>
        <p className="text-sm text-gray-600">Admin Panel</p>
      </div>
      <nav className="flex-1 p-4 space-y-2">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-2 rounded-sm transition-all duration-200 ${
                isActive
                  ? "bg-[#F5D76E]/20 text-[#B8860B] font-medium border-l-2 border-[#D4AF37]"
                  : "text-gray-700 hover:bg-[#F5D76E]/10 hover:text-[#D4AF37]"
              }`}
            >
              <span className="text-xl">{item.icon}</span>
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
};



