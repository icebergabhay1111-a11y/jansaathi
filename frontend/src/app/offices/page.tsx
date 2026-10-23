"use client";
import { useState } from "react";
import { Building2, ExternalLink, Info, Landmark, LocateFixed, MapPin, Navigation, Search } from "lucide-react";
import { ErrorBox, Notice } from "@/components/ui";
import { useApp } from "@/lib/providers";

/*
 * Nearest office locator.
 * Data: OpenStreetMap (via the public Overpass API) — community-mapped, so coverage of CSCs and
 * taluk offices is incomplete. Your location is sent from your browser directly to OpenStreetMap
 * services; JanSaathi's server never receives it.
 */

type Kind = "service_centre" | "taluk" | "collectorate" | "panchayat" | "municipal" | "post_office" | "government";
type Place = { id: string; name: string; kind: Kind; lat: number; lon: number; dist: number; address?: string; phone?: string; hours?: string };

const KIND_LABEL: Record<Kind, { en: string; hi: string; tone: string }> = {
  service_centre: { en: "Citizen service centre (CSC / e-Sevai)", hi: "जन सेवा केंद्र (CSC / ई-सेवा)", tone: "bg-leaf-50 text-leaf-dark" },
  taluk: { en: "Taluk / Tehsil office", hi: "तहसील / तालुका कार्यालय", tone: "bg-navy-100 text-navy-800" },
  collectorate: { en: "Collectorate / district office", hi: "कलेक्ट्रेट / ज़िला कार्यालय", tone: "bg-navy-100 text-navy-800" },
  panchayat: { en: "Panchayat / block office", hi: "पंचायत / ब्लॉक कार्यालय", tone: "bg-saffron-50 text-saffron-dark" },
  municipal: { en: "Municipal office", hi: "नगर निगम / नगरपालिका कार्यालय", tone: "bg-saffron-50 text-saffron-dark" },
  post_office: { en: "Post office (Aadhaar, savings, many schemes)", hi: "डाकघर (आधार, बचत, कई योजनाएँ)", tone: "bg-ivory-dark text-ink" },
  government: { en: "Other government office", hi: "अन्य सरकारी कार्यालय", tone: "bg-ivory-dark text-ink" },
};

const FILTERS: { id: "all" | Kind; en: string; hi: string }[] = [
  { id: "all", en: "All", hi: "सभी" },
  { id: "service_centre", en: "CSC / e-Sevai", hi: "CSC / ई-सेवा" },
  { id: "taluk", en: "Taluk / Tehsil", hi: "तहसील" },
  { id: "panchayat", en: "Panchayat / Block", hi: "पंचायत / ब्लॉक" },
  { id: "municipal", en: "Municipal", hi: "नगर निकाय" },
  { id: "post_office", en: "Post office", hi: "डाकघर" },
];

// State names for citizen service centres (helps both matching and the user's own search).
const CENTRE_NAMES = "common service cent|(^| )csc( |$)|e-?sevai|e-?seva|jan seva|seva kendra|sewa kendra|lok seva|lok sewa|meeseva|mee seva|akshaya|aaple sarkar|e-?mitra|atal seva|bangla sahayata|karnataka one|bangalore one|sahaj|vasudha";
const OFFICE_NAMES = "taluk|tahsil|tehsil|tahasil|mandal revenue|revenue office|collectorate|collector office|district magistrate|block development|(^| )bdo( |$)|panchayat|municipal|corporation office|nagar nigam|nagar palika|zone office|ward office";

const OVERPASS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"];

function classify(tags: Record<string, string>): Kind {
  const n = `${tags.name || ""} ${tags["name:en"] || ""} ${tags.operator || ""}`.toLowerCase();
  if (new RegExp(CENTRE_NAMES, "i").test(n)) return "service_centre";
  if (/taluk|tahsil|tehsil|tahasil|mandal revenue|revenue office/.test(n)) return "taluk";
  if (/collectorate|collector|district magistrate/.test(n)) return "collectorate";
  if (/panchayat|block development|\bbdo\b/.test(n)) return "panchayat";
  if (/municipal|corporation|nagar nigam|nagar palika|ward office|zone office/.test(n) || tags.amenity === "townhall") return "municipal";
  if (tags.amenity === "post_office") return "post_office";
  return "government";
}

function haversine(a: [number, number], b: [number, number]) {
  const R = 6371, toR = Math.PI / 180;
  const dLat = (b[0] - a[0]) * toR, dLon = (b[1] - a[1]) * toR;
  const x = Math.sin(dLat / 2) ** 2 + Math.cos(a[0] * toR) * Math.cos(b[0] * toR) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(x));
}

