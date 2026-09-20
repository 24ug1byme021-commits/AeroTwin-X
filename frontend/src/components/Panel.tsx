import type { ReactNode } from "react";

export function Panel({
  title,
  subtitle,
  children,
  className = "",
  actions,
  icon,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  className?: string;
  actions?: ReactNode;
  icon?: ReactNode;
}) {
  return (
    <section className={`atx-glass atx-glass-hover atx-rise rounded-xl p-4 transition-all duration-300 ${className}`}>
      <div className="mb-3 flex items-start justify-between gap-2">
        <div className="flex items-start gap-2.5">
          <span className="atx-heading-bar mt-0.5" />
          <div>
            <h2 className="flex items-center gap-2 text-[13px] font-semibold uppercase tracking-[0.12em] text-[var(--color-text)]">
              {icon && <span className="text-[var(--color-accent)]">{icon}</span>}
              {title}
            </h2>
            {subtitle && <p className="mt-0.5 text-xs text-[var(--color-text-muted)]">{subtitle}</p>}
          </div>
        </div>
        {actions}
      </div>
      {children}
    </section>
  );
}
