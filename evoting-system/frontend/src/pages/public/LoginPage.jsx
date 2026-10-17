import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import AuthLayout from "../../layouts/AuthLayout";
import FormField, { inputClass } from "../../components/ui/FormField";
import PasswordInput from "../../components/ui/PasswordInput";
import Button from "../../components/ui/Button";

const ROLES = [
  { value: "voter", label: "Voter" },
  { value: "election_admin", label: "Election Admin" },
  { value: "super_admin", label: "Super Admin" },
];

const REDIRECTS = {
  voter: "/voter",
  election_admin: "/admin",
  super_admin: "/admin",
};

export default function LoginPage() {
  const [role, setRole] = useState("voter");
  const [serverError, setServerError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm();

  const onSubmit = async (data) => {
    setServerError(null);
    setIsSubmitting(true);
    try {
      const user = await login(data.email, data.password, role);
      const redirectTo = location.state?.from ?? REDIRECTS[user.role] ?? "/";
      navigate(redirectTo, { replace: true });
    } catch (err) {
      setServerError(err.response?.data?.message ?? "Login failed. Check your details and try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AuthLayout title="Welcome back" subtitle="Log in to continue to your dashboard.">
      <div className="mb-6 flex rounded-md border border-line p-1">
        {ROLES.map((r) => (
          <button
            key={r.value}
            type="button"
            onClick={() => setRole(r.value)}
            className={`flex-1 rounded-[5px] px-2 py-1.5 text-xs font-medium transition-colors ${
              role === r.value ? "bg-seal text-white" : "text-muted hover:text-ink_text"
            }`}
          >
            {r.label}
          </button>
        ))}
      </div>

      {serverError && (
        <div className="mb-4 rounded-md border border-alert/30 bg-alert/5 px-3.5 py-2.5 text-sm text-alert">
          {serverError}
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} noValidate>
        <FormField label="Email" error={errors.email?.message}>
          <input
            type="email"
            className={inputClass}
            placeholder="you@example.com"
            {...register("email", { required: "Email is required." })}
          />
        </FormField>

        <FormField label="Password" error={errors.password?.message}>
          <PasswordInput
            placeholder="••••••••"
            {...register("password", { required: "Password is required." })}
          />
        </FormField>

        <Button type="submit" variant="primary" size="md" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? "Logging in…" : "Log in"}
        </Button>
      </form>

      {role === "voter" && (
        <p className="mt-6 text-center text-sm text-muted">
          New here?{" "}
          <Link to="/register" className="font-medium text-seal hover:underline">
            Register to vote
          </Link>
        </p>
      )}
    </AuthLayout>
  );
}
