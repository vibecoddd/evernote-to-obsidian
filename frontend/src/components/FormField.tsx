import type { ReactNode } from "react";

interface FormFieldProps {
  id: string;
  label: string;
  hint?: string;
  children: ReactNode;
}

export function FormField({ id, label, hint, children }: FormFieldProps) {
  return <div className="form-field"><label htmlFor={id}>{label}</label>{children}{hint && <p id={`${id}-hint`} className="field-hint">{hint}</p>}</div>;
}
