import Navbar from "../../components/public/Navbar";
import Hero from "../../components/public/Hero";
import About from "../../components/public/About";
import Security from "../../components/public/Security";
import HowItWorks from "../../components/public/HowItWorks";
import LiveElections from "../../components/public/LiveElections";
import Footer from "../../components/public/Footer";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-parchment">
      <Navbar />
      <main>
        <Hero />
        <About />
        <Security />
        <LiveElections />
        <HowItWorks />
      </main>
      <Footer />
    </div>
  );
}
