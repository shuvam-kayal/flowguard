import type { Obligation } from "@/types/dashboard";
import { formatINR } from "@/lib/formatters";
export function UpcomingObligations({ items }: { items: Obligation[] }) { return <section className="panel"><p className="eyebrow">Upcoming obligations</p><div className="mt-4 divide-y divide-[#edf1ee]">{items.map((item) => <div key={item.name} className="flex items-center justify-between py-3 text-sm"><div><p className="font-bold">{item.name}</p><p className="text-xs text-[#718078]">Due in {item.dueIn}</p></div><strong>{formatINR(item.amount)}</strong></div>)}</div></section>; }
