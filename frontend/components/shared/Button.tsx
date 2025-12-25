/** Reusable button component. */

import React from "react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "ghost";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = "primary",
  size = "md",
  isLoading = false,
  disabled,
  className = "",
  ...props
}) => {
  const baseStyles =
    "inline-flex items-center justify-center font-medium rounded-sm transition-all duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed";

  const variantStyles = {
    primary:
      "bg-[#D4AF37] text-white hover:bg-[#B8860B] focus:ring-[#D4AF37] shadow-sm hover:shadow-md",
    secondary:
      "bg-white text-gray-900 border border-[#D4AF37] hover:bg-[#F5D76E] hover:border-[#B8860B] focus:ring-[#D4AF37]",
    danger:
      "bg-red-600 text-white hover:bg-red-700 focus:ring-red-500 shadow-sm hover:shadow-md",
    ghost:
      "bg-transparent text-[#D4AF37] hover:bg-[#F5D76E]/10 focus:ring-[#D4AF37]",
  };

  const sizeStyles = {
    sm: "px-3 py-1.5 text-sm",
    md: "px-4 py-2 text-base",
    lg: "px-6 py-3 text-lg",
  };

  return (
    <button
      className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <>
          <svg
            className="animate-spin -ml-1 mr-2 h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12c0-1.357.538-2.586 1.414-3.462L6 8.586A7.962 7.962 0 0112 4c1.357 0 2.586.538 3.462 1.414L17.414 6A7.962 7.962 0 0120 12c0 1.357-.538 2.586-1.414 3.462L17.414 17A7.962 7.962 0 0112 20c-1.357 0-2.586-.538-3.462-1.414L6 17.414z"
            />
          </svg>
          Loading...
        </>
      ) : (
        children
      )}
    </button>
  );
};



