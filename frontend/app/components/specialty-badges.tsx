import type { Specialty } from "@/types/api";

interface SpecialtyBadgesProps {
  specialties: Specialty[];
  className?: string;
  badgeClassName?: string;
  tone?: "default" | "light";
}

function joinClasses(...classNames: Array<string | undefined>) {
  return classNames.filter(Boolean).join(" ");
}

export default function SpecialtyBadges({
  specialties,
  className,
  badgeClassName,
  tone = "default",
}: SpecialtyBadgesProps) {
  if (!specialties.length) {
    return null;
  }

  const defaultBadgeClassName =
    tone === "light"
      ? "border border-white/25 bg-white/10 text-white"
      : "bg-[#eef4ee] text-[#3f493e]";

  return (
    <div className={joinClasses("flex flex-wrap items-center", className)}>
      {specialties.map((specialty) => (
        <span
          key={specialty.id}
          className={joinClasses(
            "inline-flex rounded-full px-3 py-1 text-xs font-semibold tracking-wide uppercase",
            defaultBadgeClassName,
            badgeClassName,
          )}
        >
          {specialty.name}
        </span>
      ))}
    </div>
  );
}