async function overpass(query: string) {
  let last: unknown;
  for (const url of OVERPASS) {
    try {
      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 30000);
      const r = await fetch(url, { method: "POST", body: new URLSearchParams({ data: query }), signal: ctrl.signal });
      clearTimeout(timer);
      if (r.ok) return (await r.json()) as { elements: { id: number; type: string; lat?: number; lon?: number; center?: { lat: number; lon: number }; tags?: Record<string, string> }[] };
      last = new Error(`map service error ${r.status}`);
    } catch (e) { last = e; }
  }
  throw last instanceof Error ? last : new Error("map service unavailable");
}

export default function OfficesPage() {
  const { lang } = useApp();
  const hi = lang === "hi";
  const [place, setPlace] = useState("");
  const [radius, setRadius] = useState(10);
  const [origin, setOrigin] = useState<{ lat: number; lon: number; label: string } | null>(null);
  const [items, setItems] = useState<Place[] | null>(null);
  const [filter, setFilter] = useState<"all" | Kind>("all");
  const [state, setState] = useState<"idle" | "locating" | "searching">("idle");
  const [err, setErr] = useState<string | null>(null);

  async function search(lat: number, lon: number, label: string, r = radius) {
    setOrigin({ lat, lon, label }); setState("searching"); setErr(null); setItems(null);
    const m = Math.round(r * 1000);
    const q = `[out:json][timeout:25];
(
  nwr(around:${m},${lat},${lon})["office"="government"];
  nwr(around:${m},${lat},${lon})["amenity"="townhall"];
  nwr(around:${m},${lat},${lon})["amenity"="post_office"];
  nwr(around:${m},${lat},${lon})["name"~"${CENTRE_NAMES}|${OFFICE_NAMES}",i];
);
out center tags 300;`;
    try {
      const data = await overpass(q);
      const seen = new Set<string>();
      const list: Place[] = [];
      for (const el of data.elements) {
        const tags = el.tags || {};
        const la = el.lat ?? el.center?.lat, lo = el.lon ?? el.center?.lon;
        const name = tags["name:en"] || tags.name;
        if (la == null || lo == null || !name) continue;
        const key = `${name.toLowerCase()}|${la.toFixed(3)}|${lo.toFixed(3)}`;
        if (seen.has(key)) continue;
        seen.add(key);
        const addr = [tags["addr:housenumber"], tags["addr:street"], tags["addr:suburb"] || tags["addr:village"], tags["addr:city"] || tags["addr:district"], tags["addr:postcode"]].filter(Boolean).join(", ");
        list.push({ id: `${el.type}/${el.id}`, name, kind: classify(tags), lat: la, lon: lo, dist: haversine([lat, lon], [la, lo]), address: addr || undefined, phone: tags.phone || tags["contact:phone"], hours: tags.opening_hours });
      }
      list.sort((a, b) => a.dist - b.dist);
      setItems(list);
    } catch {
      setErr("The OpenStreetMap service did not respond. Please try again in a minute, or use the official links below.");
    } finally { setState("idle"); }
  }

  function useMyLocation() {
    setErr(null);
    if (!navigator.geolocation) { setErr("Location is not available in this browser. Type your town or PIN code instead."); return; }
    setState("locating");
    navigator.geolocation.getCurrentPosition(
      (p) => search(p.coords.latitude, p.coords.longitude, hi ? "आपका स्थान" : "your location"),
      (e) => { setState("idle"); setErr(e.code === 1 ? "Location permission was denied. Type your town, area or PIN code instead." : "Could not get your location. Type your town or PIN code instead."); },
      { enableHighAccuracy: false, timeout: 15000, maximumAge: 300000 },
    );
  }

  async function findPlace(e: React.FormEvent) {
    e.preventDefault();
    const q = place.trim();
    if (q.length < 3) { setErr("Type a town, area or 6-digit PIN code."); return; }
    setErr(null); setState("searching");
    try {
      const params = new URLSearchParams({ format: "jsonv2", limit: "1", countrycodes: "in", q: /^\d{6}$/.test(q) ? `${q}, India` : q });
      const r = await fetch(`https://nominatim.openstreetmap.org/search?${params}`, { headers: { Accept: "application/json" } });
      const res = r.ok ? ((await r.json()) as { lat: string; lon: string; display_name: string }[]) : [];
      if (!res.length) { setState("idle"); setErr(`We couldn't find "${q}". Try a nearby town name or a 6-digit PIN code.`); return; }
      await search(Number(res[0].lat), Number(res[0].lon), res[0].display_name.split(",").slice(0, 3).join(","));
    } catch {
      setState("idle"); setErr("The place search did not respond. Please try again, or use your location.");
    }
  }

  const shown = (items || []).filter((p) => filter === "all" || p.kind === filter);
  const busy = state !== "idle";

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <h1 className="font-display text-4xl text-navy-900">{hi ? "नज़दीकी सरकारी कार्यालय" : "Find a nearby office"}</h1>
      <p className="mt-2 max-w-3xl text-muted">{hi ? "जन सेवा केंद्र (CSC), ई-सेवा केंद्र, तहसील/तालुका, पंचायत और डाकघर खोजें — जहाँ प्रमाण पत्र, आवेदन और कई योजनाएँ उपलब्ध हैं।" : "Find Common Service Centres (CSC), e-Sevai centres, taluk/tehsil offices, panchayat offices and post offices — where you can apply for certificates and many schemes."}</p>

      <div className="card mt-6 grid gap-4 p-5">
        <div className="flex flex-wrap items-center gap-3">
          <button onClick={useMyLocation} disabled={busy} className="btn btn-saffron"><LocateFixed size={18} aria-hidden />{state === "locating" ? (hi ? "स्थान खोजा जा रहा है…" : "Getting location…") : (hi ? "मेरे स्थान का उपयोग करें" : "Use my location")}</button>
          <span className="text-sm text-muted">{hi ? "या" : "or"}</span>
          <form onSubmit={findPlace} className="flex min-w-0 flex-1 gap-2" role="search">
            <label htmlFor="place" className="sr-only">Town, area or PIN code</label>
            <input id="place" className="input" value={place} onChange={(e) => setPlace(e.target.value)} placeholder={hi ? "शहर, इलाका या PIN कोड" : "Town, area or PIN code (e.g. Katpadi or 632014)"} />
            <button className="btn btn-primary" disabled={busy}><Search size={16} aria-hidden /><span className="sr-only sm:not-sr-only">{hi ? "खोजें" : "Search"}</span></button>
          </form>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <label htmlFor="radius" className="font-semibold">{hi ? "दूरी" : "Within"}</label>
          <select id="radius" className="input !min-h-10 w-auto" value={radius} onChange={(e) => { const r = Number(e.target.value); setRadius(r); if (origin) search(origin.lat, origin.lon, origin.label, r); }}>
            {[3, 5, 10, 20].map((r) => <option key={r} value={r}>{r} km</option>)}
          </select>
          <p className="flex items-center gap-1 text-xs text-muted"><Info size={13} aria-hidden />{hi ? "आपका स्थान सीधे OpenStreetMap को जाता है, जनसाथी सर्वर को नहीं।" : "Your location goes directly from your browser to OpenStreetMap — never to JanSaathi's server."}</p>
        </div>
      </div>

      {err && <div className="mt-4"><ErrorBox message={err} /></div>}
      {state === "searching" && <p role="status" className="mt-6 text-muted">{hi ? "कार्यालय खोजे जा रहे हैं…" : "Searching offices near"} {origin?.label}…</p>}

      {items && (
        <section aria-labelledby="res-h" className="mt-6">
          <h2 id="res-h" className="font-display text-2xl text-navy-900">{shown.length} {hi ? "स्थान" : "places"} {hi ? "पास में" : "near"} {origin?.label}</h2>
          <div className="mt-3 flex flex-wrap gap-2" role="group" aria-label="Filter by office type">
            {FILTERS.map((f) => {
              const n = f.id === "all" ? items.length : items.filter((p) => p.kind === f.id).length;
              return <button key={f.id} onClick={() => setFilter(f.id)} aria-pressed={filter === f.id} className={`rounded-full px-3 py-1.5 text-sm font-semibold ${filter === f.id ? "bg-navy-900 text-white" : "border border-line bg-white text-navy-900"}`}>{hi ? f.hi : f.en} · {n}</button>;
            })}
          </div>
          {shown.length === 0 ? (
            <div className="mt-4"><Notice tone="warn">{hi ? "OpenStreetMap में इस क्षेत्र के लिए कोई कार्यालय दर्ज नहीं है। दूरी बढ़ाएँ या नीचे दिए आधिकारिक लिंक देखें।" : "No offices of this type are mapped in OpenStreetMap here. Try a larger distance, or use the official links below."}</Notice></div>
          ) : (
            <ul className="mt-4 grid gap-3 md:grid-cols-2">
              {shown.slice(0, 60).map((p) => (
                <li key={p.id} className="card flex flex-col gap-2 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-2">
                      {p.kind === "service_centre" ? <Building2 size={18} className="mt-0.5 shrink-0 text-leaf-dark" aria-hidden /> : <Landmark size={18} className="mt-0.5 shrink-0 text-navy-700" aria-hidden />}
                      <p className="font-semibold leading-snug text-navy-900">{p.name}</p>
                    </div>
                    <span className="shrink-0 text-sm font-bold text-navy-900">{p.dist < 1 ? `${Math.round(p.dist * 1000)} m` : `${p.dist.toFixed(1)} km`}</span>
                  </div>
                  <span className={`self-start rounded-full px-2 py-0.5 text-xs font-semibold ${KIND_LABEL[p.kind].tone}`}>{hi ? KIND_LABEL[p.kind].hi : KIND_LABEL[p.kind].en}</span>
                  {p.address && <p className="flex gap-1 text-sm text-muted"><MapPin size={14} className="mt-0.5 shrink-0" aria-hidden />{p.address}</p>}
                  {p.hours && <p className="text-xs text-muted">Hours (as mapped): {p.hours}</p>}
                  <div className="mt-auto flex flex-wrap gap-3 pt-1 text-sm font-semibold">
                    <a className="inline-flex items-center gap-1 text-navy-700 underline" target="_blank" rel="noopener noreferrer"
                      href={`https://www.google.com/maps/dir/?api=1&destination=${p.lat},${p.lon}`}><Navigation size={14} aria-hidden />{hi ? "रास्ता" : "Directions"}</a>
                    <a className="inline-flex items-center gap-1 text-navy-700 underline" target="_blank" rel="noopener noreferrer"
                      href={`https://www.openstreetmap.org/${p.id}`}>OpenStreetMap<ExternalLink size={12} aria-hidden /></a>
                    {p.phone && <a className="text-navy-700 underline" href={`tel:${p.phone.split(";")[0].replace(/\s/g, "")}`}>{p.phone.split(";")[0]}</a>}
                  </div>
                </li>
              ))}
            </ul>
          )}
          <p className="mt-3 text-xs text-muted">{hi ? "मानचित्र डेटा © OpenStreetMap योगदानकर्ता। जाने से पहले समय की पुष्टि करें।" : "Map data © OpenStreetMap contributors (ODbL). Community-mapped and may be incomplete or out of date — call or check timings before you go."}</p>
        </section>
      )}

      <section aria-labelledby="off-h" className="card mt-8 p-5">
        <h2 id="off-h" className="font-display text-xl text-navy-900">{hi ? "आधिकारिक स्रोत" : "Official sources"}</h2>
        <ul className="mt-3 space-y-2 text-sm">
          <li><a className="inline-flex items-center gap-1 font-semibold text-navy-700 underline" href="https://csc.gov.in" target="_blank" rel="noopener noreferrer">Common Services Centres — csc.gov.in<ExternalLink size={12} aria-hidden /></a> <span className="text-muted">— the national CSC programme (MeitY).</span></li>
          <li><a className="inline-flex items-center gap-1 font-semibold text-navy-700 underline" href="https://www.tnesevai.tn.gov.in" target="_blank" rel="noopener noreferrer">Tamil Nadu e-Sevai — tnesevai.tn.gov.in<ExternalLink size={12} aria-hidden /></a> <span className="text-muted">— e-Sevai services in Tamil Nadu.</span></li>
          <li><a className="inline-flex items-center gap-1 font-semibold text-navy-700 underline" href="https://services.india.gov.in" target="_blank" rel="noopener noreferrer">National Government Services Portal<ExternalLink size={12} aria-hidden /></a> <span className="text-muted">— links to every state&apos;s service portal.</span></li>
        </ul>
        <p className="mt-3 text-sm text-muted">{hi ? "राज्यों में केंद्रों के नाम अलग होते हैं: ई-सेवा (तमिलनाडु), अक्षय (केरल), मी-सेवा (आंध्र/तेलंगाना), आपले सरकार (महाराष्ट्र), ई-मित्र (राजस्थान), जन सेवा केंद्र (उत्तर प्रदेश)।" : "Centres have different names in different states: e-Sevai (Tamil Nadu), Akshaya (Kerala), MeeSeva (Andhra Pradesh/Telangana), Aaple Sarkar (Maharashtra), e-Mitra (Rajasthan), Jan Seva Kendra (Uttar Pradesh)."}</p>
      </section>
    </div>
  );
}
