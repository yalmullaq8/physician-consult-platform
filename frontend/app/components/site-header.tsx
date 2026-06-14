import Image from "next/image";
import Link from "next/link";

export default function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-[#bfcabb] bg-[#f9f9f9]/95 backdrop-blur">
      <div className="container-shell flex flex-wrap items-center justify-between gap-3 py-4">
        <Link href="/" className="flex items-center gap-2 whitespace-nowrap text-[#00501e]">
          <Image
            src="/360_logo_vector.svg"
            alt="360 logo"
            width={44}
            height={44}
            className="h-11 w-11 rounded-full border border-[#d6ded3] bg-white object-cover"
            priority
          />
          <span className="text-2xl font-bold tracking-tight">360.dentist</span>
        </Link>

        <nav className="flex items-center gap-2">
          <Link
            href="/physicians"
            className="rounded px-3 py-2 text-sm font-medium text-[#00501e] transition hover:bg-[#eef4ee]"
          >
            Dentists
          </Link>
        </nav>
      </div>
    </header>
  );
}