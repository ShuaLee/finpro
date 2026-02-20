import * as React from "react";

import { cn } from "../../lib/utils";

export type FloatingInputProps = React.InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  containerClassName?: string;
};

const FloatingInput = React.forwardRef<HTMLInputElement, FloatingInputProps>(
  ({ className, containerClassName, label, id, ...props }, ref) => {
    const generatedId = React.useId();
    const inputId = id ?? generatedId;

    return (
      <div className={cn("relative", containerClassName)}>
        <input
          id={inputId}
          ref={ref}
          placeholder=" "
          className={cn(
            "peer flex h-14 w-full rounded-md border border-input bg-background px-3 pb-2 pt-6 text-sm font-medium ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
            className,
          )}
          {...props}
        />
        <label
          htmlFor={inputId}
          className="pointer-events-none absolute left-3 top-2 text-xs font-medium text-muted-foreground transition-all peer-placeholder-shown:top-1/2 peer-placeholder-shown:-translate-y-1/2 peer-placeholder-shown:text-sm peer-focus:top-2 peer-focus:translate-y-0 peer-focus:text-xs"
        >
          {label}
        </label>
      </div>
    );
  },
);

FloatingInput.displayName = "FloatingInput";

export { FloatingInput };
