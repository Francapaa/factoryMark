import type { Competitor } from "@/types/analysis";

export default function CompetitorsTable({ competitors }: { competitors: Competitor[] }) {
  return (
    <table className="w-full text-left text-sm">
      <thead>
        <tr className="text-zinc-500">
          <th className="py-2 pr-4">Nombre</th>
          <th className="py-2 pr-4">Rating</th>
          <th className="py-2 pr-4">Reviews</th>
          <th className="py-2 pr-4">Distancia</th>
          <th className="py-2">Dirección</th>
        </tr>
      </thead>
      <tbody>
        {competitors.map((c) => (
          <tr key={c.place_id} className="border-t border-zinc-200 dark:border-zinc-800">
            <td className="py-2 pr-4 font-medium">{c.name}</td>
            <td className="py-2 pr-4">{c.rating ?? "—"}</td>
            <td className="py-2 pr-4">{c.user_ratings_total}</td>
            <td className="py-2 pr-4">
              {c.distance_m != null ? `${Math.round(c.distance_m)} m` : c.source === "web" ? "web" : "—"}
            </td>
            <td className="py-2">{c.address}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
