import Link from "next/link";

export default function Footer() {
  const year = new Date().getFullYear();
  return (
    <footer className="bg-black/40 border-t border-surface-border mt-12">
      <div className="max-w-7xl mx-auto px-4 py-10 grid grid-cols-2 sm:grid-cols-4 gap-8 text-xs text-gray-400">
        <div className="col-span-2 sm:col-span-1">
          <Link href="/" className="inline-flex items-center gap-2 mb-4">
            <div className="w-8 h-8 rounded-lg gradient-brand flex items-center justify-center text-white font-black">
              K
            </div>
            <span className="font-heading text-base font-bold text-white">
              KwiqBuy
            </span>
          </Link>
          <p className="leading-relaxed">
            Food and shopping, delivered fast. Serving Accra &amp; Kumasi.
          </p>
        </div>

        <div>
          <div className="font-bold text-white uppercase tracking-wider text-[10px] mb-3">
            Shop
          </div>
          <ul className="space-y-2">
            <li>
              <Link href="/food" className="hover:text-brand-primary transition-colors">
                Food
              </Link>
            </li>
            <li>
              <Link href="/shop" className="hover:text-brand-primary transition-colors">
                Shop
              </Link>
            </li>
            <li>
              <Link href="/vendors" className="hover:text-brand-primary transition-colors">
                Vendors
              </Link>
            </li>
            <li>
              <Link href="/account/orders" className="hover:text-brand-primary transition-colors">
                My orders
              </Link>
            </li>
          </ul>
        </div>

        <div>
          <div className="font-bold text-white uppercase tracking-wider text-[10px] mb-3">
            Company
          </div>
          <ul className="space-y-2">
            <li>
              <Link href="/about" className="hover:text-brand-primary transition-colors">
                About
              </Link>
            </li>
            <li>
              <Link href="/contact" className="hover:text-brand-primary transition-colors">
                Contact
              </Link>
            </li>
          </ul>
        </div>

        <div>
          <div className="font-bold text-white uppercase tracking-wider text-[10px] mb-3">
            Support
          </div>
          <ul className="space-y-2">
            <li>
              <a href="tel:0534634845" className="hover:text-brand-primary transition-colors">
                0534634845
              </a>
            </li>
            <li>
              <a
                href="https://wa.me/233534634845"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-emerald-400 transition-colors"
              >
                WhatsApp
              </a>
            </li>
          </ul>
        </div>
      </div>
      <div className="border-t border-surface-border">
        <div className="max-w-7xl mx-auto px-4 py-4 text-center text-[11px] text-gray-500">
          © {year} KwiqBuy Ghana
        </div>
      </div>
    </footer>
  );
}