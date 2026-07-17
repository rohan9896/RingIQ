"use client";

import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";

type AuthFieldProps = {
  id: string;
  label: string;
  name: string;
  type: string;
  autoComplete?: string;
  error?: string | null;
  required?: boolean;
};

export function AuthField({
  id,
  label,
  name,
  type,
  autoComplete,
  error,
  required = true,
}: AuthFieldProps) {
  const [isPasswordVisible, setIsPasswordVisible] = useState(false);
  const isPassword = type === "password";
  const inputType = isPassword && isPasswordVisible ? "text" : type;

  return (
    <div>
      <label className="text-sm font-bold text-[#34332f]" htmlFor={id}>
        {label}
      </label>
      <div className="relative mt-2">
        <input
          id={id}
          name={name}
          type={inputType}
          autoComplete={autoComplete}
          required={required}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? `${id}-error` : undefined}
          className={`h-12 w-full border border-[#bdbab1] bg-[#fffefa] px-3 text-sm text-[#171714] outline-none transition placeholder:text-[#9a978f] focus:border-[#d73a2f] focus:ring-2 focus:ring-[#d73a2f]/15 ${isPassword ? "pr-12" : ""}`}
        />
        {isPassword ? (
          <button
            type="button"
            className="absolute right-3 top-1/2 inline-flex size-8 -translate-y-1/2 items-center justify-center text-[#6d6a63] transition hover:text-[#171714] focus:outline-none focus:ring-2 focus:ring-[#d73a2f]/25"
            aria-label={isPasswordVisible ? "Hide password" : "Show password"}
            aria-pressed={isPasswordVisible}
            onClick={() => setIsPasswordVisible((visible) => !visible)}
          >
            {isPasswordVisible ? (
              <EyeOff className="size-4" aria-hidden />
            ) : (
              <Eye className="size-4" aria-hidden />
            )}
          </button>
        ) : null}
      </div>
      {error ? (
        <p id={`${id}-error`} className="mt-2 text-sm text-[#b72c24]">
          {error}
        </p>
      ) : null}
    </div>
  );
}
