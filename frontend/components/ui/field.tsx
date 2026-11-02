import { forwardRef, type InputHTMLAttributes, type SelectHTMLAttributes, type TextareaHTMLAttributes, useId } from "react";
import { cn } from "@/lib/utils";

const fieldBase =
  "w-full rounded-lg border border-ink-200 bg-white px-3 text-sm text-ink-900 placeholder:text-ink-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30 disabled:bg-ink-50 aria-[invalid=true]:border-red-500";

interface FieldShellProps {
  label: string;
  error?: string;
  hint?: string;
  id?: string;
  children: (id: string, describedBy: string | undefined) => React.ReactNode;
}

/** Accessible wrapper: label, hint and error are linked to the control with aria attributes. */
export function FieldShell({ label, error, hint, id, children }: FieldShellProps) {
  const generated = useId();
  const controlId = id ?? generated;
  const describedBy = [hint ? `${controlId}-hint` : null, error ? `${controlId}-error` : null].filter(Boolean).join(" ") || undefined;
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={controlId} className="text-sm font-medium text-ink-800">
        {label}
      </label>
      {children(controlId, describedBy)}
      {hint && !error ? (
        <p id={`${controlId}-hint`} className="text-xs text-ink-500">
          {hint}
        </p>
      ) : null}
      {error ? (
        <p id={`${controlId}-error`} role="alert" className="text-xs text-red-600">
          {error}
        </p>
      ) : null}
    </div>
  );
}

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  hint?: string;
}

export const TextField = forwardRef<HTMLInputElement, TextFieldProps>(function TextField(
  { label, error, hint, className, id, ...props },
  ref,
) {
  return (
    <FieldShell label={label} error={error} hint={hint} id={id}>
      {(controlId, describedBy) => (
        <input
          ref={ref}
          id={controlId}
          aria-invalid={Boolean(error) || undefined}
          aria-describedby={describedBy}
          className={cn(fieldBase, "h-10", className)}
          {...props}
        />
      )}
    </FieldShell>
  );
});

interface TextAreaFieldProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string;
  error?: string;
  hint?: string;
}

export const TextAreaField = forwardRef<HTMLTextAreaElement, TextAreaFieldProps>(function TextAreaField(
  { label, error, hint, className, id, ...props },
  ref,
) {
  return (
    <FieldShell label={label} error={error} hint={hint} id={id}>
      {(controlId, describedBy) => (
        <textarea
          ref={ref}
          id={controlId}
          aria-invalid={Boolean(error) || undefined}
          aria-describedby={describedBy}
          className={cn(fieldBase, "min-h-[96px] py-2 leading-relaxed", className)}
          {...props}
        />
      )}
    </FieldShell>
  );
});

interface SelectFieldProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  error?: string;
  hint?: string;
  options: { value: string; label: string; disabled?: boolean }[];
}

export const SelectField = forwardRef<HTMLSelectElement, SelectFieldProps>(function SelectField(
  { label, error, hint, options, className, id, ...props },
  ref,
) {
  return (
    <FieldShell label={label} error={error} hint={hint} id={id}>
      {(controlId, describedBy) => (
        <select
          ref={ref}
          id={controlId}
          aria-invalid={Boolean(error) || undefined}
          aria-describedby={describedBy}
          className={cn(fieldBase, "h-10", className)}
          {...props}
        >
          {options.map((o) => (
            <option key={o.value} value={o.value} disabled={o.disabled}>
              {o.label}
            </option>
          ))}
        </select>
      )}
    </FieldShell>
  );
});
