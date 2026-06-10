import { notFound } from "next/navigation";

import BookingClient from "./booking-client";
import { getPhysicianBySlug } from "@/lib/api";

interface PageProps {
  params: Promise<{ physicianSlug: string }>;
}

export default async function BookingPage({ params }: PageProps) {
  const { physicianSlug } = await params;
  const physician = await getPhysicianBySlug(physicianSlug);

  if (!physician) {
    notFound();
  }

  return <BookingClient physician={physician} />;
}


