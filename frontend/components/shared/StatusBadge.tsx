/** Status badge component for displaying conversation status consistently. */

import React from "react";
import type { ConversationStatus } from "@/lib/types/conversation";
import {
  getStatusDisplay,
  getStatusAriaLabel,
} from "@/lib/utils/statusDisplay";

interface StatusBadgeProps {
  status: ConversationStatus;
  size?: "sm" | "md";
  showIcon?: boolean;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = "md",
  showIcon = true,
  className = "",
}) => {
  const statusDisplay = getStatusDisplay(status);
  const ariaLabel = getStatusAriaLabel(status);

  const sizeClasses = {
    sm: "px-2 py-0.5 text-xs",
    md: "px-2 py-1 text-xs",
  };

  return (
    <span
      className={`inline-flex items-center gap-1 leading-5 font-semibold rounded-sm ${statusDisplay.colorClasses} ${sizeClasses[size]} ${className}`}
      aria-label={ariaLabel}
      role="status"
    >
      {showIcon && <span aria-hidden="true">{statusDisplay.icon}</span>}
      <span>{statusDisplay.label}</span>
    </span>
  );
};
