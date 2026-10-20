import Link from "next/link";
import {
  ArrowRight,
  Utensils,
  ShoppingBag,
  Store,
  Truck,
  MapPin,
  Clock,
} from "lucide-react";

export default function HomePage() {
  return (
    <>
      {/* HERO */}
      <section className="py-16 sm:py-20">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-brand-primary/10 border border-brand-primary/30 text-brand-primary text-xs font-bold uppercase tracking-wider mb-6">
            <Truck className="w-3.5 h-3.5" />
            Now live in Accra & Kumasi
          </div>
          <h1 className="font-heading text-5xl sm:text-6xl font-black leading-tight text-white">
            One app.
            <br />
            <span className="text-gradient-brand">Food and shopping.</span>
          </h1>
          <p className="text-gray-300 mt-6 max-w-2xl mx-auto text-base sm:text-lg leading-relaxed">
            Order from nearby restaurants, or shop retail from sellers across
            Ghana. Fast delivery to your door.
          </p>
        </div>
      </section>

      {/* TWO MAIN TABS */}
      <section className="max-w-5xl mx-auto px-4 pb-16">
        <div className="grid sm:grid-cols-2 gap-6">
          <CategoryCard
            href="/food"
            icon={Utensils}
            eyebrow="Restaurants near you"
            title="Order food"
            description="Fresh meals from local restaurants and kitchens, delivered hot in under 40 minutes."
            bullets={[
              { icon: MapPin, text: "Discover by location" },
              { icon: Clock, text: "Track in real time" },
            ]}
            accent="primary"
          />
          <CategoryCard
            href="/shop"
            icon={ShoppingBag}
            eyebrow="Nationwide delivery"
            title="Shop products"
            description="Electronics, groceries, fashion and more — from verified sellers, shipped to you."
            bullets={[
              { icon: Store, text: "Multiple vendors" },
              { icon: Truck, text: "Nationwide shipping" },
            ]}
            accent="accent"
          />
        </div>
      </section>

      {/* WHY KwiqBuy */}
      <section className="border-t border-surface-border py-12">
        <div className="max-w-5xl mx-auto px-4 grid sm:grid-cols-3 gap-6">
          <Feature
            icon={Utensils}
            title="Food, fast"
            message="Restaurants near you. Real-time order tracking."
          />
          <Feature
            icon={ShoppingBag}
            title="Shop, nationwide"
            message="Electronics, groceries, fashion — shipped to your door."
          />
          <Feature
            icon={Store}
            title="Sell on KwiqBuy"
            message="List products, receive orders, get paid weekly."
            href="/vendor/apply"
          />
        </div>
      </section>
    </>
  );
}

function CategoryCard({
  href,
  icon: Icon,
  eyebrow,
  title,
  description,
  bullets,
  accent,
}) {
  const accentClasses =
    accent === "primary"
      ? {
          ring: "hover:border-brand-primary/60",
          icon: "text-brand-primary bg-brand-primary/10 border-brand-primary/30",
          button: "gradient-brand text-white",
        }
      : {
          ring: "hover:border-brand-accent/60",
          icon: "text-brand-accent bg-brand-accent/10 border-brand-accent/30",
          button: "bg-brand-accent hover:bg-brand-accentDark text-white",
        };

  return (
    <Link
      href={href}
      className={`group block p-6 sm:p-8 rounded-3xl bg-surface-card border border-surface-border ${accentClasses.ring} transition-colors`}
    >
      <div
        className={`w-14 h-14 rounded-2xl flex items-center justify-center border mb-5 ${accentClasses.icon}`}
      >
        <Icon className="w-7 h-7" />
      </div>

      <div className="text-[10px] uppercase tracking-widest font-bold text-gray-500 mb-2">
        {eyebrow}
      </div>
      <div className="font-heading text-2xl font-black text-white">
        {title}
      </div>
      <p className="text-sm text-gray-400 mt-2 leading-relaxed">
        {description}
      </p>

      {bullets?.length > 0 && (
        <div className="mt-4 space-y-1.5">
          {bullets.map((b, i) => {
            const BIcon = b.icon;
            return (
              <div
                key={i}
                className="inline-flex items-center gap-2 text-xs text-gray-400"
              >
                <BIcon className="w-3.5 h-3.5 text-gray-500" />
                {b.text}
              </div>
            );
          })}
        </div>
      )}

      <div
        className={`mt-6 inline-flex items-center gap-2 px-5 py-3 rounded-2xl font-bold text-sm transition-transform group-hover:translate-x-0.5 ${accentClasses.button}`}
      >
        Explore
        <ArrowRight className="w-4 h-4" />
      </div>
    </Link>
  );
}

function Feature({ icon: Icon, title, message, href }) {
  const body = (
    <div className="p-6 rounded-2xl bg-surface-card border border-surface-border hover:border-brand-primary/40 transition-colors">
      <div className="w-12 h-12 rounded-xl bg-brand-primary/10 border border-brand-primary/20 flex items-center justify-center mb-4">
        <Icon className="w-6 h-6 text-brand-primary" />
      </div>
      <div className="font-heading text-lg font-bold text-white">{title}</div>
      <p className="text-sm text-gray-400 mt-2 leading-relaxed">{message}</p>
    </div>
  );
  if (href) return <Link href={href}>{body}</Link>;
  return body;
}