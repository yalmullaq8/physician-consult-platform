import Link from "next/link";
import Image from "next/image";
import { notFound } from "next/navigation";

import { getPhysicianBySlug } from "@/lib/api";
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
  params: Promise<{ slug: string }>;
}

function DrQaliProfilePage({
  physician,
}: {
  physician: NonNullable<Awaited<ReturnType<typeof getPhysicianBySlug>>>;
}) {
  const photoUrl = getPhysicianPhotoUrl(physician.profile_photo);

  const certificateItems = [
    "Board Certified Oral & Maxillofacial Surgeon",
    "Fellowship in Advanced Implant Dentistry",
    "Certified Digital Smile Design Specialist",
    "International Speaker in Dentofacial Aesthetics",
  ];

  return (
    <div className="container-shell flex flex-1 flex-col gap-6 py-8 md:py-10">
      <Link
        href="/physicians"
        className="w-fit rounded-full border border-[#bfcabb] bg-white px-4 py-2 text-sm font-semibold text-[#00501e] transition hover:bg-[#eef4ee]"
      >
        Back to directory
      </Link>

      <section className="overflow-hidden rounded-3xl border border-[#c9d7c5] bg-[#f7fbf6] shadow-[0_18px_45px_rgba(19,53,39,0.12)]">
        <div className="bg-[radial-gradient(circle_at_15%_20%,#d9efe0_0%,transparent_45%),radial-gradient(circle_at_90%_10%,#d2f4ef_0%,transparent_40%),linear-gradient(135deg,#0b5b31_0%,#157f68_100%)] px-6 py-8 md:px-10 md:py-10">
          <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-xs font-semibold tracking-[0.18em] text-[#dff4e9] uppercase">
                Physician Peer Connect
              </p>
              <h1 className="title-serif mt-3 text-3xl font-semibold text-white md:text-5xl">
                {physician.full_name}
              </h1>
              <p className="mt-2 max-w-2xl text-sm text-[#e8fff4] md:text-base">
                {physician.professional_title || "Dentofacial Consultant"}
              </p>
            </div>
            <Link
              href={`/book/${physician.slug}`}
              className="inline-flex items-center justify-center rounded-full border border-[#d8f2e6] bg-white px-5 py-2.5 text-sm font-semibold text-[#0b5b31] transition hover:bg-[#eefcf4]"
            >
              Book Consultation
            </Link>
          </div>
        </div>

        <div className="grid gap-6 px-6 py-6 md:px-10 md:py-8 lg:grid-cols-[0.85fr_1.15fr]">
          <aside className="rounded-2xl border border-[#d5e2d2] bg-white p-5 shadow-[0_8px_20px_rgba(32,61,47,0.07)]">
            <div className="overflow-hidden rounded-2xl border border-[#dbe8d9] bg-[#f5faf3]">
              {photoUrl ? (
                <img
                  src={photoUrl}
                  alt={`${physician.full_name} profile photo`}
                  className="h-[300px] w-full object-cover"
                />
              ) : (
                <Image
                  src="/stitch/physician-profile.webp"
                  alt="Default physician profile"
                  width={520}
                  height={520}
                  className="h-[300px] w-full object-cover"
                />
              )}
            </div>

            <div className="mt-4 grid grid-cols-2 gap-3">
              <div className="rounded-xl bg-[#edf8ef] p-3">
                <p className="text-[11px] font-semibold tracking-wider text-[#386246] uppercase">Experience</p>
                <p className="mt-1 text-lg font-semibold text-[#1b1b1b]">{physician.years_of_experience}+ years</p>
              </div>
              <div className="rounded-xl bg-[#e9f6f5] p-3">
                <p className="text-[11px] font-semibold tracking-wider text-[#2e6762] uppercase">Consultation</p>
                <p className="mt-1 text-lg font-semibold text-[#1b1b1b]">
                  {physician.consultation_duration_minutes
                    ? `${physician.consultation_duration_minutes} min`
                    : "N/A"}
                </p>
              </div>
            </div>

            <div className="mt-4 rounded-xl border border-[#d5e2d2] bg-[#f9fcf8] p-4">
              <p className="text-xs font-semibold tracking-[0.14em] text-[#3f493e] uppercase">Session Fee</p>
              <p className="mt-1 text-2xl font-semibold text-[#1b1b1b]">
                {formatPriceNoDecimals(physician.consultation_price)}
              </p>
            </div>
          </aside>

          <article className="space-y-5">
            <section className="rounded-2xl border border-[#d5e2d2] bg-white p-5 shadow-[0_8px_20px_rgba(32,61,47,0.07)]">
              <p className="inline-flex rounded-full bg-[#eef4ee] px-3 py-1 text-xs font-semibold tracking-wide text-[#3f493e] uppercase">
                {physician.specialty.name}
              </p>
              <h2 className="mt-3 text-xl font-semibold text-[#1b1b1b]">Physician Profile</h2>
              <p className="mt-2 leading-7 text-[#3f493e]">
                {physician.bio || "Profile biography is being updated."}
              </p>

              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <div className="rounded-xl border border-[#dce8da] bg-[#f9fcf8] p-3">
                  <p className="text-xs font-semibold tracking-wider text-[#3f493e] uppercase">Subspecialty</p>
                  <p className="mt-1 text-sm font-medium text-[#1b1b1b]">
                    {physician.subspecialty || "General specialist care"}
                  </p>
                </div>
                <div className="rounded-xl border border-[#dce8da] bg-[#f9fcf8] p-3">
                  <p className="text-xs font-semibold tracking-wider text-[#3f493e] uppercase">Clinic</p>
                  <p className="mt-1 text-sm font-medium text-[#1b1b1b]">
                    {physician.hospital_or_clinic || "Not specified"}
                  </p>
                </div>
              </div>
            </section>

            <section className="rounded-2xl border border-[#d5e2d2] bg-white p-5 shadow-[0_8px_20px_rgba(32,61,47,0.07)]">
              <h3 className="text-lg font-semibold text-[#1b1b1b]">Certificates & Credentials</h3>
              <p className="mt-2 text-sm text-[#3f493e]">
                Verified academic and professional certifications from the Physician Peer Connect profile.
              </p>
              <ul className="mt-4 space-y-2">
                {certificateItems.map((item) => (
                  <li key={item} className="rounded-xl border border-[#dce8da] bg-[#f7fbf6] px-3 py-2 text-sm text-[#2d4132]">
                    {item}
                  </li>
                ))}
              </ul>
            </section>
          </article>
        </div>
      </section>
    </div>
  );
}

export default async function PhysicianDetailPage({ params }: PageProps) {
  const { slug } = await params;
  const physician = await getPhysicianBySlug(slug);

  if (!physician) {
    notFound();
  }

  if (slug === "drqali") {
    return <DrQaliProfilePage physician={physician} />;
  }

  return (
    <div className="container-shell flex flex-1 flex-col gap-6 py-8 md:py-10">
      <Link
        href="/"
        className="w-fit rounded-full border border-[#bfcabb] bg-white px-4 py-2 text-sm font-semibold text-[#00501e] transition hover:bg-[#eef4ee]"
      >
        Back to homepage
      </Link>

      <section className="overflow-hidden rounded-2xl border border-[#bfcabb] bg-white shadow-[0_14px_40px_rgba(28,67,96,0.09)]">
        <div className="h-28 bg-gradient-to-r from-[#00501e] to-[#14b8a6] md:h-32" />

        <div className="px-5 pb-7 md:px-8 md:pb-9">
          <div className="flex flex-col gap-5 md:flex-row md:items-start md:justify-between">
            <div className="flex items-start gap-4 pt-10 md:pt-12">
              <div className="-mt-24 overflow-hidden rounded-full border-4 border-white bg-white shadow-lg md:-mt-28">
                {getPhysicianPhotoUrl(physician.profile_photo) ? (
                  <img
                    src={getPhysicianPhotoUrl(physician.profile_photo) ?? ""}
                    alt={`${physician.full_name} profile photo`}
                    className="h-[120px] w-[120px] object-cover md:h-[136px] md:w-[136px]"
                  />
                ) : (
                  <Image
                    src="/stitch/physician-profile.webp"
                    alt="Default physician profile"
                    width={120}
                    height={120}
                    className="h-[120px] w-[120px] object-cover md:h-[136px] md:w-[136px]"
                  />
                )}
              </div>

              <div className="pt-1 pb-2 md:pt-2">
                <p className="inline-flex rounded-full bg-[#eef4ee] px-3 py-1 text-xs font-semibold tracking-wide text-[#3f493e] uppercase">
                  {physician.specialty.name}
                </p>
                <h1 className="title-serif mt-3 text-3xl font-semibold text-[#1b1b1b] md:text-5xl">
                  {physician.full_name}
                </h1>
                <p className="mt-1 text-sm text-[#3f493e] md:text-base">
                  {physician.professional_title || "Consulting Physician"}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 md:min-w-[280px]">
              <div className="rounded-xl bg-[#e7fff7] p-3">
                <p className="text-[11px] font-semibold tracking-wider text-[#2f7468] uppercase">Experience</p>
                <p className="mt-1 text-xl font-semibold text-[#1b1b1b]">{physician.years_of_experience}+ yrs</p>
              </div>
              <div className="rounded-xl bg-[#eef4ee] p-3">
                <p className="text-[11px] font-semibold tracking-wider text-[#3f493e] uppercase">Session</p>
                <p className="mt-1 text-xl font-semibold text-[#1b1b1b]">
                  {physician.consultation_duration_minutes
                    ? `${physician.consultation_duration_minutes} min`
                    : "N/A"}
                </p>
              </div>
            </div>
          </div>

          <div className="mt-6 grid gap-6 lg:grid-cols-[1.45fr_0.55fr]">
            <article className="rounded-2xl border border-[#bfcabb] bg-[#ffffff] p-5 md:p-6">
              <h2 className="text-lg font-semibold text-[#1b1b1b]">About</h2>
              <p className="mt-3 leading-7 text-[#3f493e]">
                {physician.bio || "Profile biography is being updated."}
              </p>

              <h3 className="mt-6 text-base font-semibold text-[#1b1b1b]">Expertise summary</h3>
              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                <div className="rounded-xl border border-[#bfcabb] bg-white p-3">
                  <p className="text-xs font-semibold tracking-wider text-[#3f493e] uppercase">Subspecialty</p>
                  <p className="mt-1 text-sm font-medium text-[#1b1b1b]">
                    {physician.subspecialty || "General specialist care"}
                  </p>
                </div>
                <div className="rounded-xl border border-[#bfcabb] bg-white p-3">
                  <p className="text-xs font-semibold tracking-wider text-[#3f493e] uppercase">Clinic</p>
                  <p className="mt-1 text-sm font-medium text-[#1b1b1b]">
                    {physician.hospital_or_clinic || "Not specified"}
                  </p>
                </div>
              </div>
            </article>

            <aside className="rounded-2xl border border-[#bfcabb] bg-[#ffffff] p-5">
              <h3 className="text-base font-semibold text-[#1b1b1b]">Consultation</h3>
              <p className="mt-3 text-sm text-[#3f493e]">Fee</p>
              <p className="text-2xl font-semibold text-[#1b1b1b]">
                {formatPriceNoDecimals(physician.consultation_price)}
              </p>

              <Link
                href={`/book/${physician.slug}`}
                className="mt-6 block w-full rounded-xl bg-[#00501e] px-4 py-3 text-center text-sm font-semibold text-white transition hover:bg-[#006b2b]"
              >
                Book Consultation
              </Link>
            </aside>
          </div>
        </div>
      </section>
    </div>
  );
}


