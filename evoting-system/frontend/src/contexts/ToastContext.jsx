import { createContext, useCallback, useContext, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, XCircle, Info, X } from "lucide-react";

const ToastContext = createContext(null);

const icons = {
  success: <CheckCircle2 size={18} className="text-verified" />,
  error: <XCircle size={18} className="text-alert" />,
  info: <Info size={18} className="text-seal" />,
};

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const dismiss = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toast = useCallback(
    (message, type = "info", duration = 4500) => {
      const id = crypto.randomUUID();
      setToasts((prev) => [...prev, { id, message, type }]);
      if (duration) setTimeout(() => dismiss(id), duration);
      return id;
    },
    [dismiss]
  );

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <div className="fixed bottom-5 right-5 z-[100] flex w-80 flex-col gap-2">
        <AnimatePresence>
          {toasts.map((t) => (
            <motion.div
              key={t.id}
              layout
              initial={{ opacity: 0, x: 24 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="flex items-start gap-2.5 rounded-lg border border-line bg-surface p-3.5 shadow-lg shadow-ink/10"
            >
              {icons[t.type]}
              <p className="flex-1 text-sm text-ink_text">{t.message}</p>
              <button
                onClick={() => dismiss(t.id)}
                className="text-muted hover:text-ink_text"
                aria-label="Dismiss"
              >
                <X size={14} />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within a ToastProvider");
  return ctx;
}
