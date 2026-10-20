import Link from "next/link";
import { ArrowRight, Sparkles, Utensils, ShoppingBag, Heart } from "lucide-react";

export const metadata = {
  title: "About KwiqBuy",
  description:
    "KwiqBuy is a multi-vendor marketplace built for Ghana. Food and shopping, delivered fast.",
};

const DIFFERENTIATORS = [
  {
    icon: Utensils,
    title: "Food vendors",
    body: "Discover restaurants near you. Real-time order tracking from kitchen to doorstep.",
  },
  {
    icon: ShoppingBag,
    title: "Retail sellers",
    body: "Electronics, groceries, fashion. Nationwide shipping from verified sellers.",
  },
  {
    icon: Heart,
    title: "Local first",
    body: "Built in Ghana, for Ghana. Every naira, cedi, and order stays in the community.",
  },
];

export default function AboutPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      <div className="inline-flex items-center gap-1.5 text-brand-primary font-bold text-xs uppercase tracking-widest bg-brand-primary/10 px-3 py-1 rounded-full border border-brand-primary/20 mb-4">
        <Sparkles className="w-3.5 h-3.5" />
        Our story
      </div>

      <h1 className="font-heading text-4xl sm:text-5xl font-black text-white leading-tight">
        The marketplace
        <br />
        <span className="text-gradient-brand">built for Ghana.</span>
      </h1>

      <p className="text-gray-300 text-base sm:text-lg mt-6 leading-relaxed">
        KwiqBuy started with a simple idea: one app for everything you need,
        from food to everyday shopping, delivered fast. We partner with local
        restaurants and sellers so they can reach more customers without
        building their own logistics.
      </p>

      <p className="text-gray-300 text-base sm:text-lg mt-4 leading-relaxed">
        Our platform handles payments, delivery, and support — so vendors focus
        on what they do best: making great products.
      </p>

      <div className="grid sm:grid-cols-3 gap-4 mt-10">
        {DIFFERENTIATORS.map(({ icon: Icon, title, body }) => (
          <div
            key={title}
            className="p-5 rounded-2xl bg-surface-card border border-surface-border"
          >
            <div className="w-10 h-10 rounded-xl bg-brand-primary/10 border border-brand-primary/20 flex items-center justify-center mb-3">
              <Icon className="w-5 h-5 text-brand-primary" />
            </div>
            <div className="font-bold text-white">{title}</div>
            <p className="text-xs text-gray-400 mt-1.5 leading-relaxed">
              {body}
            </p>
          </div>
        ))}
      </div>

      <div className="mt-12 p-8 rounded-3xl bg-gradient-to-br from-brand-primary/20 to-brand-accent/20 border border-brand-primary/30 text-center">
        <h2 className="font-heading text-2xl font-black text-white">
          Want to sell on KwiqBuy?
        </h2>
        <p className="text-gray-300 mt-2 text-sm">
          Reach thousands of customers. Get paid weekly. We handle the rest.
        </p>
        <Link
          href="/vendor/apply"
          className="inline-flex items-center gap-2 mt-5 px-6 py-3 rounded-xl bg-brand-primary hover:bg-brand-primaryDark text-white font-bold text-sm transition-colors"
        >
          Apply to sell
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    </div>
  );
}