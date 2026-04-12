import { ShieldCheck, Cpu, MessageSquare, TrendingUp, Code, Database, Globe } from 'lucide-react'

export default function About() {
  const technologies = [
    { name: 'React.js', icon: Globe, desc: 'Interactive frontend with Vite & TailwindCSS' },
    { name: 'FastAPI', icon: Code, desc: 'High-performance async Python backend' },
    { name: 'PostgreSQL', icon: Database, desc: 'Relational database hosted on Neon.tech' },
    { name: 'Gemini AI', icon: MessageSquare, desc: 'LLM for human-readable product summaries' },
    { name: 'Scikit-Learn', icon: Cpu, desc: 'Custom ML classifier models (Random Forest, LogReg)' },
    { name: 'Docker', icon: Globe, desc: 'Containerised environment for seamless deployment' },
  ]

  const features = [
    { title: 'Fake Review Detection', icon: ShieldCheck, desc: 'Our ML pipeline spots manipulation and calculates a Trust Score.' },
    { title: 'Sentiment Analysis', icon: TrendingUp, desc: 'Dual-engine sentiment analysis (VADER + ML) tracks genuine opinions.' },
    { title: 'Value for Money', icon: Cpu, desc: 'Aggregates price and sentiment metrics to tell you if it`s a bargain.' }
  ]

  const team = [
    { name: 'Vanshika', role: 'Full Stack Engineer & ML', bio: 'Architecting the core machine learning pipelines, building out the Python FastAPI backends, and designing the glassmorphism frontend.' }
  ]

  return (
    <div className="animate-fade-in max-w-5xl mx-auto space-y-16 py-8">
      
      {/* Header section */}
      <section className="text-center max-w-3xl mx-auto">
        <h1 className="text-4xl md:text-5xl font-extrabold mb-6 tracking-tight bg-gradient-to-r from-brand-cyan via-white to-brand-lavender bg-clip-text text-transparent">
          About ReviewLens
        </h1>
        <p className="text-lg text-gray-300 leading-relaxed">
          ReviewLens is an AI-powered product analyser designed to cut through the noise of e-commerce. 
          By combining large language models with custom machine learning classifiers, we help consumers identify fake reviews, understand true sentiment, and make informed purchasing decisions on Amazon.
        </p>
      </section>

      {/* How it works */}
      <section className="glass p-8 md:p-12">
        <h2 className="text-2xl font-bold mb-8 text-white flex items-center gap-3">
          <Cpu className="text-brand-cyan w-6 h-6" /> How it Works
        </h2>
        <div className="grid md:grid-cols-3 gap-8">
          {features.map((feat, i) => (
            <div key={i} className="relative group">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-brand-cyan to-brand-lavender rounded-2xl opacity-0 group-hover:opacity-20 transition duration-500 blur"></div>
              <div className="relative bg-brand-navy p-6 rounded-2xl border border-white/5 h-full">
                <feat.icon className="w-8 h-8 text-brand-cyan mb-4" />
                <h3 className="text-lg font-semibold mb-2">{feat.title}</h3>
                <p className="text-gray-400 text-sm leading-relaxed">{feat.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Technologies */}
      <section>
        <h2 className="text-2xl font-bold mb-8 text-center text-white">Powered by Modern Tech</h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {technologies.map((tech, i) => (
            <div key={i} className="glass p-5 flex gap-4 items-start hover:-translate-y-1 transition-transform cursor-default">
              <div className="bg-white/5 p-3 rounded-xl shadow-inner">
                <tech.icon className="w-5 h-5 text-brand-lavender" />
              </div>
              <div>
                <h4 className="font-semibold text-gray-200">{tech.name}</h4>
                <p className="text-xs text-gray-500 mt-1">{tech.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Team */}
      <section className="glass p-8 md:p-12 text-center relative overflow-hidden">
        <div className="absolute top-0 right-0 -mr-20 -mt-20 w-64 h-64 bg-brand-cyan/10 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute bottom-0 left-0 -ml-20 -mb-20 w-64 h-64 bg-brand-lavender/10 rounded-full blur-3xl pointer-events-none"></div>
        
        <h2 className="text-2xl font-bold mb-10 text-white relative z-10">Meet the Builder</h2>
        <div className="grid md:grid-cols-1 gap-8 max-w-md mx-auto relative z-10">
          {team.map((member, i) => (
            <div key={i} className="bg-brand-navy/50 p-6 rounded-2xl border border-white/10 shadow-lg">
              <div className="w-16 h-16 mx-auto bg-gradient-to-tr from-brand-cyan to-brand-lavender rounded-full p-0.5 mb-4 shadow-[0_0_15px_rgba(110,231,249,0.3)]">
                <div className="w-full h-full bg-brand-navy rounded-full flex items-center justify-center text-xl font-bold text-white">
                  {member.name.charAt(0)}
                </div>
              </div>
              <h3 className="text-xl font-bold text-white">{member.name}</h3>
              <p className="text-brand-cyan text-sm font-medium mb-3">{member.role}</p>
              <p className="text-gray-400 text-sm leading-relaxed">{member.bio}</p>
            </div>
          ))}
        </div>
      </section>

    </div>
  )
}
