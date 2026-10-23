// Build a calendar (.ics) file for a reminder so it shows up in the phone's own calendar app.
// Generated in the browser; nothing is sent anywhere.

const esc = (s: string) => s.replace(/\\/g, "\\\\").replace(/;/g, "\\;").replace(/,/g, "\\,").replace(/\n/g, "\\n");

export function reminderIcs(r: { id: number | string; title: string; due_date: string; note?: string }): string {
  const d = r.due_date.replace(/-/g, "");
  const next = new Date(`${r.due_date}T00:00:00Z`);
  next.setUTCDate(next.getUTCDate() + 1);
  const end = next.toISOString().slice(0, 10).replace(/-/g, "");
  const stamp = new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "");
  return [
    "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//JanSaathi//Reminders//EN", "CALSCALE:GREGORIAN",
    "BEGIN:VEVENT",
    `UID:jansaathi-reminder-${r.id}@jansaathi`,
    `DTSTAMP:${stamp}`,
    `DTSTART;VALUE=DATE:${d}`,
    `DTEND;VALUE=DATE:${end}`,
    `SUMMARY:${esc(r.title)}`,
    `DESCRIPTION:${esc((r.note ? r.note + "\n" : "") + "Reminder you created in JanSaathi. This is not an official deadline — check the official portal.")}`,
    "BEGIN:VALARM", "TRIGGER:-P1D", "ACTION:DISPLAY", `DESCRIPTION:${esc(r.title)}`, "END:VALARM",
    "END:VEVENT", "END:VCALENDAR", "",
  ].join("\r\n");
}

export function downloadIcs(r: Parameters<typeof reminderIcs>[0]) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([reminderIcs(r)], { type: "text/calendar" }));
  a.download = `jansaathi-reminder-${r.due_date}.ics`;
  a.click();
  URL.revokeObjectURL(a.href);
}
