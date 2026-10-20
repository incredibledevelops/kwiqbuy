import Link from "next/link";
import { Phone, MessageCircle, Mail, MapPin, Clock } from "lucide-react";

export const metadata = {
  title: "Contact us",
  description: "Get in touch with the KwiqBuy team.",
};

export default function ContactPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      <h1 className="font-heading text-4xl font-black text-white">
        Get in touch
      </h1>
      <p className="text-gray-400 mt-2">
        Questions, feedback, partnership enquiries — we're here.
      </p>

      <div className="grid sm:grid-cols-2 gap-4 mt-8">
        <ContactCard
          icon={Phone}
          label="Call us"
          value="0534634845"
          href="tel:0534634845"
        />
        <ContactCard
          icon={MessageCircle}
          label="WhatsApp"
          value="+233 53 463 4845"
          href="https://wa.me/233534634845"
          accent="emerald"
        />
        <ContactCard
          icon={Mail}
          label="Email"
          value="hello@kwiqbuy.com"
          href="mailto:hello@kwiqbuy.com"
        />
        <ContactCard
          icon={Clock}
          label="Support hours"
          value="Mon–Sun: 8:00 – 22:00"
        />
      </div>

      <div className="mt-10 p-6 rounded-2xl bg-surface-card border border-surface-border">
        <div className="flex items-start gap-3">
          <MapPin className="w-5 h-5 text-brand-primary shrink-0 mt-0.5" />
          <div>
            <div className="font-bold text-white">Our offices</div>
            <div className="text-sm text-gray-400 mt-1">
              Accra · Kumasi · Ghana
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function ContactCard({ icon: Icon, label, value, href, accent }) {
  const color = accent === "emerald" ? "text-emerald-400" : "text-brand-primary";
  const inner = (
    <div className="p-5 rounded-2xl bg-surface-card border border-surface-border hover:border-brand-primary/40 transition-colors">
      <div className="w-10 h-10 rounded-xl bg-white/5 border border-surface-border flex items-center justify-center mb-3">
        <Icon className={`w-5 h-5 ${color}`} />
      </div>
      <div className="text-[10px] text-gray-500 uppercase tracking-wider font-bold">
        {label}
      </div>
      <div className="text-white font-bold mt-0.5">{value}</div>
    </div>
  );
  if (href) return <Link href={href}>{inner}</Link>;
  return inner;
}