import { Outfit, Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";
import Providers from "./providers";
import ServiceWorker from "@/components/site/ServiceWorker";

const outfit = Outfit({
  variable: "--font-outfit",
  subsets: ["latin"],
  weight: ["600", "700", "800", "900"],
  display: "swap",
});

const jakarta = Plus_Jakarta_Sans({
  variable: "--font-jakarta",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  display: "swap",
});

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";
const GOOGLE_VERIFICATION = process.env.NEXT_PUBLIC_GOOGLE_VERIFICATION;

export const metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "KwiqBuy | Food and shopping delivered fast",
    template: "%s | KwiqBuy",
  },
  description:
    "KwiqBuy is a multi-vendor marketplace. Order food from nearby restaurants, or shop retail from sellers across Ghana. Pay with MoMo or card.",
  keywords: [
    "KwiqBuy",
    "marketplace Ghana",
    "food delivery Accra",
    "order online Ghana",
    "multi-vendor marketplace",
  ],
  authors: [{ name: "KwiqBuy", url: SITE_URL }],
  alternates: { canonical: SITE_URL },
  openGraph: {
    type: "website",
    locale: "en_GH",
    url: SITE_URL,
    siteName: "KwiqBuy",
    title: "KwiqBuy | Food and shopping delivered fast",
    description:
      "Order food from nearby restaurants or shop retail from sellers across Ghana.",
    images: [
      { url: "/og-image.png", width: 1200, height: 630, alt: "KwiqBuy" },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "KwiqBuy",
    description: "Food and shopping, delivered fast.",
    images: ["/og-image.png"],
  },
  manifest: "/manifest.json",
  icons: {
    icon: "/favicon.ico",
    apple: "/apple-touch-icon.png",
  },
  ...(GOOGLE_VERIFICATION
    ? { verification: { google: GOOGLE_VERIFICATION } }
    : {}),
};

export const viewport = {
  themeColor: "#2563EB",
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
};

export default function RootLayout({ children }) {
  return (
    <html
      lang="en-GH"
      className={`${outfit.variable} ${jakarta.variable}`}
      suppressHydrationWarning
    >
      <body className="antialiased" suppressHydrationWarning>
        <Providers>{children}</Providers>
        <ServiceWorker />
      </body>
    </html>
  );
}