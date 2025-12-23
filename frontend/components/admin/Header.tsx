/** Header component for admin panel. */

"use client";

import React from "react";

export const Header: React.FC = () => {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Admin Dashboard</h2>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-600">Admin User</span>
          <button className="text-sm text-gray-600 hover:text-gray-900">
            Logout
          </button>
        </div>
      </div>
    </header>
  );
};

