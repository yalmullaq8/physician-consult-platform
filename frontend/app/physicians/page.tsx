import Link from "next/link";

import { getPhysicians, getSpecialties } from "@/lib/api";
import { formatPriceNoDecimals } from "@/lib/formatting";

const BACKEND_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api"
).replace(/\/api\/?$/, "");

function getPhysicianPhotoUrl(photoPath: string | null): string | null {
  if (!photoPath) {
    return null;
  }

  if (photoPath.startsWith("http://") || photoPath.startsWith("https://")) {
    return photoPath;
  }

  if (photoPath.startsWith("/")) {
    return `${BACKEND_BASE_URL}${photoPath}`;
  }

  return `${BACKEND_BASE_URL}/media/${photoPath}`;
}

interface PageProps {
  searchParams: Promise<{
    search?: string;
    specialty?: string;
  }>;
}

export default async function PhysiciansPage({ searchParams }: PageProps) {
  const params = await searchParams;

  const [physicians, specialties] = await Promise.all([
    getPhysicians({ search: params.search, specialty: params.specialty }),
    getSpecialties(),
  ]);

  return (
    <div className="container-shell flex flex-1 flex-col gap-6 py-8 md:py-10">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold tracking-[0.16em] text-[#3f493e] uppercase">
            Directory
          </p>
          <h1 className="title-serif mt-2 text-4xl font-semibold text-[#1b1b1b] md:text-5xl">
            Browse Consultants
          </h1>
          <p className="mt-3 text-sm text-[#3f493e] md:text-base">
            Search verified specialists, compare profiles, and continue to booking.
          </p>
        </div>

        <Link
          href="/"
          className="rounded-full border border-[#bfcabb] bg-white px-4 py-2 text-sm font-semibold text-[#00501e] transition hover:bg-[#eef4ee]"
        >
          Back to landing
        </Link>
      </header>

      <section className="surface-card p-5 md:p-6">
        <form className="grid gap-3 md:grid-cols-[1fr_240px_auto] md:items-end" action="/physicians">
          <div>
            <label
              htmlFor="search"
              className="text-xs font-semibold tracking-[0.16em] text-[#3f493e] uppercase"
            >
              Search
            </label>
            <input
              id="search"
              name="search"
              type="text"
              defaultValue={params.search ?? ""}
              placeholder="Physician name or specialty"
              className="mt-2 w-full rounded-xl border border-[#bfcabb] bg-white px-4 py-2.5 text-sm outline-none ring-[#00501e] transition focus:ring-2"
            />
          </div>

          <div>
            <label
              htmlFor="specialty"
              className="text-xs font-semibold tracking-[0.16em] text-[#3f493e] uppercase"
            >
              Specialty
            </label>
            <select
              id="specialty"
              name="specialty"
              defaultValue={params.specialty ?? ""}
              className="mt-2 w-full rounded-xl border border-[#bfcabb] bg-white px-4 py-2.5 text-sm outline-none ring-[#00501e] transition focus:ring-2"
            >
              <option value="">All specialties</option>
              {specialties.map((specialty) => (
                <option key={specialty.id} value={specialty.slug}>
                  {specialty.name}
                </option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            className="rounded-xl bg-[#00501e] px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-[#006b2b]"
          >
            Apply Filters
          </button>
        </form>
      </section>

      {physicians.length === 0 ? (
        <section className="surface-card p-6 text-center">
          <p className="text-sm text-[#3f493e]">No consultants match your current filters.</p>
        </section>
      ) : (
        <section className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          {physicians.map((physician) => (
            <article
              key={physician.id}
              className="surface-card rounded-[24px] border-[#bfcabb] bg-white/90 p-5"
            >
              <div className="flex items-center gap-3">
                {getPhysicianPhotoUrl(physician.profile_photo) ? (
                  <img
                    src={getPhysicianPhotoUrl(physician.profile_photo) ?? ""}
                    alt={`${physician.full_name} profile photo`}
                    className="h-14 w-14 rounded-full border border-[#d6ded3] object-cover"
                  />
                ) : (
                  <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[#eef4ee] text-base font-semibold text-[#00501e]">
                    {physician.full_name.charAt(0).toUpperCase()}
                  </div>
                )}
                <div>
                  <p className="text-xs font-semibold tracking-[0.16em] text-[#3f493e] uppercase">
                    {physician.specialty.name}
                  </p>
                  <h2 className="mt-1 text-xl font-semibold text-[#1b1b1b]">{physician.full_name}</h2>
                  <p className="mt-1 text-sm text-[#3f493e]">{physician.professional_title}</p>
                </div>
              </div>

              <p className="mt-4 line-clamp-3 text-sm leading-6 text-[#3f493e]">
                {physician.bio || "Profile details available on physician page."}
              </p>

              <div className="mt-5 flex items-center justify-between text-sm">
                <div>
                  <p className="font-semibold text-[#00501e]">
                    {physician.consultation_price
                      ? formatPriceNoDecimals(physician.consultation_price)
                      : "Price on request"}
                  </p>
                  <p className="text-xs text-[#3f493e]">
                    {physician.consultation_duration_minutes
                      ? `${physician.consultation_duration_minutes} min`
                      : "Duration TBD"}
                  </p>
                </div>
                <Link
                  href={`/physicians/${physician.slug}`}
                  className="rounded-lg border border-[#bfcabb] px-3 py-2 font-semibold text-[#00501e] transition hover:bg-[#eef4ee]"
                >
                  View Profile
                </Link>
              </div>
            </article>
          ))}
        </section>
      )}
    </div>
  );
}



