import Link from "next/link";

export const metadata = {
  title: "Privacy Policy",
  description: "How KwiqBuy collects, uses, and protects your data.",
};

export default function PrivacyPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-12 prose prose-invert prose-brand">
      <h1 className="font-heading text-3xl font-black text-white mb-6">Privacy Policy</h1>
      <p className="text-sm text-gray-400 mb-8">Last updated: {new Date().toLocaleDateString()}</p>
      
      <div className="space-y-6 text-gray-300 text-sm leading-relaxed">
        <section>
          <h2 className="text-white font-bold text-lg mb-2">1. Information We Collect</h2>
          <p>We collect your name, phone number, email address, and delivery address when you place an order. We also collect location data (with your permission) to show you nearby vendors.</p>
        </section>

        <section>
          <h2 className="text-white font-bold text-lg mb-2">2. How We Use Your Data</h2>
          <p>Your data is used to process orders, facilitate delivery, and send you order updates via SMS or email. We do not sell your personal information to third parties.</p>
        </section>

        <section>
          <h2 className="text-white font-bold text-lg mb-2">3. Payment Data</h2>
          <p>KwiqBuy does not store your credit card or Mobile Money PIN. All payment processing is handled securely by our payment partner, Paystack.</p>
        </section>

        <section>
          <h2 className="text-white font-bold text-lg mb-2">4. Your Rights (GDPR)</h2>
          <p>You have the right to request a copy of your data or delete your account at any time. You can do this directly from your Account Profile page.</p>
        </section>

        <section>
          <h2 className="text-white font-bold text-lg mb-2">5. Contact Us</h2>
          <p>If you have any questions about this Privacy Policy, please contact us at hello@kwiqbuy.com.</p>
        </section>
      </div>
    </div>
  );
}