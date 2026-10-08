export function Favicon({ url, domain, className = "w-5 h-5" }: { url?: string; domain?: string; className?: string }) {
  const displayLetter = domain ? domain.charAt(0).toUpperCase() : (url ? url.charAt(0).toUpperCase() : 'V');
  return (
    <div className={`${className} bg-white rounded flex items-center justify-center`}>
      <span className="text-xs font-bold text-black">{displayLetter}</span>
    </div>
  );
}