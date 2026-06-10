export function formatPriceNoDecimals(
  value: string | number | null | undefined,
  currencySymbol = "$",
): string {
  if (value === null || value === undefined || value === "") {
    return "N/A";
  }

  const numericValue = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(numericValue)) {
    return "N/A";
  }

  const formatted = new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(numericValue);

  return `${currencySymbol}${formatted}`;
}