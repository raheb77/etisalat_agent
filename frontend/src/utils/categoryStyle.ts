type AccentStyle = {
  border: string;
  bg: string;
  text: string;
};

const NEUTRAL: AccentStyle = {
  border: "border-zinc-200",
  bg: "bg-zinc-100",
  text: "text-zinc-700",
};

const BLUE: AccentStyle = {
  border: "border-blue-200",
  bg: "bg-blue-100",
  text: "text-blue-700",
};

const TEAL: AccentStyle = {
  border: "border-teal-200",
  bg: "bg-teal-100",
  text: "text-teal-700",
};

const RED: AccentStyle = {
  border: "border-red-200",
  bg: "bg-red-100",
  text: "text-red-700",
};

const AMBER: AccentStyle = {
  border: "border-amber-200",
  bg: "bg-amber-100",
  text: "text-amber-700",
};

export function getCategoryAccent(category?: string): AccentStyle {
  const value = category?.trim().toLowerCase() ?? "";
  if (value === "billing") return NEUTRAL;
  if (value === "plans") return BLUE;
  if (value === "network") return TEAL;
  if (value === "fraud") return RED;
  if (value === "legal") return AMBER;
  if (value === "security") return RED;
  return NEUTRAL;
}
