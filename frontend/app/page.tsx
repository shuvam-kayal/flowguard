import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "FlowGuard — Financial Safety for Gig Workers",
  description:
    "FlowGuard helps delivery partners, drivers, and freelancers manage irregular income, track bills, and build a financial safety net — without complicated tools.",
};

// ─── Reusable Section Label ───────────────────────────────────────────────────
function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="inline-block rounded-full bg-[#e8f5ee] px-3 py-1 text-xs font-semibold text-[#087344] tracking-wide">
      {children}
    </p>
  );
}

// ─── Feature Card ─────────────────────────────────────────────────────────────
function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: string;
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-xl border border-[#e5e7eb] bg-white p-5 shadow-sm">
      <div className="mb-4 grid h-10 w-10 place-items-center rounded-xl bg-[#f0faf4] text-xl">
        {icon}
      </div>
      <h3 className="text-sm font-bold text-[#111827]">{title}</h3>
      <p className="mt-2 text-sm leading-relaxed text-[#6b7280]">{description}</p>
    </div>
  );
}

// ─── Testimonial Card ─────────────────────────────────────────────────────────
function TestimonialCard({
  quote,
  name,
  role,
  initial,
}: {
  quote: string;
  name: string;
  role: string;
  initial: string;
}) {
  return (
    <div className="rounded-xl border border-[#e5e7eb] bg-white p-5 shadow-sm">
      <p className="text-sm leading-relaxed text-[#374151]">"{quote}"</p>
      <div className="mt-4 flex items-center gap-3">
        <div className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-[#e8f5ee] text-sm font-bold text-[#087344]">
          {initial}
        </div>
        <div>
          <p className="text-sm font-semibold text-[#111827]">{name}</p>
          <p className="text-xs text-[#9ca3af]">{role}</p>
        </div>
      </div>
    </div>
  );
}

// ─── Stat Box ─────────────────────────────────────────────────────────────────
function StatBox({ value, label }: { value: string; label: string }) {
  return (
    <div className="text-center">
      <p className="text-3xl font-bold text-white sm:text-4xl">{value}</p>
      <p className="mt-1 text-sm text-[#a8c9b8]">{label}</p>
    </div>
  );
}

// ─── Landing Page ─────────────────────────────────────────────────────────────
export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white font-sans text-[#111827] antialiased">

      {/* ── Topnav ──────────────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 border-b border-[#f0f0f0] bg-white/90 backdrop-blur-sm">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-3.5 sm:px-8">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-[#0f3726] text-sm font-black text-white">
              F
            </span>
            <span className="text-base font-bold text-[#111827]">FlowGuard</span>
          </Link>

          {/* Nav links */}
          <nav className="hidden items-center gap-6 sm:flex">
            <a href="#features" className="text-sm text-[#6b7280] hover:text-[#111827] transition-colors">
              Features
            </a>
            <a href="#how-it-works" className="text-sm text-[#6b7280] hover:text-[#111827] transition-colors">
              How it works
            </a>
            <a href="#testimonials" className="text-sm text-[#6b7280] hover:text-[#111827] transition-colors">
              Stories
            </a>
          </nav>

          {/* CTA */}
          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="text-sm font-semibold text-[#374151] hover:text-[#111827] transition-colors"
            >
              Sign in
            </Link>
            <Link
              href="/signup"
              className="rounded-lg bg-[#087344] px-4 py-2 text-sm font-semibold text-white hover:bg-[#065e36] transition-colors"
            >
              Get started free
            </Link>
          </div>
        </div>
      </header>

      {/* ── Hero ────────────────────────────────────────────────────────────── */}
      <section className="mx-auto max-w-6xl px-5 pt-16 pb-20 sm:px-8 sm:pt-24 sm:pb-28 text-center">
        <SectionLabel>Built for gig workers in India</SectionLabel>

        <h1 className="mt-5 text-4xl font-bold leading-tight tracking-tight text-[#111827] sm:text-5xl lg:text-6xl">
          Know exactly how much
          <br />
          <span className="text-[#087344]">you can safely spend today</span>
        </h1>

        <p className="mx-auto mt-6 max-w-xl text-base leading-relaxed text-[#6b7280] sm:text-lg">
          FlowGuard helps delivery partners, drivers, and freelancers manage
          irregular income, stay on top of bills, and build a financial safety
          net — without complicated tools or financial jargon.
        </p>

        <div className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Link
            href="/signup"
            className="w-full rounded-xl bg-[#087344] px-7 py-3.5 text-sm font-bold text-white hover:bg-[#065e36] transition-colors sm:w-auto"
          >
            Start for free — no bank details needed
          </Link>
          <Link
            href="/login"
            className="w-full rounded-xl border border-[#e5e7eb] bg-white px-7 py-3.5 text-sm font-semibold text-[#374151] hover:bg-[#f9fafb] transition-colors sm:w-auto"
          >
            Sign in to dashboard
          </Link>
        </div>

        <p className="mt-4 text-xs text-[#9ca3af]">
          Free to use · Secure · No credit card required
        </p>

        {/* Hero visual — dashboard preview strip */}
        <div className="mx-auto mt-14 max-w-3xl overflow-hidden rounded-2xl border border-[#e5e7eb] bg-[#f9fafb] shadow-xl">
          {/* Fake browser chrome */}
          <div className="flex items-center gap-1.5 border-b border-[#e5e7eb] bg-white px-4 py-3">
            <div className="h-3 w-3 rounded-full bg-[#fca5a5]" />
            <div className="h-3 w-3 rounded-full bg-[#fde68a]" />
            <div className="h-3 w-3 rounded-full bg-[#86efac]" />
            <div className="ml-3 flex-1 rounded-md bg-[#f3f4f6] px-3 py-1 text-xs text-[#9ca3af]">
              flowguard.app/dashboard
            </div>
          </div>
          {/* Mock dashboard content */}
          <div className="p-5 sm:p-6">
            <div className="grid gap-4 sm:grid-cols-[1fr_200px]">
              {/* Safe to spend card mock */}
              <div className="rounded-xl bg-[#0f3726] p-5 text-white">
                <p className="text-[10px] font-semibold uppercase tracking-widest text-[#7daa8f]">
                  Safe to spend today
                </p>
                <p className="mt-3 text-4xl font-bold">₹580</p>
                <p className="mt-1 text-xs text-[#a8c9b8]">
                  after all your bills are covered
                </p>
                <div className="mt-5">
                  <div className="mb-1.5 flex justify-between text-[10px] text-[#7daa8f]">
                    <span>Emergency savings</span>
                    <span>62% of goal</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-white/10">
                    <div className="h-full w-[62%] rounded-full bg-[#35bb7a]" />
                  </div>
                </div>
              </div>
              {/* Right column mocks */}
              <div className="grid gap-3">
                <div className="rounded-xl border border-[#e5e7eb] bg-white p-4">
                  <p className="text-[10px] text-[#9ca3af] uppercase tracking-wider">Health score</p>
                  <p className="mt-1 text-xl font-bold text-[#111827]">72 <span className="text-sm font-normal text-[#9ca3af]">/ 100</span></p>
                  <p className="text-xs text-[#087344] font-semibold">Fair</p>
                  <div className="mt-2 h-1.5 rounded-full bg-[#f0f0f0]">
                    <div className="h-full w-[72%] rounded-full bg-[#d97706]" />
                  </div>
                </div>
                <div className="rounded-xl border border-[#e5e7eb] bg-white p-4">
                  <p className="text-[10px] text-[#9ca3af] uppercase tracking-wider">Income outlook</p>
                  <p className="mt-1 text-sm font-semibold text-[#087344]">☀ Income looks stable</p>
                  <p className="mt-0.5 text-[10px] text-[#6b7280]">Earnings expected to be consistent.</p>
                </div>
              </div>
            </div>
            {/* Bills preview */}
            <div className="mt-4 rounded-xl border border-[#e5e7eb] bg-white p-4">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9ca3af] mb-2">
                Upcoming bills
              </p>
              {[
                { name: "Mobile recharge", amount: "₹299", days: "Due in 3 days", urgent: true },
                { name: "Home loan EMI",   amount: "₹4,200", days: "Due in 11 days", urgent: false },
              ].map((b) => (
                <div key={b.name} className="flex items-center justify-between py-1.5">
                  <div>
                    <p className="text-xs font-semibold text-[#111827]">{b.name}</p>
                    <p className={`text-[10px] ${b.urgent ? "text-[#c0392b] font-semibold" : "text-[#9ca3af]"}`}>
                      {b.days}
                    </p>
                  </div>
                  <strong className={`text-xs ${b.urgent ? "text-[#c0392b]" : "text-[#111827]"}`}>
                    {b.amount}
                  </strong>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── Stats banner ────────────────────────────────────────────────────── */}
      <section className="bg-[#0f3726] py-14">
        <div className="mx-auto max-w-5xl px-5 sm:px-8">
          <div className="grid grid-cols-2 gap-8 sm:grid-cols-4">
            <StatBox value="₹8,000+" label="Average monthly income tracked" />
            <StatBox value="5 min"   label="To set up your account" />
            <StatBox value="100%"    label="Free — no hidden charges" />
            <StatBox value="24/7"    label="Your dashboard, always available" />
          </div>
        </div>
      </section>

      {/* ── Features ────────────────────────────────────────────────────────── */}
      <section id="features" className="mx-auto max-w-6xl px-5 py-20 sm:px-8">
        <div className="text-center">
          <SectionLabel>Features</SectionLabel>
          <h2 className="mt-4 text-3xl font-bold tracking-tight text-[#111827] sm:text-4xl">
            Everything a gig worker needs
          </h2>
          <p className="mx-auto mt-3 max-w-lg text-base text-[#6b7280]">
            Designed for people with irregular income — not salaried employees.
            Simple enough to use every day.
          </p>
        </div>

        <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <FeatureCard
            icon="💰"
            title="Know what you can spend today"
            description="FlowGuard calculates a safe daily spending amount after accounting for upcoming bills, savings goals, and your emergency fund."
          />
          <FeatureCard
            icon="📅"
            title="Never miss a bill"
            description="Track all your EMIs, rent, utilities, and subscriptions in one place. Get alerts before payments are due."
          />
          <FeatureCard
            icon="🛡️"
            title="Build a financial safety net"
            description="Your 'safety net score' tells you how long your savings can cover essentials if your income stops. Build it gradually."
          />
          <FeatureCard
            icon="📈"
            title="Understand your income trend"
            description="See if your gig income is growing, stable, or dropping — and get an estimate of what you'll earn this month."
          />
          <FeatureCard
            icon="🤝"
            title="Check before you borrow"
            description="Before taking a loan, FlowGuard checks if you can handle the repayments. It tries to solve your need without credit first."
          />
          <FeatureCard
            icon="⚡"
            title="Instant setup with bank simulation"
            description="No linking required. We simulate a realistic financial profile from your occupation so you can explore everything right away."
          />
        </div>
      </section>

      {/* ── How it works ────────────────────────────────────────────────────── */}
      <section id="how-it-works" className="bg-[#f9fafb] py-20">
        <div className="mx-auto max-w-6xl px-5 sm:px-8">
          <div className="text-center">
            <SectionLabel>How it works</SectionLabel>
            <h2 className="mt-4 text-3xl font-bold tracking-tight text-[#111827] sm:text-4xl">
              Up and running in minutes
            </h2>
          </div>

          <div className="mt-12 grid gap-6 sm:grid-cols-3">
            {[
              {
                step: "1",
                title: "Create your free account",
                description:
                  "Enter your name, Worker ID, and what type of gig work you do. That's all we need to get started.",
              },
              {
                step: "2",
                title: "See your financial picture",
                description:
                  "FlowGuard instantly builds a realistic financial profile based on typical earnings for your occupation.",
              },
              {
                step: "3",
                title: "Use it every day",
                description:
                  "Check your safe spending limit each morning. Track your bills. See your income trend. Make smarter decisions.",
              },
            ].map(({ step, title, description }) => (
              <div key={step} className="relative">
                <div className="mb-4 grid h-10 w-10 place-items-center rounded-xl bg-[#0f3726] text-base font-bold text-white">
                  {step}
                </div>
                <h3 className="text-base font-bold text-[#111827]">{title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-[#6b7280]">{description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── For who ─────────────────────────────────────────────────────────── */}
      <section className="mx-auto max-w-6xl px-5 py-20 sm:px-8">
        <div className="text-center">
          <SectionLabel>Who is this for?</SectionLabel>
          <h2 className="mt-4 text-3xl font-bold tracking-tight sm:text-4xl">
            If your income isn't the same every month, this is for you
          </h2>
        </div>

        <div className="mt-10 flex flex-wrap justify-center gap-3">
          {[
            "🚗 Cab & auto drivers",
            "🛵 Delivery partners",
            "🔧 Freelance workers",
            "👷 Daily wage workers",
            "📦 Warehouse staff",
            "🧹 Home service providers",
            "📸 Content creators",
            "🏗️ Construction workers",
          ].map((label) => (
            <span
              key={label}
              className="rounded-full border border-[#e5e7eb] bg-white px-5 py-2.5 text-sm font-semibold text-[#374151] shadow-sm"
            >
              {label}
            </span>
          ))}
        </div>
      </section>

      {/* ── Testimonials ────────────────────────────────────────────────────── */}
      <section id="testimonials" className="bg-[#f9fafb] py-20">
        <div className="mx-auto max-w-6xl px-5 sm:px-8">
          <div className="text-center">
            <SectionLabel>Stories</SectionLabel>
            <h2 className="mt-4 text-3xl font-bold tracking-tight sm:text-4xl">
              Workers like you use FlowGuard
            </h2>
          </div>

          <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            <TestimonialCard
              quote="Before FlowGuard, I had no idea how much I could safely spend. Now I check it every morning before I start my shift."
              name="Ravi Kumar"
              role="Swiggy delivery partner, Bengaluru"
              initial="R"
            />
            <TestimonialCard
              quote="It told me not to take a loan last month because my buffer was too low. I listened. Two weeks later my income dropped. I was protected."
              name="Priya Nair"
              role="Freelance photographer, Mumbai"
              initial="P"
            />
            <TestimonialCard
              quote="I always forgot when my EMI was due. Now FlowGuard shows me exactly how many days are left and how much I need to keep aside."
              name="Mohammed Farooq"
              role="Ola cab driver, Hyderabad"
              initial="M"
            />
          </div>
        </div>
      </section>

      {/* ── Final CTA ───────────────────────────────────────────────────────── */}
      <section className="bg-[#0f3726] py-20">
        <div className="mx-auto max-w-2xl px-5 text-center sm:px-8">
          <h2 className="text-3xl font-bold text-white sm:text-4xl">
            Take control of your money today
          </h2>
          <p className="mx-auto mt-4 max-w-md text-base text-[#a8c9b8]">
            Free to use. Takes 5 minutes to set up. No bank details required.
            Start making confident financial decisions.
          </p>

          <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
            <Link
              href="/signup"
              className="w-full rounded-xl bg-[#35bb7a] px-8 py-3.5 text-sm font-bold text-[#0f3726] hover:bg-[#2ea86d] transition-colors sm:w-auto"
            >
              Create your free account
            </Link>
            <Link
              href="/login"
              className="w-full rounded-xl border border-white/20 px-8 py-3.5 text-sm font-semibold text-white hover:bg-white/5 transition-colors sm:w-auto"
            >
              I already have an account
            </Link>
          </div>
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────────────────────────── */}
      <footer className="border-t border-[#f0f0f0] bg-white py-10">
        <div className="mx-auto max-w-6xl px-5 sm:px-8">
          <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-between">
            {/* Logo */}
            <div className="flex items-center gap-2">
              <span className="grid h-7 w-7 place-items-center rounded-lg bg-[#0f3726] text-xs font-black text-white">
                F
              </span>
              <span className="text-sm font-bold text-[#111827]">FlowGuard</span>
            </div>

            <p className="text-xs text-[#9ca3af]">
              Financial resilience for gig workers. Free to use.
            </p>

            <div className="flex items-center gap-5">
              <Link href="/login" className="text-xs text-[#9ca3af] hover:text-[#374151] transition-colors">
                Sign in
              </Link>
              <Link href="/signup" className="text-xs text-[#9ca3af] hover:text-[#374151] transition-colors">
                Get started
              </Link>
            </div>
          </div>

          <div className="mt-6 border-t border-[#f0f0f0] pt-6 text-center">
            <p className="text-xs text-[#c4c9ce]">
              © {new Date().getFullYear()} FlowGuard. Built for India's gig economy workers.
            </p>
          </div>
        </div>
      </footer>

    </div>
  );
}
