import Link from "next/link";
import Image from "next/image";
import { notFound } from "next/navigation";

import LectureCarousel from "@/app/components/lecture-carousel";
import SpecialtyBadges from "@/app/components/specialty-badges";
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
  const heroImage = "/drqali_hero_img.jpeg";
  const certificatesImage = "/certificates_image.png";

  const clinicalScopeCards = [
    {
      title: "ORTHODONTICS & DENTOFACIAL ORTHOPEDICS",
      lines: ["Fixed appliances", "Aligner Therapy", "Growth Modification", "Surgical Orthodontics"],
      image:
        "/orthodontics_img.png",
    },
    {
      title: "PERIODONTICS",
      lines: ["Gum Disease Management", "Periodontal Surgery", "Gum Grafting", "Dental Implant Therapy"],
      image:
        "/periodontics_resized.jpg",
    },
    {
      title: "DENTAL EDUCATION",
      lines: ["Demystifying dentistry", "Clinical workflow insights", "Patient-first communication"],
      image:
        "/insta_resized.jpg",
    },
    {
      title: "OUTREACH",
      lines: ["Local oral health campaigns", "International volunteer care", "Community education"],
      image:
        "/outreach_zoom_resize.jpg",
    },
  ];

  return (
    <div className="bg-[#f9f9f9] text-[#1b1b1b]">
      <div className="mx-auto w-full max-w-[1280px] px-4 py-8 md:px-12">
    

        <section className="relative mb-12 h-[560px] overflow-hidden rounded-xl">
          <img
            src={heroImage}
            alt={`${physician.full_name} hero portrait`}
            className="h-full w-full object-cover object-center md:object-top"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/25 to-transparent" />
          <div className="absolute inset-x-0 bottom-0 p-7 md:p-12">
            <div className="max-w-2xl">
              {/* <SpecialtyBadges specialties={physician.specialties} tone="light" className="mb-4 gap-2" /> */}
              <h2 className="text-4xl font-bold text-white md:text-5xl">Welcome!</h2>
              <p className="mt-4 text-sm leading-relaxed text-white/95 md:text-base">
                I&apos;m Dr. Mohammad Qali, a quadruple board-certified Periodontist and Orthodontist.
                Whether you&apos;re seeking expert clinical guidance, advanced dental treatment solutions, or simply exploring a comprehensive 360° approach to oral health and smile transformation, you&apos;ve come to the right place.
              </p>
              <a
                href="https://www.instagram.com/dr_qali/"
                target="_blank"
                rel="noopener noreferrer"
                className="mt-5 inline-flex text-white transition hover:opacity-80"
                aria-label="Instagram profile"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect width="20" height="20" x="2" y="2" rx="5" ry="5" />
                  <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
                  <line x1="17.5" x2="17.51" y1="6.5" y2="6.5" />
                </svg>
              </a>
              <div className="mt-7">
                <Link
                  href={`/book/${physician.slug}`}
                  className="inline-flex rounded-full bg-[#00501e] px-8 py-3 text-sm font-bold uppercase tracking-wide text-white transition hover:scale-[1.02]"
                >
                  Book Consultation
                </Link>
              </div>
            </div>
          </div>
        </section>

        <div className="mb-14 overflow-hidden border-y border-[#bfcabb] py-4">
          <div className="flex w-max animate-[marquee_20s_linear_infinite] gap-8 whitespace-nowrap text-xs font-bold tracking-[0.18em] text-[#00501e] uppercase">
            <span>General Dentistry</span>
            <span>Orthodontics</span>
            <span>Aligners</span>
            <span>Braces</span>
            <span>Interceptive Orthodontics</span>
            <span>Surgical Orthodontics</span>
            <span>General Dentistry</span>
            <span>Orthodontics</span>
            <span>Aligners</span>
            <span>Braces</span>
            <span>Interceptive Orthodontics</span>
            <span>Surgical Orthodontics</span>
          </div>
        </div>

        <div className="space-y-8">
          <section>
            <div className="overflow-hidden rounded-xl border border-[#bfcabb] bg-[#f3f5f2] p-2 md:p-3">
              <img
                src={certificatesImage}
                alt="Professional certificates and board certifications"
                className="h-auto w-full rounded-lg object-contain"
              />
            </div>
          </section>

          <section className="rounded-xl border border-[#bfcabb] bg-white p-6 md:p-8">
            <span className="block text-xs font-bold tracking-[0.16em] text-[#00501e] uppercase">About</span>
            <div className="mt-4 flex flex-col gap-6 md:flex-row md:items-start">
              {getPhysicianPhotoUrl(physician.profile_photo) ? (
                <img
                  src={getPhysicianPhotoUrl(physician.profile_photo) ?? ""}
                  alt={`${physician.full_name} portrait`}
                  className="h-32 w-32 rounded-xl object-cover"
                />
              ) : (
                <Image
                  src="/stitch/physician-profile.webp"
                  alt="Default physician portrait"
                  width={128}
                  height={128}
                  className="h-32 w-32 rounded-xl object-cover"
                />
              )}

              <div>
                <p className="leading-7 text-[#1b1b1b]">
                  {physician.bio ||
                    "Profile biography is being updated. Dr. Qali combines postgraduate orthodontic training with comprehensive general dentistry, focusing on individualized treatment planning and long-term oral health outcomes."}
                </p>
                <p className="mt-4 leading-7 text-[#1b1b1b]">
                  As a certified aligner provider, he manages interdisciplinary and complex cases while maintaining a conservative, evidence-based clinical style.
                </p>
                <button className="mt-5 rounded-full bg-[#1b1b1b] px-6 py-2 text-xs font-bold tracking-wide text-white uppercase">
                  Full Bio
                </button>
              </div>
            </div>
          </section>

          <section>
            <div className="mb-10 flex justify-center">
              <Link
                href={`/book/${physician.slug}`}
                className="rounded-full bg-[#00501e] px-10 py-4 text-sm font-bold uppercase tracking-wide text-white transition hover:scale-[1.02]"
              >
                Book Consultation
              </Link>
            </div>

            <div className="mb-8">
              <LectureCarousel />
            </div>

            <h3 className="mb-6 text-3xl font-semibold text-[#1b1b1b]">Clinical Scope</h3>
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
              {clinicalScopeCards.map((card) => (
                <article
                  key={card.title}
                  className="overflow-hidden rounded-xl border border-[#bfcabb] bg-white transition hover:-translate-y-1 hover:shadow-lg"
                >
                  <div className="h-40 overflow-hidden">
                    <img src={card.image} alt={`${card.title} visual`} className="h-full w-full object-cover" />
                  </div>
                  <div className="p-5">
                    <h4 className="mb-3 text-xs font-bold tracking-[0.12em] text-[#00501e] uppercase">{card.title}</h4>
                    <ul className="space-y-1.5 text-sm text-[#3f493e]">
                      {card.lines.map((line) => (
                        <li key={line}>{line}</li>
                      ))}
                    </ul>
                  </div>
                </article>
              ))}
            </div>
          </section>
        </div>
      </div>

      <style>{`
        @keyframes marquee {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
      `}</style>
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
                <SpecialtyBadges specialties={physician.specialties} className="gap-1.5" />
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


