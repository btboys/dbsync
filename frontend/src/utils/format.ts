export function fmtDatetime(val: string | null | undefined): string {
  if (!val) return "-";
  try {
    // Backend returns naive UTC datetime strings (no timezone marker).
    // Append Z to treat as UTC, then get*() methods convert to browser local time.
    const raw = val.includes("T") && !val.endsWith("Z") ? val + "Z" : val;
    const d = new Date(raw);
    if (isNaN(d.getTime())) return val;
    const pad = (n: number) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
  } catch {
    return val;
  }
}

export function fmtBytes(bytes: number | null | undefined): string {
  if (!bytes) return "-";
  const units = ["B", "KB", "MB", "GB"];
  let i = 0;
  let size = bytes;
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024;
    i++;
  }
  return `${size.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}
