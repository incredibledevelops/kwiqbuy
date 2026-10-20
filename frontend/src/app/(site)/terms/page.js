import Link from "next/link";

export const metadata = {
  title: "Terms of Service",
  description: "KwiqBuy terms and conditions for using our platform.",
};

export default function TermsPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-12 prose prose-invert prose-brand">
      <h1 className="font-heading text-3xl font-black text-white mb-6">Terms of Service</h1>
      <p className="text-sm text-gray-400 mb-8">Last updated: {new Date().toLocaleDateString()}</p>
      
      <div className="space-y-6 text-gray-300 text-sm leading-relaxed">
        <section>
          <h2 className="text-white font-bold text-lg mb-2">1. Acceptance of Terms</h2>
          <p>By accessing or using KwiqBuy, you agree to be bound by these Terms of Service. If you do not agree to these terms, please do not use our platform.</p>
        </section>

        <section>
          <h2 className="text-white font-bold text-lg mb-2">2. Use of the Platform</h2>
          <p>KwiqBuy is a multi-vendor marketplace connecting customers with local food and retail vendors in Ghana. We do not prepare food or manufacture products; we facilitate the ordering, payment, and delivery process.</p>
        </section>

        <section>
          <h2 className="text-white font-bold text-lg mb-2">3. Payments and Refunds</h2>
          <p>All payments are processed securely via Paystack (Mobile Money, Card, or Bank Transfer). Refunds are handled on a case-by-case basis. If there is an issue with your order, please contact support within 24 hours.</p>
        </section>

        <section>
          <h2 className="text-white font-bold text-lg mb-2">4. Vendor Responsibilities</h2>
          <p>Vendors are solely responsible for the quality, safety, and accuracy of the products they list. Vendors must comply with all local health and safety regulations.</p>
        </section>

        <section>
          <h2 className="text-white font-bold text-lg mb-2">5. Limitation of Liability</h2>
          <p>KwiqBuy is not liable for any indirect, incidental, or consequential damages arising from your use of the platform, including but not limited to issues with food quality or delivery delays.</p>
        </section>
      </div>

      <div className="mt-12 pt-8 border-t border-surface-border">
        <Link href="/contact" className="text-brand-primary font-bold hover:underline">
          Questions? Contact Support
        </Link>
      </div>
    </div>
  );
}