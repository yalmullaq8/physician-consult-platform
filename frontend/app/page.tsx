import Link from "next/link";

import SpecialtyBadges from "@/app/components/specialty-badges";
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

export default async function Home({ searchParams }: PageProps) {
  const params = await searchParams;

  const [physicians, specialties] = await Promise.all([
    getPhysicians({ search: params.search, specialty: params.specialty }),
    getSpecialties(),
  ]);

  const spotlight = physicians.slice(0, 9);

  return (
    <div className="flex flex-1 flex-col bg-[#f9f9f9] pb-20 text-[#1b1b1b]">
      <main className="container-shell mt-8 flex flex-col gap-8">
        <form action="/" className="grid gap-2 rounded-2xl border border-[#bfcabb] bg-white p-3 md:grid-cols-[1fr_auto_auto] md:items-center md:p-4">
          <input
            type="text"
            name="search"
            placeholder="Search by name, specialty, or condition..."
            defaultValue={params.search ?? ""}
            className="w-full rounded-lg border border-[#bfcabb] bg-[#f3f3f3] px-4 py-2.5 text-sm text-[#1b1b1b] outline-none ring-[#00501e] transition focus:ring-2"
          />

          <select
            name="specialty"
            defaultValue={params.specialty ?? ""}
            className="rounded-lg border border-[#bfcabb] bg-[#f3f3f3] px-3 py-2.5 text-sm text-[#1b1b1b] outline-none ring-[#00501e] transition focus:ring-2"
          >
            <option value="">All specialties</option>
            {specialties.map((specialty) => (
              <option key={specialty.id} value={specialty.slug}>
                {specialty.name}
              </option>
            ))}
          </select>

          <button
            type="submit"
            className="rounded-lg bg-[#00501e] px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-[#006b2b]"
          >
            Search
          </button>
        </form>

        <section className="space-y-3">
          <h1 className="title-serif text-4xl font-semibold tracking-tight md:text-5xl">
            Peer Consultations
          </h1>
          <p className="max-w-3xl text-base leading-7 text-[#3f493e] md:text-lg">
            Connect with leading specialists for collaborative medical insights.
          </p>
        </section>

        <section className="flex flex-wrap items-center gap-2">
          <span className="rounded-full border border-[#bfcabb] bg-white px-3 py-1 text-xs font-semibold text-[#3f493e]">
            {specialties.length} specialties
          </span>
          <span className="rounded-full border border-[#bfcabb] bg-white px-3 py-1 text-xs font-semibold text-[#3f493e]">
            {physicians.length} consultants
          </span>
          {specialties.slice(0, 4).map((specialty) => (
            <Link
              key={specialty.id}
              href={`/?search=${encodeURIComponent(params.search ?? "")}&specialty=${specialty.slug}`}
              className="rounded-full border border-[#bfcabb] bg-white px-3 py-1 text-xs font-medium text-[#00501e] transition hover:bg-[#eef4ee]"
            >
              {specialty.name}
            </Link>
          ))}
          {(params.search || params.specialty) && (
            <Link
              href="/"
              className="rounded-full border border-[#00501e] bg-[#eef4ee] px-3 py-1 text-xs font-semibold text-[#00501e]"
            >
              Clear filters
            </Link>
          )}
        </section>

        <section id="consultants" className="space-y-5">
          <div>
            <p className="text-xs font-semibold tracking-[0.16em] text-[#3f493e] uppercase">
              Find a Consultant
            </p>
            <h2 className="title-serif text-3xl font-semibold md:text-4xl">
              Consultant profiles ready for physician-to-physician consults.
            </h2>
          </div>

          {spotlight.length ? (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {spotlight.map((physician) => (
                <article
                  key={physician.id}
                  className="flex h-full flex-col rounded-3xl border border-[#bfcabb] bg-white/80 p-5 backdrop-blur"
                >
                  <div className="mb-4 flex items-center gap-3">
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
                      <SpecialtyBadges specialties={physician.specialties} className="gap-1.5" badgeClassName="bg-[#eef4ee] text-[#00501e]" />
                      <h3 className="mt-1 text-xl font-semibold">{physician.full_name}</h3>
                      <p className="mt-1 text-sm text-[#3f493e]">{physician.professional_title}</p>
                    </div>
                  </div>

                  <div className="mb-4">
                    <p className="text-xs font-semibold tracking-[0.14em] text-[#6f7a6e] uppercase">
                      Available for consultation
                    </p>
                  </div>

                  <p className="line-clamp-4 text-sm leading-6 text-[#3f493e]">
                    {physician.bio || "Profile details available on physician page."}
                  </p>

                  <div className="mt-5 flex items-center justify-between text-sm">
                    <span className="font-semibold text-[#00501e]">
                      {physician.consultation_price
                        ? formatPriceNoDecimals(physician.consultation_price)
                        : "Price on request"}
                    </span>
                    <span className="text-[#6f7a6e]">
                      {physician.consultation_duration_minutes
                        ? `${physician.consultation_duration_minutes} min`
                        : "Duration TBD"}
                    </span>
                  </div>

                  <div className="mt-6 grid grid-cols-2 gap-2">
                    <Link
                      href={`/book/${physician.slug}`}
                      className="rounded-lg bg-[#00501e] px-3 py-2 text-center text-sm font-bold text-white transition hover:bg-[#006b2b]"
                    >
                      Book Now
                    </Link>
                    <Link
                      href={`/dentists/${physician.slug}`}
                      className="rounded-lg border border-[#00501e] px-3 py-2 text-center text-sm font-bold text-[#00501e] transition hover:bg-[#eef4ee]"
                    >
                      More Details
                    </Link>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <div className="rounded-2xl border border-[#bfcabb] bg-white p-8 text-center">
              <h3 className="text-xl font-semibold">No consultants found</h3>
              <p className="mt-2 text-sm text-[#3f493e]">
                Try adjusting your search terms or resetting filters.
              </p>
              <Link
                href="/"
                className="mt-4 inline-flex rounded-lg bg-[#00501e] px-4 py-2 text-sm font-semibold text-white"
              >
                Reset Search
              </Link>
            </div>
          )}

          <div className="flex justify-center">
            <Link
              href="/dentists"
              className="rounded-lg border border-[#00501e] px-5 py-2.5 text-sm font-semibold text-[#00501e] transition hover:bg-[#eef4ee]"
            >
              View Full Consultant Directory
            </Link>
          </div>
        </section>
      </main>
    </div>
  );
}



