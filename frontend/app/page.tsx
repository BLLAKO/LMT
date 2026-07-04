import Header from "@/components/landing/Header";
import Hero from "@/components/landing/Hero";
import AudienceSection from "@/components/landing/AudienceSection";
import FeatureHighlights from "@/components/landing/FeatureHighlights";
import DownloadCta from "@/components/landing/DownloadCta";
import Footer from "@/components/landing/Footer";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-page">
      <Header />
      <main>
        <Hero />
        <AudienceSection />
        <FeatureHighlights />
        <DownloadCta />
      </main>
      <Footer />
    </div>
  );
}
