import { useRef, useState, useEffect } from "react";
import { Send, CornerDownLeft } from "lucide-react";

interface MessageInputProps {
  onSend: (text: string) => void;
  disabled: boolean;
  placeholder: string;
}

export function MessageInput({ onSend, disabled, placeholder }: MessageInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [value]);

  function submit() {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  return (
    <div className="border-t border-white/5 bg-ink-900/70 px-4 py-4 backdrop-blur-xl sm:px-8">
      <div className="mx-auto max-w-3xl">
        <div
          className={`group flex items-end gap-2 rounded-2xl border bg-ink-850/70 px-3 py-2.5 transition-all ${
            disabled
              ? "border-white/5 opacity-70"
              : "border-white/10 focus-within:border-brand-500/50 focus-within:shadow-glow"
          }`}
        >
          <textarea
            ref={textareaRef}
            rows={1}
            value={value}
            disabled={disabled}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className="scroll-thin max-h-40 flex-1 resize-none bg-transparent py-1.5 text-sm leading-relaxed text-slate-100 placeholder:text-slate-500 focus:outline-none disabled:cursor-not-allowed"
          />
          <button
            onClick={submit}
            disabled={disabled || !value.trim()}
            className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-brand-500 to-accent-500 text-white shadow-glow transition-all enabled:hover:scale-105 enabled:active:scale-95 disabled:cursor-not-allowed disabled:opacity-40 disabled:shadow-none"
            aria-label="Send message"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
        <p className="mt-2 flex items-center justify-center gap-1 text-[11px] text-slate-500">
          <CornerDownLeft className="h-3 w-3" /> to send · Shift + Enter for new line
        </p>
      </div>
    </div>
  );
}
