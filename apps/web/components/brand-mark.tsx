import Link from "next/link";

export function BrandMark({ inverse = false }: { inverse?: boolean }) {
  return (
    <Link href="/" className="inline-flex items-center gap-3" aria-label="RingIQ home">
      <span
        className={`grid size-9 place-items-center border text-sm font-black ${
          inverse
            ? "border-white/25 bg-[#d73a2f] text-white"
            : "border-[#171714] bg-[#d73a2f] text-white"
        }`}
      >
        輪
      </span>
      <span className={inverse ? "text-white" : "text-[#171714]"}>
        <span className="block text-sm font-bold leading-4">RingIQ</span>
        <span className={`utility-label block text-[0.6rem] ${inverse ? "!text-white/55" : ""}`}>
          Voice intelligence
        </span>
      </span>
    </Link>
  );
}
