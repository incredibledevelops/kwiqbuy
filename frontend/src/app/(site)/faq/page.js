import Link from "next/link";
import { MessageCircle } from "lucide-react";

export const metadata = {
  title: "Help Center & FAQ",
  description: "Frequently asked questions about KwiqBuy.",
};

const FAQS = [
  {
    q: "How do I track my order?",
    a: "Once your order is confirmed, you will receive a link to your live tracking page. You can see the vendor's progress and the rider's location in real-time."
  },
  {
    q: "What payment methods do you accept?",
    a: "We accept Mobile Money (MTN, Vodafone, AirtelTigo), Visa/Mastercard, and bank transfers via Paystack."
  },
  {
    q: "Can I order from multiple vendors at once?",
    a: "Currently, you can only order food items together, or retail items together. If you mix food and retail in one cart, you will need to check out separately."
  },
  {
    q: "How do I become a vendor?",
    a: "Click 'Sell on KwiqBuy' at the bottom of the page. Fill out the application, and our team will review it within 2 business days."
  },
  {
    q: "What if my food arrives cold or damaged?",
    a: "Please contact our support team immediately via WhatsApp or phone call. We will resolve the issue and issue a refund if necessary."
  }
];

export default function FAQPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-12">
      <div className="text-center mb-10">
        <h1 className="font-heading text-3xl font-black text-white">Help Center</h1>
        <p className="text-gray-400 mt-2">How can we help you today?</p>
      </div>

      <div className="space-y-4">
        {FAQS.map((faq, i) => (
          <div key={i} className="bg-surface-card border border-surface-border rounded-2xl p-5">
            <h3 className="font-bold text-white mb-2">{faq.q}</h3>
            <p className="text-sm text-gray-400 leading-relaxed">{faq.a}</p>
          </div>
        ))}
      </div>

      <div className="mt-12 p-8 rounded-3xl bg-brand-primary/10 border border-brand-primary/30 text-center">
        <h2 className="font-heading text-xl font-bold text-white">Still need help?</h2>
        <p className="text-sm text-gray-400 mt-2">Our support team is available Mon-Sun, 8am - 10pm.</p>
        <div className="flex justify-center gap-4 mt-6">
          <Link href="https://wa.me/233534634845" className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-bold text-sm transition-colors">
            <MessageCircle className="w-4 h-4" /> WhatsApp Us
          </Link>
          <Link href="/contact" className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-surface-dark border border-surface-border text-white font-bold text-sm hover:border-brand-primary transition-colors">
            Contact Page
          </Link>
        </div>
      </div>
    </div>
  );
}