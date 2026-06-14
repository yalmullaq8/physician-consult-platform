"use client";

import Image from "next/image";
import { useEffect, useState } from "react";

const SLIDES = [
  {
    src: "/lecture_image.jpeg",
    alt: "Dr. Qali presenting a lecture",
  },
  {
    src: "/lecture_image2.jpeg",
    alt: "Dr. Qali during a clinical education session",
  },
];

const INTERVAL_MS = 4000;

export default function LectureCarousel() {
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % SLIDES.length);
    }, INTERVAL_MS);

    return () => window.clearInterval(timer);
  }, []);

  return (
    <section className="rounded-xl border border-[#bfcabb] bg-white p-3 md:p-4">
      <div className="relative aspect-[16/9] overflow-hidden rounded-lg">
        {SLIDES.map((slide, index) => (
          <Image
            key={slide.src}
            src={slide.src}
            alt={slide.alt}
            fill
            sizes="(max-width: 768px) 100vw, 70vw"
            priority={index === 0}
            className={`object-cover transition-opacity duration-700 ${
              index === currentIndex ? "opacity-100" : "opacity-0"
            }`}
          />
        ))}
      </div>

      <div className="mt-3 flex justify-center gap-2">
        {SLIDES.map((slide, index) => (
          <button
            key={`${slide.src}-dot`}
            type="button"
            onClick={() => setCurrentIndex(index)}
            className={`h-2.5 w-2.5 rounded-full transition ${
              index === currentIndex ? "bg-[#00501e]" : "bg-[#c8d5c4] hover:bg-[#9eb39a]"
            }`}
            aria-label={`Go to slide ${index + 1}`}
          />
        ))}
      </div>
    </section>
  );
}